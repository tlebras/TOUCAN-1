"""
A central library for functions/tools that are used across several of the other tools
"""
import numpy as np
import scipy
from osgeo import gdal


def get_angles(jsonresults):
    """
    Extract the viewing angle information from the JSON object returned
    from the database

    :param jsonresults: JSON formatted string result from database query
    :returns: sun zenith angle, sensor zenith angle, relative azimuth angle (in radians)
    """
    angles = {}
    for angle in ('SZA', 'SAA', 'VZA', 'VAA'):
        angles[angle] = np.array([entry[angle] for entry in jsonresults])

    sun_zenith = scipy.deg2rad(angles['SZA'])
    sensor_zenith = scipy.deg2rad(angles['VZA'])

    # Relative azimuth angle, should be in range 0-180
    relative_azimuth = np.abs(scipy.deg2rad(angles['SAA']) - scipy.deg2rad(angles['VAA']))
    fix = relative_azimuth > scipy.pi
    relative_azimuth[fix] = 2*scipy.pi - relative_azimuth[fix]

    return sun_zenith, sensor_zenith, relative_azimuth


def get_reflectance(filelist):
    """
    Read in reflectance data from list of GeoTiff files, and compute the area mean
    for each band for each file.

    :param filelist: List of file names to read
    :returns: Array of reflectances, dimensions nbands x nfiles
    """
    def read_file(thisfile):
        """
        Function to open Geotiff and read data as array
        Returns area mean
        """
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
