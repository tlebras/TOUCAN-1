__author__ = 'marrabld'

import sys
import scipy
import scipy.linalg
import numpy as np
import datetime
import matplotlib.pyplot as plt
import csv

from osgeo import gdal

sys.path.append(".")
from libbase import ToolBase
from libquerydb import Querydb

class Cloudscreening(ToolBase):
    def __init__(self):
        pass

    def run(self, jsonresults):
        """
        Compute and plot BRDF. Take results from a database query, extract the reflectance
        values from the returned files, calculate BRDF timeseries, plot the timeseries, and
        output to a csv text file.

        :param jsonresults: The results from a database query, as JSON format
        """

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
        reflectance_arr = self.get_reflectance(files)

        # -------------------------------
        # Get list of wavelengths
        # -------------------------------
        Q = Querydb()
        wavelengths = Q.get_wavelengths(instrument)

class SimpleThreshold(Cloudscreening):
    def __init__(self):
        pass

