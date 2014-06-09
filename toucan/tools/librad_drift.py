import numpy as np
import datetime
import matplotlib.pyplot as plt

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

        #  TODO think how we will organise the bands
        band_idx = {'reference': 12,
                    'target': 2}

        # -------------------------------
        # Extract fields we need
        # -------------------------------
        data = {}
        for sensor in ('reference', 'target'):
            data[sensor] = self.extract_fields(jsonresults[sensor])
            data[sensor]['reflectance'] = libtools.get_reflectance_band(data[sensor]['files'], band_idx[sensor])
        # Instrument names
        ref_instrument = data['reference']['instrument'][0]
        target_instrument = data['target']['instrument'][0]

        # Check data are ok
        self.check_fields(data['reference'], data['target'])

        # -------------------------------
        # Doublets are found using angular matching criteria
        # -------------------------------
        doublets, doublet_times = libtools.get_doublets(data['reference'], data['target'], amc_threshold=45, day_threshold=3)

        # -------------------------------
        # Timeseries of drift is calculated
        # -------------------------------
        ref_ratio = self.get_drift_timeseries(data, doublets)

        # -------------------------------
        # Plot displayed and/or saved
        # -------------------------------
        self.plot_radiometric_drift(doublet_times, ref_ratio, target_instrument, ref_instrument)

        # Text file saved

    @staticmethod
    def extract_fields(jsonresults):
        """
        Extract fields that we need from the JSON object
        and return in a nicer format
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

    @staticmethod
    def check_fields(reference, target):
        """
        Check that target and reference regions match
        """
        if set(reference['region']) != set(target['region']):
            raise IOError("ERROR: Target and reference sensor regions do not match")

    @staticmethod
    def get_drift_timeseries(data, doublets):
        """
        Compute the ratio of targe:reference reflectance, given a list of doublets. The area mean
        reflectance values are used.

        :param data: Dictionary containing the image data
        :param doublets: A list of tuples, each holding the index of the target and reference sensor for that doublet pair
        :returns: Timeseries of reflectance ratio 
        """
        # Get reflectance ratio
        refratio = []
        for d in doublets:
            t_idx = d[0]
            r_idx = d[1]
            refratio.append(np.nanmean(data['target']['reflectance'][t_idx]) /
                            np.nanmean(data['reference']['reflectance'][r_idx]))

        return refratio

    @staticmethod
    def plot_radiometric_drift(times, ref_ratio, target, reference):
        """
        Plot the ratio of target and reference reflectance, and over lay regression line.

        :param times: List of datetime objects, for x axis
        :param ref_ratio: The reflectance ratio timeseries to plot
        :param target: String name of target sensor
        :param reference: String name of reference sensor
        """
        sec2year = 86400. * 365.  # Number of seconds in a year

        # Fit line to ratio. NB polyfit doesn't understand datetime objects
        timestamps = [float(d.strftime('%s')) for d in times]
        fit = np.polyfit(timestamps, ref_ratio,1)
        fit_fn = np.poly1d(fit)

        drift = fit[0] * sec2year
        # Plot points and regression line
        plt.plot(times, ref_ratio, 'yo', times, fit_fn(timestamps), '--k')

        plt.xlabel('Date')
        plt.ylabel('%s reflectance / %s reflectance' %(target.upper(), reference.upper()))
        plt.title('Drift: %0.2f per year'%drift)
        plt.show()

if __name__ == '__main__':
   main()