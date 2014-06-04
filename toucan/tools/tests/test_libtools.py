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
        self.assertDictEqual(result, {'key1':1, 'key2':'b'})

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

    def test_check_doublet(self):
        """
        Test that check doublet returns correct results
        """
        dummy = {'dates': datetime.datetime(2000, 1, 1),
                     'reflectance': np.ones((3,3,3))*np.nan,
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