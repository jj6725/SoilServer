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

    def __init__(self, device=None):
        self.device = device or os.environ.get("SOIL_FB_DEVICE", "/dev/fb1")
        if not os.path.exists(self.device):
            raise RuntimeError("no framebuffer at %s" % self.device)
        self.width, self.height = self._probe_size()
        # Fail early rather than at the first frame if we can't write.
        with open(self.device, "wb"):
            pass

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
            f.write(self._to_rgb565(img))

    @staticmethod
    def _to_rgb565(img):
        """Pack to little-endian RGB565, which is what fbtft panels expect.

        Per-pixel struct.pack costs about a second per frame on a Pi Zero, so
        use numpy when it is available and keep the slow path as a fallback.
        """
        try:
            import numpy
        except ImportError:
            packed = bytearray()
            for r, g, b in img.getdata():
                packed += struct.pack(
                    "<H", ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                )
            return bytes(packed)

        arr = numpy.asarray(img, dtype=numpy.uint16)
        rgb565 = (
            ((arr[:, :, 0] & 0xF8) << 8)
            | ((arr[:, :, 1] & 0xFC) << 3)
            | (arr[:, :, 2] >> 3)
        )
        return rgb565.astype("<u2").tobytes()


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
    screen = get_screen()
    print("Using %s backend at %dx%d" % (screen.name, screen.width, screen.height))
