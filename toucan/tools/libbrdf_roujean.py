import sys
import scipy
import scipy.linalg
import numpy as np
sys.path.append(".")

from libbase import ToolBase
from libquerydb import Querydb

def main():
    brdf = RoujeanBRDF()
    brdf.run()

class RoujeanBRDF(ToolBase):
    """
    Class for calculating the Roujean BRDF coefficients. Bassed on Roujean (1992). A Bidrectional Reflectance Model
    of the Earth's Surface fo the Correction of Remote Sensing Data
    """

    def __init__(self):
        pass

    def run(self):
        """
        Do some stuff here
        """

        #  Query the database for matching files
        search = {'site': 'Libya4',
                  'sensor': 'meris'
                  }
        Q = Querydb(search)
        results = Q.get()

        # Extract fields we need
        files = np.array([result['archive_location'] for result in results])
        sun_zenith, sensor_zenith, relative_azimuth = self.get_angles(results)

    @staticmethod
    def get_angles(jsonobject):
        """
        Extract the viewing angle information from the JSON object returned
        from the database

        :param jsonobject: JSON formatted string result from database query
        :returns: sun zenith angle, sensor zenith angle, relative azimuth angle
        """
        angles={}
        for angle in ('SZA', 'SAA', 'VZA', 'VAA'):
            angles[angle] = np.array([entry[angle] for entry in jsonobject])

        sun_zenith = scipy.deg2rad(angles['SZA'])
        sensor_zenith = scipy.deg2rad(angles['VZA'])
        relative_azimuth = scipy.deg2rad(angles['SAA']) - scipy.deg2rad(angles['VAA'])

        return sun_zenith, sensor_zenith, relative_azimuth

    @staticmethod
    def calc_kernel_f1(sun_zenith, sensor_zenith, relative_azimuth):
        """
        Calculates the F1 Kernel from Roujean (1992)

        :param sun_zenith: <numpy> array of sun zenith angles in radians.
        :param sensor_zenith: <numpy> array of sensor zenith angles in radians
        :param relative_azimuth: <numpy> array of relative (sun/sensor) azimuth angles in radians.
        :return: <numpy> Roujean F1 kernel
        """

        # Just a bit of syntax candy
        # Do it in here so it goes out of scope after the method call
        cos = scipy.cos
        sin = scipy.sin
        tan = scipy.tan

        delta = scipy.sqrt(tan(sun_zenith)**2 + tan(sensor_zenith)**2 -
                           2*tan(sensor_zenith)*tan(sun_zenith)*cos(relative_azimuth))

        kernel_f1 = 1/(2*scipy.pi) * ((scipy.pi - relative_azimuth)*cos(relative_azimuth)
                                      + sin(relative_azimuth))
        kernel_f1 *= tan(sun_zenith)*tan(sensor_zenith)
        kernel_f1 -= 1/scipy.pi * (tan(sun_zenith) + tan(sensor_zenith) + delta)

        return kernel_f1

    @staticmethod
    def calc_kernel_f2(sun_zenith, sensor_zenith, relative_azimuth):
        """
        Calculates the F2 Kernel from Roujean (1992)

        :param sun_zenith: <numpy> array of sun zenith angles in radians.
        :param sensor_zenith: <numpy> array of sensor zenith angles in radians
        :param relative_azimuth: <numpy> array of relative (sun/sensor) azimuth angles in radians.
        :return: <numpy> Roujean F2 kernel
        """

        # Just a bit of syntax candy
        # Do it in here so it goes out of scope after the method call
        cos = scipy.cos
        sin = scipy.sin
        acos = scipy.arccos

        scatt_angle = acos(cos(sun_zenith)*cos(sensor_zenith) +
                           sin(sun_zenith)*sin(sensor_zenith)*cos(relative_azimuth))

        kernel_f2 = 4/(3*scipy.pi) * (1/(cos(sun_zenith)+cos(sensor_zenith)))
        kernel_f2 *= (scipy.pi/2 - scatt_angle)*cos(scatt_angle) + sin(scatt_angle)
        kernel_f2 -= 1/3.0

        return kernel_f2

    def calc_roujean_coeffs(self, sun_zenith, sensor_zenith, relative_azimuth, reflectance):
        """
        Calculates the Roujean coefficients k0, k1 and k2, given the angles and reflectance

        :param sun_zenith: <numpy> array of sun zenith angles in radians.
        :param sensor_zenith: <numpy> array of sensor zenith angles in radians
        :param relative_azimuth: <numpy> array of relative (sun/sensor) azimuth angles in radians.
        :param reflectance: <numpy> array of reflectance (TOA in the case of dimitripy)
        return: k_coeff: <numpy>
        """

        # Remove any values that have -999 for the reflectance.
        idx = reflectance != -999

        f_matrix = scipy.ones((reflectance[idx].shape[0], 3))  # There are 3 k_coeffs
        f_matrix[:, 1] = self.calc_kernel_f1(sun_zenith[idx], sensor_zenith[idx], relative_azimuth[idx])
        f_matrix[:, 2] = self.calc_kernel_f2(sun_zenith[idx], sensor_zenith[idx], relative_azimuth[idx])

        try:
            k_coeff, _, _, _ = scipy.linalg.lstsq(f_matrix, reflectance[idx].T)
        except:
            k_coeff = scipy.asarray([-999, -999, -999])  # Right thing to do?

        return k_coeff.T

    def calc_brdf(self, sun_zenith, sensor_zenith, relative_azimuth, k_coeff):
        """
        Calculates the BRDF given the viewing geometry and the Roujean k coefficients.

        :param sun_zenith: <numpy> array of sun zenith angles in radians.
        :param sensor_zenith: <numpy> array of sensor zenith angles in radians
        :param relative_azimuth: <numpy> array of relative (sun/sensor) azimuth angles in radians.
        :param k_coeff: <numpy> (n, 3) array of Roujean coefficients k0m k1 and k2 respectively
        return brdf: <numpy> array of reflectance values
        """

        f1 = self.calc_kernel_f1(sun_zenith, sensor_zenith, relative_azimuth)
        f2 = self.calc_kernel_f2(sun_zenith, sensor_zenith, relative_azimuth)
        brdf = k_coeff[0] + k_coeff[1]*f1 + k_coeff[2]*f2

        return brdf

    def brdf_timeseries(self, sun_zenith, sensor_zenith, relative_azimuth, reflectance,
                        dates, start_date, end_date,
                        bin_size=20):
        """
        Plot timeseries of binned BRDF
        """


if __name__ == '__main__':
    main()