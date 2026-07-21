#!/usr/bin/env python3
"""Air quality dashboard for a 480x320 panel attached to the pi.

Renders with PIL and pushes frames to whatever backend devices/screen.py
finds. Reads sensors through DeviceManager directly, so it does not need the
Flask server to be running -- though both can run at once, since DeviceManager
caches readings.

    python3 dashboard.py                 # render to the panel
    SOIL_DISPLAY=png python3 dashboard.py --once   # one frame to dashboard.png
"""

import argparse
import time
from collections import deque

from PIL import Image, ImageDraw, ImageFont

import aqi
from devices.screen import get_screen

# DeviceManager is imported inside main() rather than here, so that the
# rendering code stays importable on a machine without the sensor libraries.

WIDTH, HEIGHT = 480, 320
MARGIN = 12

# Dark surface -- these panels are usually looked at in a room, not sunlight,
# and a dark field keeps the lit pixels to the data.
BG = "#1a1a19"
TILE = "#232320"
TEXT = "#ffffff"
TEXT_DIM = "#c3c2b7"
TEXT_MUTED = "#84837a"
GRID = "#3a3a36"

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/roboto/Roboto-Medium.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]
FONT_CANDIDATES_REG = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/roboto/Roboto-Regular.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]


def load_font(size, bold=True):
    candidates = FONT_CANDIDATES if bold else FONT_CANDIDATES_REG
    # The fonts.ttf package ships with the Enviro+ examples; prefer it if there.
    try:
        from fonts.ttf import RobotoMedium, RobotoRegular

        candidates = [RobotoMedium if bold else RobotoRegular] + candidates
    except ImportError:
        pass
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


FONTS = {}


def font(size, bold=True):
    key = (size, bold)
    if key not in FONTS:
        FONTS[key] = load_font(size, bold)
    return FONTS[key]


def text_size(draw, text, fnt):
    """Measure text across Pillow versions.

    draw.textbbox arrived in Pillow 8.0 and font.getsize was removed in
    Pillow 10, so neither works everywhere. Old Raspberry Pi OS images ship
    Pillow 5.x from apt, which is the low end this has to cope with.
    """
    if hasattr(draw, "textbbox"):
        left, top, right, bottom = draw.textbbox((0, 0), text, font=fnt)
        return right - left, bottom - top
    return fnt.getsize(text)


def rounded(draw, box, radius, fill):
    """Rounded rectangle, hand-drawn where Pillow lacks rounded_rectangle.

    ImageDraw.rounded_rectangle only exists from Pillow 8.2.
    """
    if hasattr(draw, "rounded_rectangle"):
        draw.rounded_rectangle(box, radius=radius, fill=fill)
        return

    x0, y0, x1, y1 = (int(v) for v in box)
    radius = int(min(radius, (x1 - x0) // 2, (y1 - y0) // 2))
    if radius <= 0:
        draw.rectangle((x0, y0, x1, y1), fill=fill)
        return
    d = radius * 2
    # Cross of rectangles, then a quarter circle in each corner.
    draw.rectangle((x0 + radius, y0, x1 - radius, y1), fill=fill)
    draw.rectangle((x0, y0 + radius, x1, y1 - radius), fill=fill)
    draw.pieslice((x0, y0, x0 + d, y0 + d), 180, 270, fill=fill)
    draw.pieslice((x1 - d, y0, x1, y0 + d), 270, 360, fill=fill)
    draw.pieslice((x0, y1 - d, x0 + d, y1), 90, 180, fill=fill)
    draw.pieslice((x1 - d, y1 - d, x1, y1), 0, 90, fill=fill)


def meter(draw, box, fraction, colour, track=GRID):
    """A single ratio against its limit, on a same-ramp track."""
    x0, y0, x1, y1 = box
    height = y1 - y0
    radius = height // 2
    rounded(draw, box, radius, track)
    fraction = max(0.0, min(1.0, fraction))
    if fraction <= 0:
        return
    # Keep the filled end at least as wide as the cap so it stays a pill.
    filled = max(height, int((x1 - x0) * fraction))
    rounded(draw, (x0, y0, x0 + filled, y1), radius, colour)


def sparkline(draw, box, values, colour):
    x0, y0, x1, y1 = box
    if len(values) < 2:
        return
    lo, hi = min(values), max(values)
    span = hi - lo if hi > lo else 1
    step = (x1 - x0) / (len(values) - 1)
    points = [
        (x0 + i * step, y1 - (v - lo) / span * (y1 - y0))
        for i, v in enumerate(values)
    ]
    try:
        draw.line(points, fill=colour, width=2, joint="curve")
    except TypeError:
        # joint= predates Pillow 5.3; the line just renders with plain corners.
        draw.line(points, fill=colour, width=2)


class Dashboard:
    def __init__(self, screen, manager, history=60):
        self.screen = screen
        self.manager = manager
        self.aqi_history = deque(maxlen=history)

    # -- panels ------------------------------------------------------------

    def draw_header(self, draw, data, devices):
        draw.text((MARGIN, 8), "AIR QUALITY", font=font(13), fill=TEXT_DIM)
        stamp = time.strftime("%H:%M")
        w, _ = text_size(draw, stamp, font(13))
        draw.text((WIDTH - MARGIN - w, 8), stamp, font=font(13), fill=TEXT_DIM)

        label = "%d sensors" % len(devices)
        w2, _ = text_size(draw, label, font(11, bold=False))
        draw.text(
            (WIDTH - MARGIN - w - 14 - w2, 9),
            label,
            font=font(11, bold=False),
            fill=TEXT_MUTED,
        )
        draw.line((MARGIN, 28, WIDTH - MARGIN, 28), fill=GRID, width=1)

    def draw_hero(self, draw, box, value):
        """The one number the dashboard leads with: overall AQI."""
        x0, y0, x1, y1 = box
        short, _long, colour = aqi.band(value)
        rounded(draw, box, 10, TILE)

        draw.text((x0 + 14, y0 + 12), "US AQI", font=font(11), fill=TEXT_MUTED)

        shown = "--" if value is None else str(value)
        draw.text((x0 + 14, y0 + 28), shown, font=font(68), fill=TEXT)

        # The band name always renders. The six AQI colours are not separable
        # by colour alone -- adjacent bands fall below the normal-vision and
        # CVD separation floors -- so the word carries the meaning and the
        # colour only reinforces it.
        draw.text((x0 + 14, y0 + 108), short, font=font(15), fill=colour)

        if len(self.aqi_history) > 1:
            draw.text(
                (x0 + 14, y1 - 40), "LAST HOUR", font=font(9), fill=TEXT_MUTED
            )
            sparkline(
                draw, (x0 + 14, y1 - 26, x1 - 14, y1 - 12), self.aqi_history, colour
            )

    def draw_pm_tile(self, draw, box, label, value, unit, aqi_value):
        x0, y0, x1, y1 = box
        rounded(draw, box, 10, TILE)
        short, _long, colour = aqi.band(aqi_value)

        draw.text((x0 + 12, y0 + 12), label, font=font(11), fill=TEXT_MUTED)

        shown = "--" if value is None else ("%g" % round(value, 1))
        fnt = font(34)
        w, _ = text_size(draw, shown, fnt)
        draw.text((x0 + 12, y0 + 30), shown, font=fnt, fill=TEXT)
        draw.text(
            (x0 + 17 + w, y0 + 48), unit, font=font(10, bold=False), fill=TEXT_MUTED
        )

        if aqi_value is not None:
            draw.text(
                (x0 + 12, y0 + 78),
                "AQI %d" % aqi_value,
                font=font(11),
                fill=TEXT_DIM,
            )
            draw.text((x0 + 12, y0 + 96), short, font=font(11), fill=colour)

        # Scaled against AQI 200 ("Unhealthy"), so a full bar is unambiguous.
        draw.text((x0 + 12, y1 - 34), "0", font=font(9), fill=TEXT_MUTED)
        w200, _ = text_size(draw, "200", font(9))
        draw.text((x1 - 12 - w200, y1 - 34), "200", font=font(9), fill=TEXT_MUTED)
        fraction = 0 if aqi_value is None else aqi_value / 200.0
        meter(draw, (x0 + 12, y1 - 20, x1 - 12, y1 - 12), fraction, colour)

    def draw_stat_tile(self, draw, box, label, value, unit, status, colour):
        x0, y0, _x1, _y1 = box
        rounded(draw, box, 10, TILE)
        draw.text((x0 + 10, y0 + 9), label, font=font(10), fill=TEXT_MUTED)

        fnt = font(26)
        w, _ = text_size(draw, value, fnt)
        draw.text((x0 + 10, y0 + 24), value, font=fnt, fill=TEXT)
        if unit:
            draw.text(
                (x0 + 14 + w, y0 + 39), unit, font=font(10, bold=False), fill=TEXT_MUTED
            )
        if status:
            draw.text((x0 + 10, y0 + 62), status, font=font(10), fill=colour)

    # -- assembly ----------------------------------------------------------

    def secondary_tiles(self, data):
        """Whatever the pi actually has, in a fixed order.

        Adding a sensor to DeviceManager only needs a row here -- tiles that
        have no reading are dropped rather than shown empty.
        """
        candidates = []

        temp = data.get("temp")
        if temp is not None:
            # Both scales: celsius as the headline, fahrenheit on the
            # second line of the tile where a status word would go.
            fahrenheit = temp * 9.0 / 5.0 + 32.0
            candidates.append(
                ("TEMP", "%.1f" % temp, "C", "%.1f F" % fahrenheit, TEXT_DIM)
            )

        humidity = data.get("humidity")
        if humidity is not None:
            status, colour = aqi.describe_humidity(humidity)
            candidates.append(("HUMIDITY", "%.0f" % humidity, "%", status, colour))

        voc = data.get("voc_index")
        if voc is not None:
            status, colour = aqi.describe_voc(voc)
            candidates.append(("VOC INDEX", "%d" % voc, "", status, colour))

        co2 = data.get("co2")
        if co2 is not None:
            status, colour = aqi.describe_co2(co2)
            candidates.append(("CO2", "%d" % co2, "ppm", status, colour))

        pressure = data.get("pressure")
        if pressure is not None:
            candidates.append(("PRESSURE", "%.0f" % pressure, "hPa", "", TEXT_DIM))

        lux = data.get("lux")
        if lux is not None:
            candidates.append(("LIGHT", "%.0f" % lux, "lux", "", TEXT_DIM))

        return candidates

    def render(self, data, devices):
        img = Image.new("RGB", (WIDTH, HEIGHT), BG)
        draw = ImageDraw.Draw(img)

        self.draw_header(draw, data, devices)

        air = data.get("air_quality", {})
        pm25 = air.get("pm25_ugm3")
        pm10 = air.get("pm10_ugm3")
        overall = data.get("aqi")
        if overall is not None:
            self.aqi_history.append(overall)

        top = 38
        hero_h = 168
        hero_w = 196
        self.draw_hero(draw, (MARGIN, top, MARGIN + hero_w, top + hero_h), overall)

        pm_x = MARGIN + hero_w + 10
        pm_w = (WIDTH - MARGIN - pm_x - 10) // 2
        self.draw_pm_tile(
            draw,
            (pm_x, top, pm_x + pm_w, top + hero_h),
            "PM2.5",
            pm25,
            "ug/m3",
            aqi.pm25_aqi(pm25),
        )
        self.draw_pm_tile(
            draw,
            (pm_x + pm_w + 10, top, WIDTH - MARGIN, top + hero_h),
            "PM10",
            pm10,
            "ug/m3",
            aqi.pm10_aqi(pm10),
        )

        tiles = self.secondary_tiles(data)[:4]
        row_y = top + hero_h + 10
        if not tiles:
            note = (
                "No sensors detected -- check wiring and i2cdetect"
                if not devices
                else "Sensors found, waiting for the first reading"
            )
            w, _ = text_size(draw, note, font(12, bold=False))
            draw.text(
                ((WIDTH - w) // 2, row_y + 30),
                note,
                font=font(12, bold=False),
                fill=TEXT_MUTED,
            )
        if tiles:
            gap = 8
            tile_w = (WIDTH - 2 * MARGIN - gap * (len(tiles) - 1)) // len(tiles)
            for i, (label, value, unit, status, colour) in enumerate(tiles):
                x = MARGIN + i * (tile_w + gap)
                self.draw_stat_tile(
                    draw,
                    (x, row_y, x + tile_w, HEIGHT - MARGIN),
                    label,
                    value,
                    unit,
                    status,
                    colour,
                )

        return img

    def run(self, interval=5, once=False):
        while True:
            data = self.manager.get_data()
            self.screen.display(self.render(data, self.manager.devices))
            if once:
                return
            time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="render a single frame")
    parser.add_argument("--interval", type=float, default=5.0)
    args = parser.parse_args()

    from deviceManager import DeviceManager

    screen = get_screen()
    print("display: %s %dx%d" % (screen.name, screen.width, screen.height))
    manager = DeviceManager()
    print("sensors: %s" % (", ".join(manager.devices) or "none"))

    Dashboard(screen, manager).run(interval=args.interval, once=args.once)


if __name__ == "__main__":
    main()
