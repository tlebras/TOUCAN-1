from django.test import TestCase
from mock import *
import numpy as np
import datetime

from tools import libtools

class ToolsTests(TestCase):
    """
    Test the shared tools library
    """

    def test_slice_dictionary(self):
        """
        Test the dictionary slicer
        """
        testdic = {'key1': (0, 1, 2, 3),
                   'key2': ('a', 'b', 'c', 'd'),
        }
        result = libtools.slice_dictionary(testdic, 1)
        self.assertDictEqual(result, {'key1': 1, 'key2': 'b'})

    def test_mean_date(self):
        """
        Test calculation of mean date
        """
        date1 = datetime.datetime(2000, 1, 1)
        date2 = datetime.datetime(2000, 1, 3)
        expected = datetime.datetime(2000, 1, 2)
        result = libtools.mean_date((date1, date2))
        self.assertEquals(result, expected)

    def test_get_angles(self):
        """
        Test that get_angles returns expected results
        """
        testjson = [{'SAA': 0, 'SZA': 0, 'VZA': 0, 'VAA': 0}]
        sun_zenith, sensor_zenith, relative_azimuth = libtools.get_angles(testjson)
        self.assertEquals(sun_zenith, 0)
        self.assertEquals(sensor_zenith, 0)
        self.assertEquals(relative_azimuth, 0)

    def test_get_mean_reflectance(self):
        """
        Test get_mean_reflectance returns correct array shape
        """
        fake_files = ('file1', 'file2')
        nfiles = len(fake_files)
        nbands = 3  # Arbitrary

        # Mock the file opening bit
        with patch('osgeo.gdal.Open') as mock:
            # Set fake return_value to mock reading in data from the file
            mock.return_value.ReadAsArray.return_value = np.zeros((nbands, 2, 2))
            out = libtools.get_mean_reflectance(fake_files)
        self.assertTrue((out == np.zeros((nbands, nfiles))).all())

    def test_get_reflectance_band(self):
        """
        Test get_reflectance_band returns correct array shape
        """
        fake_files = ('file1', 'file2')
        nfiles = len(fake_files)
        nx = 4
        ny = 5

        # Mock the file opening bit
        with patch('osgeo.gdal.Open') as mock:
            # Set fake return_value to mock reading in data from the file
            mock.return_value.GetRasterBand.return_value.ReadAsArray.return_value = np.zeros((nx, ny))
            out = libtools.get_reflectance_band(fake_files, 0)
        # Check result is a list with nfiles entries
        self.assertEquals(len(out), nfiles)
        # Check the arrays in the list have correct dimensions
        self.assertEquals(out[0].shape, (nx, ny))

    def test_get_reflectance_all(self):
        """
        Test get_reflectance_band returns correct array shape
        """
        fake_files = ('file1', 'file2')
        nfiles = len(fake_files)
        nx = 4
        ny = 5
        nz = 15

        # Mock the file opening bit
        with patch('osgeo.gdal.Open') as mock:
            # Set fake return_value to mock reading in data from the file
            mock.return_value.GetRasterBand.return_value.ReadAsArray.return_value = np.zeros((nx, ny, nz))
            out = libtools.get_reflectance_all(fake_files)
        # Check result is a list with nfiles entries
        self.assertEquals(len(out), nfiles)
        # Check the arrays in the list have correct dimensions
        self.assertEquals(out[0].shape, (nx, ny, nz))

    def test_check_doublet(self):
        """
        Test that check doublet returns correct results
        """
        dummy = {'dates': datetime.datetime(2000, 1, 1),
                 'reflectance': np.ones((3, 3, 3)) * np.nan,
                 'SZA': 0,
                 'VZA': 0,
                 'RAA': 0}

        # Test valid doublet
        valid = libtools.check_doublet(dummy, dummy, 0, 0, 0)
        self.assertTrue(valid)

        # Test fail on AMC threshold
        valid = libtools.check_doublet(dummy, dummy, -1, 0, 0)
        self.assertFalse(valid)

        # Test fail on date threshold
        valid = libtools.check_doublet(dummy, dummy, 0, -1, 0)
        self.assertFalse(valid)

        # Test fail on ROI coverage threshold
        valid = libtools.check_doublet(dummy, dummy, 0, 0, 1)
        self.assertFalse(valid)

    def test_calc_amc(self):
        """
        Test AMC calculation
        """
        dum = (0, 0)
        amc = libtools.calc_amc(dum, dum, dum)
        self.assertEquals(amc, 0)

    def test_calc_amc_threshold(self):
        """
        Test AMC threshold calculation
        """
        dum = 0
        amc = libtools.calc_amc_threshold(dum, dum, dum)
        self.assertEquals(amc, 0)