import numpy as np
from django.test import TestCase
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
        testjson = [{'SAA':0, 'SZA':0, 'VZA':0, 'VAA':0}]
        sun_zenith, sensor_zenith, relative_azimuth = libbrdf_roujean.RoujeanBRDF.get_angles(testjson)
        self.assertEquals(sun_zenith, 0)
        self.assertEquals(sensor_zenith, 0)
        self.assertEquals(relative_azimuth, 0)

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
        dum = np.array([0,])  # arguments need to be numpy arrays
        k_coeff = brdf.calc_roujean_coeffs(dum, dum, dum, dum)
        self.assertEquals(sum(k_coeff), 0)

    def test_calc_brdf(self):
        """
        Test BRDF calculation
        """
        brdf = libbrdf_roujean.RoujeanBRDF()
        brdf = brdf.calc_brdf(0, 0, 0, [0,0,0])
        self.assertEquals(brdf, 0)