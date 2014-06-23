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

    target_list = []
    for sensor in ('aatsr', 'meris'):  # Just for testing
        search['sensor'] = sensor
        target_list.append(Q.get_images(search))

    supersensor = SuperSensor()
    supersensor.run(reference, target_list)


class SuperSensor(ToolBase):
    """
    Class for creating a DIMITRI-style 'supersensor', combining various sensors into one
    """
    def __init__(self):
        pass

    def run(self, reference, target_list):

        #-----------------------------------
        # Loop over the sensors that are to be calibrated to the reference sensor
        #-----------------------------------
        band_list = {}
        recalibrated = {}
        for target in target_list:
            # Get the metadata
            self.get_metadata(reference, target)

            #-----------------------------------
            # Loop over the reference sensor's bands
            #-----------------------------------
            band_list[self.instrument['target']] = []
            recalibrated[self.instrument['target']] = {}
            for ref_idx, ref_band in enumerate(self.wavelengths['reference']):

                # Does the recalibration sensor have a band close to this one?
                tgt_idx = np.argmin(np.abs(np.array(self.wavelengths['target'] - ref_band)))
                tgt_band = self.wavelengths['target'][tgt_idx]

                if np.abs(ref_band - tgt_band) > 10:
                    pass
                else:
                    band_idx = {'reference': ref_idx, 'target': tgt_idx}
                    band_list[self.instrument['target']].append(ref_band)  # Store list of bands processed

                    # -------------------------------
                    # Read reflectance from geotiffs
                    # -------------------------------
                    for sensor in ('reference', 'target'):
                        self.data[sensor]['reflectance'] = libtools.get_reflectance_band(self.data[sensor]['files'],
                                                                                         band_idx[sensor])
                    # -------------------------------
                    # Get doublets
                    # -------------------------------
                    doublets, doublet_times = libtools.get_doublets(self.data['reference'], self.data['target'])

                    # -------------------------------
                    # Fit polynomial to the doublets data
                    # -------------------------------
                    poly = self.fit_polynomial(doublets, doublet_times, order=4)

                    # -------------------------------
                    # Use polynomial to recalibrate all the target sensor data (ie not just the doublets)
                    # Store as a list of arrays
                    # -------------------------------
                    recalibrated[self.instrument['target']][ref_band] = self.recalibrate_band(poly)

        # -------------------------------
        # Combine all target sensor data
        # -------------------------------
        bands_found, combined = self.combine_recalibrated(band_list, recalibrated)

    def get_metadata(self, reference, target):
            """
            Read in the metadata

            :param reference: Results from a database query, as JSON format, for the reference sensor
            :param target: A list of JSON format database query results, for the recalibration sensor(s)
            """
            #-----------------------------------
            # Get metadata
            #-----------------------------------
            self.data = {'reference': self.extract_fields(reference),
                         'target': self.extract_fields(target)}

            # Pick out instrument names
            self.instrument = {'reference': self.data['reference']['instrument'][0],
                               'target': self.data['target']['instrument'][0]}

            # Get lists of wavelengths
            Q = Querydb()
            self.wavelengths = {'reference': np.array(Q.get_wavelengths(self.instrument['reference'])),
                                'target': np.array(Q.get_wavelengths(self.instrument['target']))}

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
        bias = libtools.get_sensor_bias(self.data['reference']['reflectance'], self.data['target']['reflectance'],
                                        doublets)

        # Fit polynomial to the data
        # NB polyfit doesn't understand datetime objects so convert to timestamps (seconds)
        timestamps = [float(d.strftime('%s')) for d in doublet_times]
        poly = np.polyfit(timestamps, bias, order)

        return poly

    def recalibrate_band(self, poly):
        """
        Recalibrate TOA reflectance using previously calculated polynomial fit to reference sensor's data.
        In effect we are saying "given this target sensor measurement, what measurement would we have got from the
         reference sensor?"

        :param poly: Polynomial coefficients, returned by :py:meth:`SuperSensor.fit_polynomial`
        :return: List of arrays of recalibrated reflectance at the target dates
        """
        dates = self.data['target']['dates']
        target = self.data['target']['reflectance']

        # Calculate the value of the bias at each target date,
        # using the polynomial coefficients
        recal = np.poly1d(poly)
        timestamps = [float(d.strftime('%s')) for d in dates]
        bias = recal(timestamps)

        # Bias was calculated as bias = (target - reference)/reference
        # Now we effectively want to solve for "reference" when we know
        # "bias" and "target" --> reference = target / (1 + bias)
        recalibrated = [target[i] / (1 + bias[i]) for i in xrange(len(dates))]

        return recalibrated

    @staticmethod
    def combine_recalibrated(band_list, recalibrated):
        """
        Combine the recalibrated data from all the target sensors, padding out any
        bands that weren't included (so that each sensor has the same number of bands)

        :param band_list: List of which bands were found for any target sensor
        :param recalibrated: Dictionary containing lists of arrays for each target sensor
        :returns: List of all the bands that were found across all target sensors
        :returns: New dictionary such that each target sensor has the same number of bands in the
         list (with None objects for bands that weren't present)
        """
        # Empty list to store the final arrays
        combined = {}

        # Get list of wavelengths that were found across the target sensors
        bands_found = sorted({x for bands in band_list.itervalues() for x in bands})

        # Make a new dictionary, looping over each band so that each target sensor has a list
        # containing either the recalibrated data array or "None" if that band wasn't processed
        # for this sensor
        for instrument in band_list.keys():
            combined[instrument] = []
            for band in bands_found:
                if band in band_list[instrument]:
                    combined[instrument].append(recalibrated[instrument][band])
                else:
                    combined[instrument].append(None)

        return bands_found, combined

if __name__ == '__main__':
   main()