import sys
import scipy
import scipy.linalg
import numpy as np
import datetime
import matplotlib.pyplot as plt

from osgeo import gdal

sys.path.append(".")
from libbase import ToolBase
from libquerydb import Querydb

def main():

    #  Query the database for matching files
    search = {'site': 'Libya4',
              'sensor': 'meris',
              'end_date':'2006-12-31',
              'order_by': 'time',
              }
    Q = Querydb()
    results = Q.get_images(search)

    brdf = RoujeanBRDF()
    brdf.run(results)

class RoujeanBRDF(ToolBase):
    """
    Class for calculating the Roujean BRDF coefficients. Bassed on Roujean (1992). A Bidrectional Reflectance Model
    of the Earth's Surface fo the Correction of Remote Sensing Data
    """

    def __init__(self):
        pass

    def run(self, jsonresults):
        """
        Compute and plot BRDF
        """

        # Extract fields we need
        files = np.array([result['archive_location'] for result in jsonresults])
        dates = np.array([datetime.datetime.strptime(result['time'], '%Y-%m-%dT%H:%M:%S.%f') for result in jsonresults])
        sun_zenith, sensor_zenith, relative_azimuth = self.get_angles(jsonresults)

        # Read reflectance from the archived files
        reflectance_arr = self.get_reflectance(files)

        # Get list of wavelengths
        instrument = jsonresults[0]['instrument']['name']
        Q = Querydb()
        wavelengths = Q.get_wavelengths(instrument)

        # Generate the plot
        self.brdf_timeseries(sun_zenith, sensor_zenith, relative_azimuth, reflectance_arr,
                        dates, min(dates), max(dates), wavelengths)

    @staticmethod
    def get_angles(jsonresults):
        """
        Extract the viewing angle information from the JSON object returned
        from the database

        :param jsonobject: JSON formatted string result from database query
        :returns: sun zenith angle, sensor zenith angle, relative azimuth angle
        """
        angles={}
        for angle in ('SZA', 'SAA', 'VZA', 'VAA'):
            angles[angle] = np.array([entry[angle] for entry in jsonresults])

        sun_zenith = scipy.deg2rad(angles['SZA'])
        sensor_zenith = scipy.deg2rad(angles['VZA'])

        # Relative azimuth angle, should be in range 0-180
        relative_azimuth = np.abs(scipy.deg2rad(angles['SAA']) - scipy.deg2rad(angles['VAA']))
        fix = relative_azimuth > scipy.pi
        relative_azimuth[fix] = 2*scipy.pi - relative_azimuth[fix]

        return sun_zenith, sensor_zenith, relative_azimuth

    @staticmethod
    def get_reflectance(filelist):
        """
        Read in reflectance data from list of GeoTiff files, and compute the area mean
        for each band for each file.

        :param filelist: List of file names to read
        :returns: Array of reflectances, dimensions nbands x nfiles
        """
        def read_file(thisfile):
            """ Function to open Geotiff and read data as array"""
            image = gdal.Open(thisfile)
            data = image.ReadAsArray()
            arr = np.nanmean(np.nanmean(data, axis=1), axis=1)
            image = None
            return arr

        # Loop over all the files and read reflectances
        first = True
        for thisfile in filelist:
            dat = read_file(thisfile)
            if first:
                reflectance_arr = dat
                first = False
            else:
                reflectance_arr = np.vstack([reflectance_arr, dat])

        # Return the array, transposed so first dimension is the band
        return reflectance_arr.T

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
        idx = ~np.isnan(reflectance) & ~np.isnan(sun_zenith)

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
                        dates, start_date, end_date, wavelengths,
                        bin_size=5):
        """
        Plot timeseries of binned BRDF
        """
        # Keep within the dates that we have available
        start_date = max(start_date, min(dates))
        end_date = min(end_date, max(dates))

        # Initialise everything
        nbands = len(reflectance)
        current = start_date
        step = datetime.timedelta(days=bin_size)
        datebins = []
        first = True

        # Step through the date bins
        while current < end_date:
            idx = (dates >= current) & (dates < current+step)

            # Compute BRDF for each band
            brdf=[]
            for band in range(nbands):
                k_coeff = self.calc_roujean_coeffs(sun_zenith[idx], sensor_zenith[idx], relative_azimuth[idx],
                                                   reflectance[band, idx])
                brdf.append(self.calc_brdf(sun_zenith[idx], sensor_zenith[idx], relative_azimuth[idx], k_coeff))

            # Add to the array
            brdf = np.nanmean(np.array(brdf), axis=1)
            if first:
                brdf_arr = brdf
                first = False
            else:
                brdf_arr = np.vstack([brdf_arr, brdf])

            # Keep track of the bin midpoint, for plotting
            datebins.append(current + step/2)
            current += step

        # Plot timeseries with one line per band
        colormap = plt.cm.spectral
        plt.figure()
        plt.gca().set_color_cycle([colormap(i) for i in np.linspace(0, 0.9, nbands)])
        lines = plt.plot(datebins, brdf_arr, '-o')
        plt.legend(lines, wavelengths, )
        plt.show()

if __name__ == '__main__':
    main()