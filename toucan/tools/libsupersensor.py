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

                # Get the reflectance for this band (if we have it for this calibration sensor)

                # Get doublets for each reference-calibration sensor pair

                # Fit polynomial to the doublets data

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

if __name__ == '__main__':
   main()