import numpy as np
import datetime

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

    search['sensor'] = 'aatsr'
    target = Q.get_images(search)

    drift = RadiometricDrift()
    drift.run(reference, target)


class RadiometricDrift(ToolBase):
    """
    Class for computing radiometric drift
    """
    def run(self, reference, target):
        # User specifies reference sensor and target sensor, date range, and site
        jsonresults = {'reference': reference,
                       'target': target
        }

        # -------------------------------
        # Extract fields we need
        # -------------------------------
        data = {}
        for sensor in ('reference', 'target'):
            data[sensor] = self.extract_fields(jsonresults[sensor])

        # Check data are ok
        self.check_fields(data['reference'], data['target'])

        # Doublets are found using angular matching criteria

        # Timeseries of drift is calculated

        # Plot displayed and/or saved

        # Text file saved
        pass

    @staticmethod
    def extract_fields(jsonresults):
        """
        Extract fields that we need from the JSON object
        and return in a nicer format
        """
        files = np.array([result['archive_location'] for result in jsonresults])
        dates = np.array([datetime.datetime.strptime(result['time'], '%Y-%m-%dT%H:%M:%S.%f') for result in jsonresults])
        angles = libtools.get_angles(jsonresults)
        sun_zenith, sensor_zenith, relative_azimuth = angles
        instrument = jsonresults[0]['instrument']['name']
        region = jsonresults[0]['region']['region']

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

    @staticmethod
    def check_fields(reference, target):
        """
        Check that target and reference regions match
        """
        if reference['region'] != target['region']:
            raise IOError("ERROR: Target and reference sensor regions do not match")

if __name__ == '__main__':
   main()