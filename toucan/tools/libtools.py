"""
A central library for functions/tools that are used across several of the other tools
"""
import datetime
import os

import numpy as np
import scipy
from osgeo import gdal


def slice_dictionary(dic_in, idx):
    """
    Slice a dictionary - ie given a dictionary where all the keys point to a list (or 1d array),
    return a new dictionary with the same keys but just one slice from each of those lists.
    It is as if we could do ``dictionary[:][index]``

    :param dic_in: Input dictionary to be sliced
    :param idx: Index to slice
    :returns: Sliced dictionary with same keys as input
    """
    dic_out = {key: dic_in[key][idx] for key in dic_in.keys()}
    return dic_out


def mean_date(dates):
    """
    Return the mean value from a list of dates. We convert the dates into unix timestamps,
    which are just numbers and therefore easy to take the mean, then convert the mean value
    back to a datetime object.

    :param dates: List of python datetime dates
    :returns: The mean date
    """
    timestamps = [float(d.strftime('%s')) for d in dates]
    mean_timestamp = np.mean(timestamps)
    mean_date = datetime.datetime.fromtimestamp(mean_timestamp)

    return mean_date


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


def get_mean_reflectance(filelist):
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
        image = gdal.Open(os.path.realpath(thisfile))
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


def get_reflectance_band(filelist, band_idx):
    """
    Read in reflectance data for specified band from a list of GeoTiff files and return a list of 2d reflectance arrays

    :param filelist: List of file names to read
    :param band_idx: Index of the band to read (0-based)
    :returns: List (nfiles long) of 2d reflectance arrays
    """
    def read_file(thisfile):
        """
        Function to open Geotiff and read the specified band as 2d array
        """
        image = gdal.Open(thisfile)
        data = image.GetRasterBand(band_idx + 1).ReadAsArray()  # convert to 1 based index
        image = None
        return data

    # Loop over all the files and read reflectances
    reflectance_list = []
    for thisfile in filelist:
        dat = read_file(thisfile)
        reflectance_list.append(dat)

    return reflectance_list

def get_reflectance_all(filelist):
    """
    Read in reflectance data and return as a 3D reflectance array

    :param filelist: List of file names to read
    :return: List (nfiles long) of 3d reflectance arrays
    """

    reflectance_list = []

    for file in filelist:
        image = gdal.Open(file)
        num_bands = image.RasterCount
        num_x = image.RasterXSize
        num_y = image.RasterYSize

        ref_array = scipy.zeros((num_y, num_x, 1))  # rows, columns, bands
        ref_array[:, :, 0] = image.GetRasterBand(1).ReadAsArray()

        for i_iter in range(1, num_bands): # fillout the rest
            ref_array = scipy.dstack((ref_array, image.GetRasterBand(i_iter).ReadAsArray()))

        reflectance_list.append(ref_array)
        del ref_array

    return reflectance_list


def get_doublets(reference, target, amc_threshold=15, day_threshold=3, roi_threshold=0.75):
    """
    Get doublets that fit the angular matching criteria

    :param reference: Dictionary containing the reference sensor data
    :param target: Dictionary containing the target sensor data
    :param amc_threshold: [Optional] Threshold value to use for AMC (default 15)
    :param day_threshold: [Optional] Threshold value for time offset allowed, in days (default 3)
    :param roi_threshold: [Optional] Minimum ROI coverage allowed as a fraction (default 0.75)
    :returns: List of index pairs (ie index of the image in the reference and target image lists),
     and list of the mean time for each doublet.
    """
    maxdays = datetime.timedelta(days=day_threshold)
    doublets = []
    times = []

    # Loop over each target sensor image
    for target_idx,_ in enumerate(target['dates']):
        # Find which reference images are within the day threshold. These are the ones we'll check
        target_date = target['dates'][target_idx]
        candidates = np.where(np.abs(reference['dates'] - target_date) < maxdays)[0]

        # Loop through these candidates and see if they fulfil all criteria to be a match
        for ref_idx in candidates:
            # Get just this pair of images from the dictionaries
            reference_image = slice_dictionary(reference, ref_idx)
            target_image = slice_dictionary(target, target_idx)
            valid = check_doublet(reference_image, target_image, amc_threshold, day_threshold, roi_threshold)
            # Check if this pair of images meets the criteria to be a doublet
            # and store the indices if so. Also store the mean date for plotting
            if valid:
                doublets.append((target_idx, ref_idx))
                # Get the mean time for the two images
                times.append(mean_date((target_image['dates'], reference_image['dates'])))

    return doublets, times


def check_doublet(reference, target, amc_threshold, day_threshold, roi_threshold):
    """
    Check if this doublet meets all the criteria

    :param reference: Dictionary containing data for a single image (reflectance array, date, viewing angles) for the reference sensor
    :param target: Same as reference, but for the target sensor
    :param amc_threshold: Threshold value for AMC
    :param day_threshold: Threshold value for time offset, in days
    :param roi_threshold: Threshold value for ROI coverage, as fraction
    :returns: True if doublet meets all criteria, False if any failed
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