import sys
import scipy
import scipy.linalg
import numpy as np
import datetime
import matplotlib.pyplot as plt
import csv

sys.path.append(".")
from libbase import ToolBase
from libquerydb import Querydb
import libtools

def main():

    #  Query the database for matching files
    search = {'site': 'Libya4',
              'sensor': 'meris',
              'end_date':'2006-12-31',
              'order_by': 'time',
              }
    Q = Querydb()
    results = Q.get_images(search)

    brdf = RoujeanBRDF()
    brdf.run(results)


class RoujeanBRDF(ToolBase):
    """
    Class for calculating the Roujean BRDF coefficients. Based on Roujean (1992): A Bidirectional Reflectance Model
    of the Earth's Surface fo the Correction of Remote Sensing Data
    """

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
        sun_zenith, sensor_zenith, relative_azimuth = libtools.get_angles(jsonresults)
        instrument = jsonresults[0]['instrument']['name']
        region = jsonresults[0]['region']['region']

        # -------------------------------
        # Read reflectance from the archived files
        # -------------------------------
        reflectance_arr = libtools.get_mean_reflectance(files)

        # -------------------------------
        # Get list of wavelengths
        # -------------------------------
        Q = Querydb()
        wavelengths = Q.get_wavelengths(instrument)

        # -------------------------------
        # Calculate BRDF timeseries
        # -------------------------------
        temp = self.brdf_timeseries(sun_zenith, sensor_zenith, relative_azimuth, reflectance_arr,
                                    dates, min(dates), max(dates))
        datebins, brdf_arr, ref_arr, err_r_arr, err_s_arr = temp    # To keep line lengths down

        # Min and max date strings, for use in filenames
        d_min, d_max = datebins[0].strftime('%Y-%m-%d'), datebins[-1].strftime('%Y-%m-%d')

        # -------------------------------
        # Filter the data (take out anything
        # > 2std away from mean)
        # -------------------------------
        # Get the difference between measured reflectance and
        # modelled BRDF, as a percentage of BRDF
        brdf_ratio = (ref_arr - brdf_arr) / brdf_arr * 100
        plot_brdf = self.filter_timeseries(brdf_ratio)

        # -------------------------------
        # Generate the plot
        # -------------------------------
        # File name has format brdf_instrument_region_mindate_maxdate.png
        title = instrument.upper()+' BRDF at site '+region
        savename = '_'.join(['brdf', instrument, region, d_min, d_max])+'.png'
        self.plot_timeseries(datebins, plot_brdf, wavelengths, xlabel='Date',
                             title=title, savename=savename)

        # -------------------------------
        # Save to text file
        # -------------------------------
        # File name has format brdf_instrument_region_mindate_maxdate.csv
        csv_file = '_'.join(['brdf', instrument, region, d_min, d_max])+'.csv'
        self.save_as_text(datebins, ['BRDF', 'Reflectance', 'Random error', 'Systematic error'], wavelengths,
                          [brdf_arr, ref_arr, err_r_arr, err_s_arr], csv_file)

    @staticmethod
    def calc_kernel_f1(sun_zenith, sensor_zenith, relative_azimuth):
        """
        Calculates the F1 Kernel from Roujean (1992)

        :param sun_zenith: <numpy> array of sun zenith angles in radians.
        :param sensor_zenith: <numpy> array of sensor zenith angles in radians
        :param relative_azimuth: <numpy> array of relative (sun/sensor) azimuth angles in radians.
        :return: Roujean F1 kernel
        """

        # Just a bit of syntax candy
        # Do it in here so it goes out of scope after the method call
        cos = scipy.cos
        sin = scipy.sin
        tan = scipy.tan

        delta = scipy.sqrt(tan(sun_zenith)**2 + tan(sensor_zenith)**2 -
                           2*tan(sensor_zenith)*tan(sun_zenith)*cos(relative_azimuth))

        kernel_f1 = 1/(2*scipy.pi) * ((scipy.pi - relative_azimuth)*cos(relative_azimuth)
                                      + sin(relative_azimuth))
        kernel_f1 *= tan(sun_zenith)*tan(sensor_zenith)
        kernel_f1 -= 1/scipy.pi * (tan(sun_zenith) + tan(sensor_zenith) + delta)

        return kernel_f1

    @staticmethod
    def calc_kernel_f2(sun_zenith, sensor_zenith, relative_azimuth):
        """
        Calculates the F2 Kernel from Roujean (1992)

        :param sun_zenith: <numpy> array of sun zenith angles in radians.
        :param sensor_zenith: <numpy> array of sensor zenith angles in radians
        :param relative_azimuth: <numpy> array of relative (sun/sensor) azimuth angles in radians.
        :return: Roujean F2 kernel
        """

        # Just a bit of syntax candy
        # Do it in here so it goes out of scope after the method call
        cos = scipy.cos
        sin = scipy.sin
        acos = scipy.arccos

        scatt_angle = acos(cos(sun_zenith)*cos(sensor_zenith) +
                           sin(sun_zenith)*sin(sensor_zenith)*cos(relative_azimuth))

        kernel_f2 = 4/(3*scipy.pi) * (1/(cos(sun_zenith)+cos(sensor_zenith)))
        kernel_f2 *= (scipy.pi/2 - scatt_angle)*cos(scatt_angle) + sin(scatt_angle)
        kernel_f2 -= 1/3.0

        return kernel_f2

    def calc_roujean_coeffs(self, sun_zenith, sensor_zenith, relative_azimuth, reflectance):
        """
        Calculates the Roujean coefficients k0, k1 and k2, given the angles and reflectance

        :param sun_zenith: <numpy> array of sun zenith angles in radians.
        :param sensor_zenith: <numpy> array of sensor zenith angles in radians
        :param relative_azimuth: <numpy> array of relative (sun/sensor) azimuth angles in radians.
        :param reflectance: <numpy> array of reflectance (TOA in the case of dimitripy)
        :returns: numpy array with the k0, k1, k2 coefficients
        """

        # Remove any values that have nan for the reflectance.
        idx = ~np.isnan(reflectance) & ~np.isnan(sun_zenith)

        f_matrix = scipy.ones((reflectance[idx].shape[0], 3))  # There are 3 k_coeffs
        f_matrix[:, 1] = self.calc_kernel_f1(sun_zenith[idx], sensor_zenith[idx], relative_azimuth[idx])
        f_matrix[:, 2] = self.calc_kernel_f2(sun_zenith[idx], sensor_zenith[idx], relative_azimuth[idx])

        try:
            k_coeff, _, _, _ = scipy.linalg.lstsq(f_matrix, reflectance[idx].T)
        except:
            k_coeff = scipy.asarray([-999, -999, -999])  # Right thing to do?

        return k_coeff.T

    def calc_brdf(self, sun_zenith, sensor_zenith, relative_azimuth, k_coeff):
        """
        Calculates the BRDF given the viewing geometry and the Roujean k coefficients.

        :param sun_zenith: <numpy> array of sun zenith angles in radians.
        :param sensor_zenith: <numpy> array of sensor zenith angles in radians
        :param relative_azimuth: <numpy> array of relative (sun/sensor) azimuth angles in radians.
        :param k_coeff: <numpy> (n, 3) array of Roujean coefficients k0, k1 and k2 respectively
        :returns: brdf - array of reflectance values
        """

        f1 = self.calc_kernel_f1(sun_zenith, sensor_zenith, relative_azimuth)
        f2 = self.calc_kernel_f2(sun_zenith, sensor_zenith, relative_azimuth)
        brdf = k_coeff[0] + k_coeff[1]*f1 + k_coeff[2]*f2

        return brdf

    def brdf_timeseries(self, sun_zenith, sensor_zenith, relative_azimuth, reflectance,
                        dates, start_date, end_date, bin_size=5, k_start=None, k_end=None):
        """
        Plot timeseries of binned BRDF

        :param sun_zenith: <numpy> array of sun zenith angles in radians.
        :param sensor_zenith: <numpy> array of sensor zenith angles in radians
        :param relative_azimuth: <numpy> array of relative (sun/sensor) azimuth angles in radians.
        :param reflectance: <numpy> array of reflectances, nbands x ntimes
        :param dates: The times of the images, as array of python datetime objects
        :param start_date: Start date for the timeseries, as a python datetime object
        :param end_date: End date for the timeseries, as a python datetime object
        :param wavelengths: List of the sensor's bands
        :param bin_size: [Optional] Length of the time bins, in days. Default is 5 days.
        :param k_start: Date to use as start period when calculating k coefficients. If none given, defaults to start_date
        :param k_end: Date to use as end period when calculating k coefficients. If none given, defaults to end_date

        :returns: Binned dates (list) and binned BRDF, sensor reflectance, random error, systematic error
                  (arrays with shape nbands x ntimes)
        """
        # Keep within the dates that we have available
        start_date = max(start_date, min(dates))
        end_date = min(end_date, max(dates))

        # Initialise everything
        nbands = len(reflectance)
        current = start_date
        step = datetime.timedelta(days=bin_size)
        datebins = []
        k_coeffs = np.zeros([nbands, 3])
        first = True

        # Use the main timeseries start/end dates
        # for k coefficient calculation if no other dates
        # were specified
        if not k_start:
            k_start = start_date
        if not k_end:
            k_end = end_date

        # Calculate k coefficients for specified time period
        idx = (dates >= k_start) & (dates <= k_end)
        for band in range(nbands):
            k_coeffs[band, :] = self.calc_roujean_coeffs(sun_zenith[idx], sensor_zenith[idx], relative_azimuth[idx],
                                                         reflectance[band, idx])

        # Now model BRDF for the whole timeseries, using the
        # previously calculated k coefficients
        # -----------------------------------------
        # Step through the date bins
        while current <= end_date:
            # Pick out which images are in this bin
            idx = (dates >= current) & (dates < current+step)
            nvals = np.sum(idx)

            if nvals > 0:
                # Compute BRDF for each band
                brdf=[]
                for band in range(nbands):

                    # Calculate modelled brdf for this bin
                    brdf.append(self.calc_brdf(sun_zenith[idx], sensor_zenith[idx], relative_azimuth[idx], k_coeffs[band]))

                # Mean for this time bin
                # (Modelled brdf and our original reflectance)
                brdf = np.nanmean(np.array(brdf), axis=1)
                ref_bin = np.nanmean(reflectance[:, idx], axis=1)

                # Calculate error estimates for this time bin
                roujean_diff = reflectance[:, idx] - np.tile(brdf, (nvals, 1)).T
                rmse = np.sqrt(np.nanmean(roujean_diff**2, axis=1))
                err_r = 3 * rmse    # Random error
                err_s = rmse/np.sqrt(nvals)  # Systematic error

                # Add this time bin's results to the final arrays
                if first:
                    brdf_arr = brdf
                    ref_arr = ref_bin
                    err_r_arr = err_r
                    err_s_arr = err_s
                    first = False
                else:
                    brdf_arr = np.vstack([brdf_arr, brdf])
                    ref_arr = np.vstack([ref_arr, ref_bin])
                    err_r_arr = np.vstack([err_r_arr, err_r])
                    err_s_arr = np.vstack([err_s_arr, err_s])

                # Keep track of the bin's mean datetime, for plotting
                # Convert to timestamps first, to enable easy mean calculation
                datebins.append(libtools.mean_date(dates[idx]))

            current += step

        return datebins, brdf_arr, ref_arr, err_r_arr, err_s_arr

    @staticmethod
    def filter_timeseries(timeseries):
        """
        Filter the timeseries, removing any points more than 2 standard deviations away

        :param timeseries: Array of data to be filered
        :returns: Array with np.nan insterted at points that were more than 2 standard deviations from mean
        """
        ts_mean = np.nanmean(timeseries)
        ts_std = np.std(timeseries)

        bad = np.abs(timeseries - ts_mean) > 2*ts_std
        timeseries[bad] = np.nan
        return timeseries

    @staticmethod
    def plot_timeseries(times, ydata, line_labels, title=None, xlabel=None, ylabel=None, savename=None):
        """
        Line plot of the input data, with separate line per band

        :param times: 1d list of times, as python datetime objects
        :param ydata: The data to plot. 2d array with dimensions nbands x ntimes
        :param line_labels: Labels for the plot legend. List with length nbands
        :param title: [Optional] Title for the plot
        :param xlabel: [Optional] Text label for the x axis
        :param ylabel: [Optional] Text label for the y axis
        """
        nbands = len(line_labels)
        fig = plt.figure(figsize=(16,10))

        # Set up color cycling
        colormap = plt.cm.spectral
        plt.gca().set_color_cycle([colormap(i) for i in np.linspace(0, 0.9, nbands)])

        # Plot timeseries with one line per band
        lines = plt.plot(times, ydata, '-o')

        # Put legend box outside the plot window
        plt.legend(lines, line_labels, title='Bands',
                  loc='center left', bbox_to_anchor=(1, 0.5))

        # Labels
        if title:
            plt.title(title)
        if xlabel:
            plt.xlabel(xlabel)
        if ylabel:
            plt.ylabel(ylabel)

        # Show or save figure
        if savename:
            plt.savefig(savename, bbox_inches='tight', pad_inches=0)
        else:
            plt.show()

    @staticmethod
    def save_as_text(date_list, variables, bands, array_list, filename):
        """
        Save the BRDF and error estimates in a csv text file

        Use similar format as DIMITRI:

        * Going along the columns = different dates
        * Going down the rows, start with parameter 1 and have a row per wavelength. Then
          start the next parameter and have a row per wavelength etc.

        :param date_list: List of dates, to be used as column headers
        :param variables: List of the variable names we are printing
        :param bands: The wavelength values
        :param array_list: List of arrays of data to print. Should be
                           same number of arrays as we have names in variables
                           and the arrays should have dimensions len(date_list)x len(bands)
        :param filename: Name of the file to write to
        """
        strd = datetime.datetime.strftime
        header_row = ['Variable', 'Wavelength'] + [strd(d, '%Y-%m-%dT%H:%M:%S') for d in date_list]

        # Build a 2d array containing all the data
        array_2d = np.hstack(array_list).T  # Transpose to get time dimension as column

        # Write to CSV file
        csv_file = csv.writer(open(filename,"w"), delimiter=',', quoting=csv.QUOTE_MINIMAL)
        csv_file.writerow(header_row)
        for ind, row in enumerate(array_2d):
            # Add columns for the variable name and the band
            thisvar = ind // len(bands)
            thisband = ind % len(bands)
            csv_file.writerow([variables[thisvar], bands[thisband]]+list(row))


if __name__ == '__main__':
    main()