"""Checks the AQI breakpoint maths against known EPA reference points."""

import unittest

import aqi


class TestPM25(unittest.TestCase):
    def test_band_boundaries(self):
        # Each breakpoint's upper concentration must land on its AQI ceiling.
        self.assertEqual(aqi.pm25_aqi(0.0), 0)
        self.assertEqual(aqi.pm25_aqi(9.0), 50)
        self.assertEqual(aqi.pm25_aqi(35.4), 100)
        self.assertEqual(aqi.pm25_aqi(55.4), 150)
        self.assertEqual(aqi.pm25_aqi(125.4), 200)
        self.assertEqual(aqi.pm25_aqi(225.4), 300)
        self.assertEqual(aqi.pm25_aqi(325.4), 500)

    def test_interpolation(self):
        # 88.4 ug/m3 sits in the 55.5-125.4 band -> 151 + 49/69.9 * 32.9
        self.assertEqual(aqi.pm25_aqi(88.4), 174)
        self.assertEqual(aqi.pm25_aqi(5.0), 28)

    def test_above_scale_clamps(self):
        self.assertEqual(aqi.pm25_aqi(9999), 500)

    def test_missing_and_negative(self):
        self.assertIsNone(aqi.pm25_aqi(None))
        self.assertIsNone(aqi.pm25_aqi(-1))


class TestPM10(unittest.TestCase):
    def test_band_boundaries(self):
        self.assertEqual(aqi.pm10_aqi(54), 50)
        self.assertEqual(aqi.pm10_aqi(154), 100)
        self.assertEqual(aqi.pm10_aqi(604), 500)

    def test_interpolation(self):
        # 140 ug/m3 -> 51 + 49/99 * 85
        self.assertEqual(aqi.pm10_aqi(140), 93)


class TestOverall(unittest.TestCase):
    def test_takes_worst_sub_index(self):
        # PM2.5 88.4 -> 174 beats PM10 140 -> 93
        self.assertEqual(aqi.overall_aqi(88.4, 140), 174)

    def test_tolerates_one_missing(self):
        self.assertEqual(aqi.overall_aqi(88.4, None), 174)
        self.assertEqual(aqi.overall_aqi(None, 140), 93)

    def test_none_when_nothing_reports(self):
        self.assertIsNone(aqi.overall_aqi(None, None))


class TestBands(unittest.TestCase):
    def test_labels_track_value(self):
        self.assertEqual(aqi.band(0)[0], "GOOD")
        self.assertEqual(aqi.band(50)[0], "GOOD")
        self.assertEqual(aqi.band(51)[0], "MODERATE")
        self.assertEqual(aqi.band(174)[0], "UNHEALTHY")
        self.assertEqual(aqi.band(500)[0], "HAZARDOUS")

    def test_no_data_band(self):
        short, _long, _colour = aqi.band(None)
        self.assertEqual(short, "--")

    def test_every_band_has_a_word(self):
        # Colour is never the sole encoding, so each band needs a label.
        for _ceiling, short, long, _colour in aqi.AQI_BANDS:
            self.assertTrue(short.strip())
            self.assertTrue(long.strip())


if __name__ == "__main__":
    unittest.main()
