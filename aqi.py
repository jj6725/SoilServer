"""US EPA Air Quality Index calculation and severity bands.

Breakpoints are the 2024 revised PM2.5 standard (the primary NAAQS was
lowered from 12.0 to 9.0 ug/m3 in Feb 2024) and the 24-hour PM10 standard.
Both take concentrations in ug/m3 -- particle *counts* from the PMS5003
cannot be used here, see DeviceManager.get_data().
"""

# (conc_low, conc_high, aqi_low, aqi_high)
PM25_BREAKPOINTS = [
    (0.0, 9.0, 0, 50),
    (9.1, 35.4, 51, 100),
    (35.5, 55.4, 101, 150),
    (55.5, 125.4, 151, 200),
    (125.5, 225.4, 201, 300),
    (225.5, 325.4, 301, 500),
]

PM10_BREAKPOINTS = [
    (0, 54, 0, 50),
    (55, 154, 51, 100),
    (155, 254, 101, 150),
    (255, 354, 151, 200),
    (355, 424, 201, 300),
    (425, 604, 301, 500),
]

# (aqi_ceiling, short label, long label, colour)
#
# Hues are the EPA's recognisable green/yellow/orange/red/purple scale, stepped
# up for a dark panel -- every one clears 3:1 against the #1a1a19 surface.
# The six bands cannot be told apart by colour alone: adjacent pairs sit below
# the normal-vision separation floor (yellow/orange) and the green/yellow pair
# collapses under protanopia. The band NAME is therefore always drawn next to
# the value; colour is reinforcement only, never the sole encoding.
AQI_BANDS = [
    (50, "GOOD", "Good", "#3ec93e"),
    (100, "MODERATE", "Moderate", "#ffd633"),
    (150, "SENSITIVE", "Unhealthy for sensitive groups", "#ff9a3c"),
    (200, "UNHEALTHY", "Unhealthy", "#f2564f"),
    (300, "VERY BAD", "Very unhealthy", "#b98cd9"),
    (500, "HAZARDOUS", "Hazardous", "#d4526e"),
]


def _piecewise(concentration, breakpoints):
    if concentration is None or concentration < 0:
        return None
    for conc_lo, conc_hi, aqi_lo, aqi_hi in breakpoints:
        if concentration <= conc_hi:
            span = conc_hi - conc_lo
            if span <= 0:
                return aqi_lo
            return round(
                (aqi_hi - aqi_lo) / span * (concentration - conc_lo) + aqi_lo
            )
    # Above the top breakpoint the scale is undefined; clamp to its ceiling.
    return breakpoints[-1][3]


def pm25_aqi(concentration):
    return _piecewise(concentration, PM25_BREAKPOINTS)


def pm10_aqi(concentration):
    return _piecewise(concentration, PM10_BREAKPOINTS)


def overall_aqi(pm25_conc, pm10_conc):
    """Overall AQI is the worst of the contributing pollutant sub-indices."""
    sub = [a for a in (pm25_aqi(pm25_conc), pm10_aqi(pm10_conc)) if a is not None]
    if not sub:
        return None
    return max(sub)


def band(aqi):
    """Return (short_label, long_label, colour) for an AQI value."""
    if aqi is None:
        return ("--", "No data", "#6b6a64")
    for ceiling, short, long, colour in AQI_BANDS:
        if aqi <= ceiling:
            return (short, long, colour)
    return AQI_BANDS[-1][1:]


def describe_voc(voc_index):
    """SGP40 VOC index is 0-500, centred on 100 = typical indoor baseline."""
    if voc_index is None:
        return ("--", "#6b6a64")
    if voc_index <= 0:
        return ("WARMING UP", "#6b6a64")
    if voc_index < 100:
        return ("CLEAN", "#3ec93e")
    if voc_index < 200:
        return ("NORMAL", "#3ec93e")
    if voc_index < 300:
        return ("ELEVATED", "#ffd633")
    if voc_index < 400:
        return ("HIGH", "#ff9a3c")
    return ("VERY HIGH", "#f2564f")


def describe_humidity(humidity):
    if humidity is None:
        return ("--", "#6b6a64")
    if 40 <= humidity <= 60:
        return ("COMFORTABLE", "#3ec93e")
    if 30 <= humidity < 40 or 60 < humidity <= 70:
        return ("FAIR", "#ffd633")
    return ("DRY" if humidity < 30 else "DAMP", "#ff9a3c")


def describe_co2(co2):
    if co2 is None:
        return ("--", "#6b6a64")
    if co2 < 800:
        return ("FRESH", "#3ec93e")
    if co2 < 1200:
        return ("STUFFY", "#ffd633")
    if co2 < 2000:
        return ("POOR", "#ff9a3c")
    return ("VENTILATE", "#f2564f")
