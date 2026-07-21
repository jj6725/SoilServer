"""Output backend for the dashboard.

3.5" Pi panels ship with wildly different drivers, so this tries the common
ones in order of how likely they are to already work on a stock Pi OS image:

  1. /dev/fb1 framebuffer -- what the fbtft/fb_ili9486 kernel drivers expose.
     Needs no Python driver at all and is the usual setup for the cheap 480x320
     "3.5 inch RPi LCD" boards.
  2. luma.lcd -- explicit SPI driver, if you drive the panel from userspace.
  3. A PNG file -- development fallback so the layout can be worked on off-pi.

Set SOIL_DISPLAY=fb|luma|png to force one instead of autodetecting.
"""

import os
import struct


class FramebufferScreen:
    """Writes RGB565 straight to a Linux framebuffer device."""

    name = "framebuffer"

    # Framebuffers belonging to the main HDMI/desktop pipeline. Writing the
    # dashboard to one of these would scribble over the primary display, so
    # they are only used when nothing else is available.
    PRIMARY_DRIVERS = ("vc4", "drm", "simple", "wayland")

    def __init__(self, device=None):
        self.device = device or os.environ.get("SOIL_FB_DEVICE") or self._autodetect()
        if not os.path.exists(self.device):
            raise RuntimeError("no framebuffer at %s" % self.device)
        self.width, self.height = self._probe_size()
        self.bpp = self._probe_int("bits_per_pixel", 16)
        # DRM's fbdev emulation pads rows, so trust the reported stride.
        self.stride = self._probe_int("stride", self.width * self.bpp // 8)
        if self.bpp not in (16, 32):
            raise RuntimeError(
                "%s reports %d bits per pixel; only 16 and 32 are handled"
                % (self.device, self.bpp)
            )
        # Fail early rather than at the first frame if we can't write.
        with open(self.device, "wb"):
            pass

    def _probe_int(self, attr, default):
        fb = os.path.basename(self.device)
        try:
            with open("/sys/class/graphics/%s/%s" % (fb, attr)) as f:
                return int(f.read().strip())
        except (OSError, ValueError):
            return default

    @classmethod
    def _fb_name(cls, fb):
        try:
            with open("/sys/class/graphics/%s/name" % fb) as f:
                return f.read().strip()
        except OSError:
            return ""

    @classmethod
    def _autodetect(cls):
        """Pick the SPI panel, not the HDMI output.

        Panel numbering is not stable -- fbtft usually lands on fb1 when HDMI
        holds fb0, but on a headless pi the panel can be fb0 instead. Choose
        by driver name and only fall back to a primary framebuffer if that is
        genuinely all there is.
        """
        try:
            devices = sorted(
                d for d in os.listdir("/sys/class/graphics") if d.startswith("fb")
            )
        except OSError:
            devices = []

        fallback = None
        for fb in devices:
            path = "/dev/%s" % fb
            if not os.path.exists(path):
                continue
            name = cls._fb_name(fb).lower()
            if name and not any(p in name for p in cls.PRIMARY_DRIVERS):
                return path
            if fallback is None:
                fallback = path

        if fallback is None:
            raise RuntimeError("no framebuffer devices found under /dev")
        return fallback

    def _probe_size(self):
        """Read the panel geometry from sysfs, falling back to 480x320."""
        fb = os.path.basename(self.device)
        try:
            with open("/sys/class/graphics/%s/virtual_size" % fb) as f:
                w, h = f.read().strip().split(",")
                return int(w), int(h)
        except (OSError, ValueError):
            return 480, 320

    def display(self, img):
        if img.size != (self.width, self.height):
            img = img.resize((self.width, self.height))
        if img.mode != "RGB":
            img = img.convert("RGB")
        with open(self.device, "wb") as f:
            f.write(self._pack(img))

    def _pack(self, img):
        """Pack an RGB image into the framebuffer's own pixel format.

        16bpp is RGB565, what the fbtft drivers expose. 32bpp is XRGB8888,
        which is what DRM's fbdev emulation usually gives -- stored
        little-endian, so the bytes go out in B, G, R, X order.

        Rows are padded out to the reported stride; DRM in particular does not
        always make stride equal width * bytes-per-pixel, and a mismatch
        shears the image diagonally.
        """
        try:
            import numpy
        except ImportError:
            return self._pack_slow(img)

        arr = numpy.asarray(img, dtype=numpy.uint8)
        height, width = arr.shape[0], arr.shape[1]

        if self.bpp == 16:
            wide = arr.astype(numpy.uint16)
            packed = (
                ((wide[:, :, 0] & 0xF8) << 8)
                | ((wide[:, :, 1] & 0xFC) << 3)
                | (wide[:, :, 2] >> 3)
            )
            rows = packed.astype("<u2").view(numpy.uint8).reshape(height, width * 2)
        else:
            out = numpy.empty((height, width, 4), dtype=numpy.uint8)
            out[:, :, 0] = arr[:, :, 2]  # blue
            out[:, :, 1] = arr[:, :, 1]  # green
            out[:, :, 2] = arr[:, :, 0]  # red
            out[:, :, 3] = 0xFF  # unused/alpha
            rows = out.reshape(height, width * 4)

        if self.stride > rows.shape[1]:
            padding = numpy.zeros(
                (height, self.stride - rows.shape[1]), dtype=numpy.uint8
            )
            rows = numpy.hstack((rows, padding))
        return rows.tobytes()

    def _pack_slow(self, img):
        """numpy-free fallback. Costs about a second a frame on a Pi Zero."""
        width, height = img.size
        pixels = list(img.getdata())
        out = bytearray()
        for y in range(height):
            row = bytearray()
            for x in range(width):
                r, g, b = pixels[y * width + x]
                if self.bpp == 16:
                    row += struct.pack(
                        "<H", ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                    )
                else:
                    row += bytes((b, g, r, 0xFF))
            row += bytes(max(0, self.stride - len(row)))
            out += row
        return bytes(out)


class LumaScreen:
    """Drives the panel over SPI via luma.lcd."""

    name = "luma"

    def __init__(self):
        from luma.core.interface.serial import spi
        from luma.lcd.device import ili9486

        serial = spi(port=0, device=0, gpio_DC=24, gpio_RST=25, bus_speed_hz=32000000)
        self.device = ili9486(serial, width=480, height=320, rotate=0)
        self.width = self.device.width
        self.height = self.device.height

    def display(self, img):
        if img.mode != "RGB":
            img = img.convert("RGB")
        self.device.display(img)


class PngScreen:
    """Development fallback -- writes each frame to a PNG."""

    name = "png"

    def __init__(self, path=None):
        self.path = path or os.environ.get("SOIL_PNG_PATH", "dashboard.png")
        self.width = 480
        self.height = 320

    def display(self, img):
        img.save(self.path)


_BACKENDS = {
    "fb": FramebufferScreen,
    "luma": LumaScreen,
    "png": PngScreen,
}


def get_screen():
    forced = os.environ.get("SOIL_DISPLAY")
    if forced:
        try:
            backend = _BACKENDS[forced]
        except KeyError:
            raise RuntimeError(
                "SOIL_DISPLAY=%s is not one of: %s"
                % (forced, ", ".join(sorted(_BACKENDS)))
            )
        return backend()

    for backend in (FramebufferScreen, LumaScreen):
        try:
            screen = backend()
        except Exception:
            continue
        else:
            return screen
    return PngScreen()


if __name__ == "__main__":
    print("framebuffers:")
    try:
        found = sorted(
            d for d in os.listdir("/sys/class/graphics") if d.startswith("fb")
        )
    except OSError:
        found = []
    if not found:
        print("  none -- no SPI panel driver loaded?")
    for fb in found:
        print(
            "  /dev/%-6s name=%-20s exists=%s"
            % (fb, FramebufferScreen._fb_name(fb) or "?", os.path.exists("/dev/" + fb))
        )

    screen = get_screen()
    print(
        "\nUsing %s backend at %dx%d%s"
        % (
            screen.name,
            screen.width,
            screen.height,
            " (%s)" % screen.device if hasattr(screen, "device") else "",
        )
    )
    if hasattr(screen, "bpp"):
        print("  %d bpp, stride %d bytes" % (screen.bpp, screen.stride))
    if screen.name == "png":
        print("No panel found -- frames go to a PNG file instead.")
