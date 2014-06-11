import numpy as np
import datetime
import matplotlib.pyplot as plt
import csv

from libbase import ToolBase
from libquerydb import Querydb
import libtools


def main():

    #  Query the database for matching files
    Q = Querydb()
    search = {'site': 'Libya4',
              'sensor': 'aatsr',
              'end_date': '2006-12-31',
              'order_by': 'time',
              }
    reference = Q.get_images(search)

    search['sensor'] = 'meris'
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
        # Extract metadata fields
        # -------------------------------
        data = {}
        for sensor in ('reference', 'target'):
            data[sensor] = self.extract_fields(jsonresults[sensor])

        # Check data are ok
        self.check_fields(data['reference'], data['target'])

        # Pick out instrument names
        instrument = {'reference': data['reference']['instrument'][0],
                      'target': data['target']['instrument'][0]}

        # -------------------------------
        # Get lists of wavelengths
        # -------------------------------
        Q = Querydb()
        wavelengths = {'target': np.array(Q.get_wavelengths(instrument['target'])),
                       'reference': np.array(Q.get_wavelengths(instrument['reference']))
                       }

        # -------------------------------
        # Loop over all the target sensor's
        # bands and see if we have a reference
        # sensor band close to it
        #
        # If we do, carry on and process that band,
        # else skip to the next one
        # -------------------------------
        ref_ratio_all = []
        drift_all = []
        bands = []
        for target_idx, target_band in enumerate(wavelengths['target']):
            ref_idx = np.argmin(np.abs(np.array(wavelengths['reference'] - target_band)))
            ref_band = wavelengths['reference'][ref_idx]

            if np.abs(target_band - ref_band) > 10:
                pass
            else:
                band_idx = {'reference': ref_idx, 'target': target_idx}
                bands.append(target_band)
                # -------------------------------
                # Read reflectance from geotiffs
                # -------------------------------
                for sensor in ('reference', 'target'):
                    data[sensor]['reflectance'] = libtools.get_reflectance_band(data[sensor]['files'], band_idx[sensor])

                # -------------------------------
                # Doublets are found using angular matching criteria
                # -------------------------------
                doublets, doublet_times = libtools.get_doublets(data['reference'], data['target'], amc_threshold=45)

                # -------------------------------
                # Timeseries of drift is calculated
                # -------------------------------
                ref_ratio = self.get_drift_timeseries(data, doublets)
                ref_ratio_all.append(ref_ratio)

                # -------------------------------
                # Plot displayed and/or saved
                # -------------------------------
                savename = 'drift_%s_ref_%s_%i.png' % (instrument['target'], instrument['reference'], target_band)
                drift = self.plot_radiometric_drift(doublet_times, ref_ratio, instrument['target'], 
                                                    instrument['reference'], target_band, savename)
                drift_all.append(drift)

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

        :param reference: Dictionary with reference sensor data
        :param target: Dictionary with target sensor data
        :raises IOError: if the regions don't match
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
    def plot_radiometric_drift(times, ref_ratio, target, reference, band, savename=None):
        """
        Plot the ratio of target and reference reflectance, and over lay regression line.

        :param times: List of datetime objects, for x axis
        :param ref_ratio: The reflectance ratio timeseries to plot
        :param target: String name of target sensor
        :param reference: String name of reference sensor
        :param band: The wavelength of this timeseries
        :param savename: [optional] Filename to save to
        :returns: The drift (per year)
        """
        sec2year = 86400. * 365.  # Number of seconds in a year

        # Fit line to ratio. NB polyfit doesn't understand datetime objects so convert to timestamps (seconds)
        timestamps = [float(d.strftime('%s')) for d in times]
        fit = np.polyfit(timestamps, ref_ratio, 1)
        fit_fn = np.poly1d(fit)

        drift = fit[0] * sec2year

        # Plot points and regression line
        plt.figure(figsize=(16, 10))
        plt.rcParams.update({'font.size': 18})
        plt.plot(times, ref_ratio, 'bo', times, fit_fn(timestamps), '--k')
        plt.ylabel('%s / %s reflectance at band %03i nm' %(target.upper(), reference.upper(), band))
        plt.title('Drift: %0.2f per year' % drift)

        if savename:
            plt.savefig(savename)
        else:
            plt.show()

        return drift

    @staticmethod
    def save_as_text(bands, drift, filename):
        """
        Save the drift information to a csv text file

        :param bands: List of the wavelengths
        :param drfit: List of the drift values that were calculated
        :param filename: The file to write to
        """
        header_row = ['Wavelength', 'Drift']

        # Write to CSV file
        csv_file = csv.writer(open(filename,"w"), delimiter=',', quoting=csv.QUOTE_MINIMAL)
        csv_file.writerow(header_row)
        for ind, band in enumerate(bands):
            csv_file.writerow([band, drift[ind]])

if __name__ == '__main__':
   main()