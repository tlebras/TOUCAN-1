from django.test import TestCase
from mock import *
import numpy as np

from tools import libtools


class ToolsTests(TestCase):
    """
    Test the shared tools library
    """
    def test_get_angles(self):
        """
        Test that get_angles returns expected results
        """
        testjson = [{'SAA':0, 'SZA':0, 'VZA':0, 'VAA':0}]
        sun_zenith, sensor_zenith, relative_azimuth = libtools.get_angles(testjson)
        self.assertEquals(sun_zenith, 0)
        self.assertEquals(sensor_zenith, 0)
        self.assertEquals(relative_azimuth, 0)

    def test_get_reflectance(self):
        """
        Test get_reflectance returns correct array shape
        """
        fake_files = ('file1', 'file2')
        nfiles = len(fake_files)
        nbands = 3  # Arbitrary

        # Mock the file opening bit
        with patch('osgeo.gdal.Open') as mock:
            # Set fake return_value to mock reading in data from the file
            mock.return_value.ReadAsArray.return_value = np.zeros((nbands, 2, 2))
            out = libtools.get_reflectance(fake_files)
            self.assertTrue((out == np.zeros((nbands, nfiles))).all())