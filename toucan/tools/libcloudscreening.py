__author__ = 'marrabld'

import sys
import datetime

import numpy as np


sys.path.append(".")
from libbase import ToolBase
from libquerydb import Querydb
import libtools


def main():

    #  Query the database for matching files
    search = {'site': 'Libya4',
              'sensor': 'meris',
              'end_date': '2006-12-31',
              'order_by': 'time',
              }
    Q = Querydb()
    results = Q.get_images(search)

    cloudscreening = CloudscreeningSimpleThreshold()
    mask = cloudscreening.run(results)

class Cloudscreening(ToolBase):
    def __init__(self):
        pass

    def run(self, jsonresults):
        pass


class CloudscreeningSimpleThreshold(Cloudscreening):
    def __init__(self):
        pass

    def calc_band_ratio(self, image, band_numerator, band_denominator):
        """
        Calculate a simple band ratio.  of an image

        :param image: <3d numpy> Array where 3 dim is the bands
        :param band_numerator: <int> The band number (index from 0)
        :param band_denominator: <int> The band number
        :return: <2d numpy> Array which is the ratio of the bands
        """
        # todo Check the that the bands are withing the image dimensional range

        int(band_numerator)
        int(band_denominator)

        return image[:, :, band_numerator] / image[:, :, band_denominator]

    def apply_band_threshold(self, image, threshold):
        """
        Apply a band threshold to the image values.

        :param image: <2d numpy>  Array
        :param threshold: <float> The threshold to apply.  Values below will be set to 0 and above to 1
        :return: <2d numpy> <int> Binary array
        """

        return (image > threshold).astype(int)

    def run(self, jsonresults):
        """
        Compute binary cloudmask. Take results from a database query, extract the reflectance
        values from the returned files, calculate cloudmask

        :param jsonresults: The results from a database query, as JSON format
        :return <numpy 2d> <int> Binary cloudmask
        """

        #TODO figure out how to pass parameters such as the threshold. in the jsonresults??

        # -------------------------------
        # Extract fields we need
        # -------------------------------
        files = np.array([result['archive_location'] for result in jsonresults])
        dates = np.array([datetime.datetime.strptime(result['time'], '%Y-%m-%dT%H:%M:%S.%f') for result in jsonresults])
        sun_zenith, sensor_zenith, relative_azimuth = self.get_angles(jsonresults)
        instrument = jsonresults[0]['instrument']['name']
        region = jsonresults[0]['region']['region']

        # -------------------------------
        # Read reflectance from the archived files
        # -------------------------------
        reflectance_arr = libtools.get_reflectance_all(files)

        # -------------------------------
        # Get list of wavelengths
        # -------------------------------
        Q = Querydb()
        wavelengths = Q.get_wavelengths(instrument)

        image = self.calc_band_ratio(reflectance_arr, 0, wavelengths.shape[0] - 1)
        mask = self.apply_band_threshold(image, 0.7)

        return mask

