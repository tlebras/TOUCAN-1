import numpy as np
import datetime
import unittest

from django.test import TestCase
from mock import *
from tools import libbase, libbrdf_roujean


class BaseTests(TestCase):
    def test_base_class(self):
        """
        Test abstract base class
        """

        class MyClass(libbase.ToolBase):
            def run(self):
                pass

        self.assertTrue(issubclass(MyClass, libbase.ToolBase))
        self.assertTrue(isinstance(MyClass(), libbase.ToolBase))

    def test_incomplete_base_class(self):
        """
        Check that base class fails to instantiate if it doesn't
        overload the run method
        """

        class MyClass(libbase.ToolBase):
            def norun(self):
                pass

        self.assertTrue(issubclass(MyClass, libbase.ToolBase))
        with self.assertRaises(TypeError):
            MyClass()


class BrdfRoujeanTests(TestCase):
    """
    Test the Roujean BRDF library
    """

    def test_get_angles(self):
        """
        Test that get_angles returns expected results
        """
        testjson = [{'SAA': 0, 'SZA': 0, 'VZA': 0, 'VAA': 0}]
        sun_zenith, sensor_zenith, relative_azimuth = libbrdf_roujean.RoujeanBRDF.get_angles(testjson)
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
            out = libbrdf_roujean.RoujeanBRDF.get_reflectance(fake_files)
            self.assertTrue((out == np.zeros((nbands, nfiles))).all())

    def test_calc_f1_kernel(self):
        """
        Test calculation of f1 kernel
        """
        f1 = libbrdf_roujean.RoujeanBRDF.calc_kernel_f1(0, 0, 0)
        self.assertEquals(f1, 0)

    def test_calc_f2_kernel(self):
        """
        Test calculation of f2 kernel
        """
        f2 = libbrdf_roujean.RoujeanBRDF.calc_kernel_f2(0, 0, 0)
        self.assertEquals(f2, 0)

    def test_calc_roujean_coeffs(self):
        """
        Test calculation of Roujean coefficients
        """
        brdf = libbrdf_roujean.RoujeanBRDF()

        # Test returns expected result from valid input
        dum = np.array([0, ])  # arguments need to be numpy arrays
        k_coeff = brdf.calc_roujean_coeffs(dum, dum, dum, dum)
        self.assertEquals(sum(k_coeff), 0)

        # Test returns -999 if scipy.linalg.lstsq fails
        dum = np.array([np.nan, ])  # arguments need to be numpy arrays
        k_coeff = brdf.calc_roujean_coeffs(dum, dum, dum, dum)
        self.assertEquals(sum(k_coeff), -999 * 3)

    def test_calc_brdf(self):
        """
        Test BRDF calculation
        """
        brdf = libbrdf_roujean.RoujeanBRDF()
        brdf = brdf.calc_brdf(0, 0, 0, [0, 0, 0])
        self.assertEquals(brdf, 0)

    def test_brdf_timeseries(self):
        """
        Test BRDF timeseries generation
        """
        # nb arguments need to be numpy arrays
        # Use a date range wider than bin_size, to ensure we cover all parts of the code
        brdf = libbrdf_roujean.RoujeanBRDF()
        testdates = np.array([datetime.datetime(2006, 1, 1), datetime.datetime(2006, 1, 31)])
        dum = np.array([0, 0])
        sza = vza = raa = dum
        ref = np.tile(dum, (15, 1))
        bin_size = 5

        results = brdf.brdf_timeseries(sza, vza, raa, ref, testdates, testdates[0], testdates[1], bin_size)
        # Check correct dates are returned
        self.assertEquals(sum(results[0] != testdates), 0)
        # Check correct data values are returned
        self.assertEquals(np.sum(results[1:]), 0)


    @unittest.skip('No X server running')  # to do, make a skipif 
    def test_plot_timeseries(self):
        """
        Test the timeseries plot
        """
        with patch('matplotlib.pyplot.show') as mock:  # don't display the figure
            with patch('matplotlib.pyplot.savefig') as mock2:  # don't display the figure
                brdf = libbrdf_roujean.RoujeanBRDF()
                dum = np.array([0, 0, 0])
                # Test with and without the optional arguments for full coverage
                brdf.plot_timeseries(dum, dum, dum, title='title', xlabel='xlabel', ylabel='ylabel',
                                     savename='savename')
                brdf.plot_timeseries(dum, dum, dum)

    def test_filter_timeseries(self):
        """
        Check that filter_timeseries removes correct values

        NB we need to be able to compare arrays that contain nan. Normally nan!=nan by definition,
        but we can use numpy.testing.assert_array_equal to compare such that nan==nan.
        It returns None if the arrays are equal, and raises AssertionError if they are different
        """
        timeseries = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 99, -99], dtype='float')
        result = libbrdf_roujean.RoujeanBRDF.filter_timeseries(timeseries)
        expected = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, np.nan, np.nan], dtype='float')

        self.assertEqual(np.testing.assert_array_equal(result, expected), None)

    def test_save_csv(self):
        """
        Test the CSV file writer
        """
        # Avoid actually opening/writing to a file
        with patch('__builtin__.open') as mock:
            nbands = 3
            dum = np.zeros((2, nbands))
            brdf = libbrdf_roujean.RoujeanBRDF()
            dates = np.array([datetime.datetime(2006, 1, 1), datetime.datetime(2006, 1, 31)])
            brdf.save_as_text(dates, ['var1', 'var2'], range(nbands), [dum, dum], 'filename.csv')
