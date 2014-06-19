import sys
import numpy as np
import datetime


sys.path.append(".")
from libbase import ToolBase
from libquerydb import Querydb
import libtools


def main():

    #  Query the database for matching files
    Q = Querydb()
    search = {'site': 'Libya4',
              'sensor': 'meris',
              'end_date': '2006-12-31',
              'order_by': 'time',
              }
    reference = Q.get_images(search)

    calibration_list = []
    for sensor in ('aatsr',):
        search['sensor'] = sensor
        calibration_list.append(Q.get_images(search))

    super = SuperSensor()
    super.run(reference, calibration_list)


class SuperSensor(ToolBase):
    """
    Class for creating a DIMITRI-style 'supersensor', combining various sensors into one
    """
    def __init__(self):
        pass

    def run(self, reference, calibration_list):

        #-----------------------------------
        # Loop over the sensors that are to be calibrated to the reference sensor
        #-----------------------------------
        for calibration in calibration_list:
            # Get the metadata
            self.get_metadata(reference, calibration)

            #-----------------------------------
            # Loop over the reference sensor's bands
            #-----------------------------------
            for ref_idx, ref_band in enumerate(self.wavelengths['reference']):

                # Does the recalibration sensor have a band close to this one?
                cal_idx = np.argmin(np.abs(np.array(self.wavelengths['calibration'] - ref_band)))
                cal_band = self.wavelengths['calibration'][cal_idx]

                if np.abs(ref_band - cal_band) > 10:
                    pass
                else:
                    band_idx = {'reference': ref_idx, 'calibration': cal_idx}

                    # -------------------------------
                    # Read reflectance from geotiffs
                    # -------------------------------
                    for sensor in ('reference', 'calibration'):
                        self.data[sensor]['reflectance'] = libtools.get_reflectance_band(self.data[sensor]['files'],
                                                                                         band_idx[sensor])
                    # -------------------------------
                    # Get doublets
                    # -------------------------------
                    doublets, doublet_times = libtools.get_doublets(self.data['reference'], self.data['calibration'])

                    # -------------------------------
                    # Fit polynomial to the doublets data
                    # -------------------------------
                    poly = self.fit_polynomial(doublets, doublet_times)

            # Use polynomial to recalibrate all the calibration sensor data (ie not just the doublets)

    def get_metadata(self, reference, calibration):
            """
            Read in the metadata

            :param reference: Results from a database query, as JSON format, for the reference sensor
            :param calibration: A list of JSON format database query results, for the recalibration sensor(s) 
            """
            #-----------------------------------
            # Get metadata
            #-----------------------------------
            self.data = {'reference': self.extract_fields(reference),
                         'calibration': self.extract_fields(calibration)}

            # Pick out instrument names
            instrument = {'reference': self.data['reference']['instrument'][0],
                          'calibration': self.data['calibration']['instrument'][0]}

            # Get lists of wavelengths
            Q = Querydb()
            self.wavelengths = {'calibration': np.array(Q.get_wavelengths(instrument['calibration'])),
                                'reference': np.array(Q.get_wavelengths(instrument['reference']))}

    @staticmethod
    def extract_fields(jsonresults):
        """
        Extract fields that we need from the JSON object
        and return as a dictionary

        :param jsonresults: The results from a database query, as JSON format
        :returns: Dictionary containing all the data
        """
        files = np.array([result['archive_location'] for result in jsonresults])
        dates = np.array([datetime.datetime.strptime(result['time'], '%Y-%m-%dT%H:%M:%S.%f') for result in jsonresults])
        angles = libtools.get_angles(jsonresults)
        sun_zenith, sensor_zenith, relative_azimuth = np.rad2deg(angles)
        # Make the instrument and region fields lists, so that they work when we take timeslice later
        instrument = np.tile(jsonresults[0]['instrument']['name'], (len(files)))
        region = np.tile(jsonresults[0]['region']['region'], (len(files)))

        # Create dictionary holding all fields
        data = {'files': files,
                'dates': dates,
                'SZA': sun_zenith,
                'VZA': sensor_zenith,
                'RAA': relative_azimuth,
                'instrument': instrument,
                'region': region,
                }
        return data

    def fit_polynomial(self, doublets, doublet_times, order=2):
        """
        Fit a polynomial to the reference-calibration sensor data

        :param doublets: List of tuples giving the indices of the doublet pairs
        :param order: [Optional] Order of polynomial to use. Default is 2 (ie quadratic).
        :returns: Polynomial coefficients
        """

        # Get timeseries of the sensor bias
        bias = libtools.get_sensor_bias(self.data['reference']['reflectance'], self.data['calibration']['reflectance'],
                                        doublets)

        # Fit polynomial to the data
        # NB polyfit doesn't understand datetime objects so convert to timestamps (seconds)
        timestamps = [float(d.strftime('%s')) for d in doublet_times]
        poly = np.polyfit(timestamps, bias, order)

        return poly

if __name__ == '__main__':
   main()