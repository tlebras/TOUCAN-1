"""
A central library for functions/tools that are used across several of the other tools
"""
import numpy as np
import scipy
from osgeo import gdal


def slice_dictionary(dic_in, idx):
    """
    Slice a dictionary - ie given a dictionary where all the keys point to a list (or 1d array),
    return a new dictionary with the same keys but just one slice from each of those lists

    :param dic_in: Input dictionary to be sliced
    :param idx: Index to slice
    :returns: Sliced dictionary with same keys as input
    """
    dic_out = {key: dic_in[key][idx] for key in dic_in.keys()}
    return dic_out


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


def check_doublet(reference, target, amc_threshold, day_threshold, roi_threshold):
    """
    Check if this doublet meets all the criteria

    :param reference: Dictionary containing data for a single image (reflectance array, date, viewing angles) for the reference sensor
    :param target: Same as reference, but for the target sensor
    :param amc_threshold: Threshold value for AMC
    :param day_threshold: Threshold value for time offset, in days
    :param roi_threshold: Threshold value for ROI coverage, as fraction
    :returns: valid, True if doublet meets all criteria, False if any failed
    """
    valid_doublet = True

    # Check AMC
    amc = calc_amc((reference['SZA'], target['SZA']), (reference['VZA'], target['VZA']),
                   (reference['RAA'], target['RAA']))
    if amc > amc_threshold:
        valid_doublet = False

    # Check dates
    date_diff = np.abs(reference['dates'] - target['dates']).days
    if date_diff > day_threshold:
        valid_doublet = False

    # Check ROI coverage
    coverage = lambda arr: float(np.sum(~np.isnan(arr))) / arr.size
    ref_cover = coverage(reference['reflectance'])
    tar_cover = coverage(target['reflectance'])
    if (ref_cover < roi_threshold) or (tar_cover < roi_threshold):
        valid_doublet = False

    return valid_doublet


def calc_amc(sza, vza, raa):
    """
    Calculate angular matching criteria (AMC)

    :param sza: Tuple containing sun zenith angle for sensor A and sensor B
    :param vza: Tuple containing viewing zenith angle for sensor A and sensor B
    :param raa: Tuple containing relative azimuth angle for sensor A and sensor B
    :returns: The AMC value
    """
    s1 = (sza[1] - sza[0])**2
    s2 = (vza[1] - vza[0])**2
    s3 = 0.25 * (np.abs(raa[1]) - np.abs(raa[0]))**2

    amc = np.sqrt(s1 + s2 + s3)
    return amc


def calc_amc_threshold(dsza, dvza, draa):
    """
    Calculate the threshold AMC value, based on input angle offsets

    :param dsza: The threshold difference in sun zenith angle between two sensors
    :param dvza: The threshold difference in sensor zenith angle between two sensors
    :param draa: The threshold difference in relative azimuth angle between two sensors
    :returns: The corresponding threshold AMC value
    """
    amc = np.sqrt(dsza**2 + dvza**2 + 0.25*draa**2)
    return amc