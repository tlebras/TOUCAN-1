from ingest_images_geo_tools import GeoTools
import os
import datetime
from calendar import isleap
import pytz
import numpy as np

class DataReaders():
    """
    Class to hold all of our different readers for different instruments and filetypes
    """
    def read_aatsr(self, ingest):
        """
        Read an AATSR file (.N1 format) and extract data for our region of interest

        Default values are specified for variable names, wavelengths etc, but these can be overridden
        by user if they are put in the json file. Default is to read Reflectance

        :param ingest: An IngestImages object instance, which contains metadata and inputdir variables
        :return: Dictionary containing all the data arrays
        """
        # Set the AATSR viewing direction
        direction = ingest.metadata['direction']

        # Define the names of the viewing angle datasets, if not overridden by metadata file
        if not 'angle_names' in ingest.metadata.keys():
            ingest.metadata['angle_names'] = {}
            ingest.metadata['angle_names'].update({'VZA': 'view_elev_'+direction,
                                                   'VAA': 'view_azimuth_'+direction,
                                                   'SZA': 'sun_elev_'+direction,
                                                   'SAA': 'sun_azimuth_'+direction})

        # Define name of the time variable, if not overridden by metadata file
        if not 'time_variable' in ingest.metadata.keys():
            ingest.metadata['time_variable'] = 'FIRST_LINE_TIME'

        # Define wavelengths, if not overridden by metadata file
        if not 'wavelengths' in ingest.metadata.keys():
            ingest.metadata['wavelengths'] = (550, 660, 865, 1610, 3700, 10850, 12000)

        # Define the variable names to read in, if not overridden by metadata file
        # Default to Reflectance
        if not 'variables' in ingest.metadata.keys():
            ingest.metadata['vartype'] = 'reflectance'
            varnames = []
            for band_name in ('reflec_dir_0550', 'reflec_dir_0670', 'reflec_dir_0870', 'reflec_dir_1600', 
                              'btemp_dir_0370', 'btemp_dir_1100', 'btemp_dir_1200'):
                    varnames.append(band_name.replace('dir', direction.lower()))
            ingest.metadata['variables'] = varnames

        # Name of the flag array, and which bit to use
        if not 'flag_name' in ingest.metadata.keys():
            ingest.metadata['flag_name'] = 'confid_flags_'+direction.lower()
            ingest.metadata['flag_bit'] = 3

        # Read in the data (extracting ROI and regridding at same time)
        data, time_temp = self.read_n1(ingest)

        # Convert time to python datetime object
        ingest.metadata['datetime'] = datetime.datetime.strptime(time_temp,'%d-%b-%Y %H:%M:%S.%f').replace(tzinfo=pytz.UTC)

        return data

    def read_meris(self, ingest):
        """
        Read a MERIS file (.N1 format) and extract data for our region of interest

        Default values are specified for variable names, wavelengths etc, but these can be overridden
        by user if they are put in the json file. Default is to read Radiance.

        :param ingest: An IngestImages object instance, which contains metadata and inputdir variables
        :return: Dictionary containing all the data arrays
        """
        # Define the names of the viewing angle datasets, if not overridden by metadata file
        if not 'angle_names' in ingest.metadata.keys():
            ingest.metadata['angle_names'] = {'VZA': 'view_zenith',
                                              'VAA': 'view_azimuth',
                                              'SZA': 'sun_zenith',
                                              'SAA': 'sun_azimuth'}

        # Define name of the time variable, if not overridden by metadata file
        if not 'time_variable' in ingest.metadata.keys():
            ingest.metadata['time_variable'] = 'FIRST_LINE_TIME'

        # Define wavelengths, if not overridden by metadata file
        if not 'wavelengths' in ingest.metadata.keys():
            ingest.metadata['wavelengths'] = (412, 443, 490, 510, 560, 620, 665, 681, 708, 753,
                                              761, 778, 865, 885, 900)

        # Define the variable names to read in, if not overridden by metadata file
        # Default to Radiance
        if not 'variables' in ingest.metadata.keys():
            ingest.metadata['vartype'] = 'radiance'
            varnames = []
            for band,_ in enumerate(ingest.metadata['wavelengths'], 1):
                varnames.append('radiance_'+str(band))
            ingest.metadata['variables'] = varnames

        # Name of the flag array, and which bit to use
        if not 'flag_name' in ingest.metadata.keys():
            ingest.metadata['flag_name'] = 'l1_flags'
            ingest.metadata['flag_bit'] = 7

        # Read in the data (extracting ROI and regridding at same time)
        data, time_temp = self.read_n1(ingest)

        # Convert time to python datetime object
        ingest.metadata['datetime'] = datetime.datetime.strptime(time_temp,'%d-%b-%Y %H:%M:%S.%f').replace(tzinfo=pytz.UTC)

        return data

    def read_viirs(self, ingest):
        """
        Read a VIIRS file (.hdf format) and extract data for our region of interest

        Default values are specified for variable names, wavelengths etc, but these can be overridden
        by user if they are put in the json file. Default is to read Reflectance

        :param ingest: An IngestImages object instance, which contains metadata and inputdir variables
        :return: Dictionary containing all the data arrays
        """
        # Define the names of the viewing angle datasets, if not overridden by metadata file
        if not 'angle_names' in ingest.metadata.keys():
            ingest.metadata['angle_names'] = {'VZA': 'SatelliteZenithAngle',
                                              'VAA': 'SatelliteAzimuthAngle',
                                              'SZA': 'SolarZenithAngle',
                                              'SAA': 'SolarAzimuthAngle'}
        # Define name of the time variable, if not overridden by metadata file
        if not 'time_variable' in ingest.metadata.keys():
            ingest.metadata['time_variable'] = 'Beginning_Time_IET'

        # Define wavelengths, if not overridden by metadata file
        if not 'wavelengths' in ingest.metadata.keys():
            ingest.metadata['wavelengths'] = (412, 445, 488, 555, 672, 746, 865, 1240, 1378, 1610, 2250, 
                                              3700, 4050, 8550, 10763, 12013)

        # Define the variable names to read in, if not overridden by metadata file
        # Default to Reflectance
        if not 'variables' in ingest.metadata.keys():
            varnames = []
            vartype = 'Reflectance'
            ingest.metadata['vartype'] = vartype
            for band,_ in enumerate(ingest.metadata['wavelengths'], 1):
                if not ((vartype == 'Reflectance') & (band > 11)):  # Reflectance only has bands 1-11
                    varnames.append(vartype+'_M'+str(band))
            ingest.metadata['variables'] = varnames

        # Read in the data (extracting ROI and regridding at same time)
        data, time_temp = self.read_hdf_gdal(ingest)

        # Convert time (microseconds since 00:00 1st Jan 1958) to python datetime object
        micros = float(time_temp)
        epoch = datetime.datetime(1958,1,1)
        ingest.metadata['datetime'] = (epoch + datetime.timedelta(microseconds=micros)).replace(tzinfo=pytz.utc)

        return data

    def read_hdf_gdal(self, ingest):
        """Read an HDF format data file (eg VIIRS), using GDAL package

        Extract the region of interest, and at the same time regrid to a regular grid.
        Returns a dictionary containing the parameters that were requested in the metadata file
        (plus coordinates) for the specified region.
        
        :param ingest: An IngestImages object instance, which contains metadata and inputdir variables
        :return: Dictionary containing the coordinates and data arrays
        :return: The value of whichever variable was specified by ingest.metadata['time_variable'].
                 This will be converted to a proper datetime in the calling method.
        """
        from osgeo import gdal

        data = {}
        hdf = gdal.Open(os.path.join(ingest.inputdir, str(ingest.metadata['filename'])))

        # Get the time
        time_temp = float(hdf.GetMetadataItem(ingest.metadata['time_variable']))

        # Regrid coordinates and extract region of interest
        datasets = hdf.GetSubDatasets()
        ds = [ds for ds,descr in datasets if ' Longitude ' in descr][0]
        longitude = gdal.Open(ds).ReadAsArray()
        ds = [ds for ds,descr in datasets if ' Latitude ' in descr][0]
        latitude = gdal.Open(ds).ReadAsArray()

        new_lon, new_lat = GeoTools.get_new_lat_lon(longitude, latitude, ingest.metadata['region_coords'])
        data['longitude'] = new_lon
        data['latitude'] = new_lat

        # Helper function to read a dataset, then extract and regrid to region of interest
        def get_variable(varname):
            ds = [ds for ds,descr in datasets if ' '+varname+' ' in descr][0]
            # Not all bands have offset/scale
            try:
                scale_factor = float(gdal.Open(ds).GetMetadataItem('Scale'))
            except TypeError:
                scale_factor = 1.0
            try:
                offset = float(gdal.Open(ds).GetMetadataItem('Offset'))
            except TypeError:
                offset = 0.0
            array = (gdal.Open(ds).ReadAsArray() - offset) * scale_factor
            array_roi = GeoTools.extract_region_and_regrid(longitude, latitude, new_lon, new_lat, array)
            return array_roi

        # Get the variables that were specified in the metadata file
        for variable in ingest.metadata['variables']:
            data[variable] = get_variable(str(variable))  # str() is needed as json returns unicode

        # Get the viewing angles
        for angle in ingest.metadata['angle_names']:
            data[angle] = get_variable(ingest.metadata['angle_names'][angle])

        del ds, hdf
        return data, time_temp

    def read_n1(self, ingest):
        """
        Read N1 file (eg MERIS or AATSR), using pyepr package

        Extract the region of interest, and at the same time regrid to a regular grid.
        Returns a dictionary containing the parameters that were requested in the metadata file
        (plus coordinates) for the specified region.

        :param ingest: An IngestImages object instance, which contains metadata and inputdir variables
        :return: Dictionary containing the coordinates and data arrays
        :return: The value of whichever variable was specified by ingest.metadata['time_variable'].
                 This will be converted to a proper datetime in the calling method.
        """
        import epr

        data = {}
        image = epr.open(os.path.join(ingest.inputdir, str(ingest.metadata['filename'])))

        # Get date/time (is a string like '06-APR-2012 09:00:56.832999')
        time_temp = image.get_sph().get_field(ingest.metadata['time_variable']).get_elem()

        # Regrid coordinates and extract region of interest
        longitude = image.get_band('longitude').read_as_array()
        latitude = image.get_band('latitude').read_as_array()
        new_lon, new_lat = GeoTools.get_new_lat_lon(longitude, latitude, ingest.metadata['region_coords'])
        data['longitude'] = new_lon
        data['latitude'] = new_lat

        # Read in flag array, and extract bit for valid/invalid points to remove missing data points
        if 'flag_name' in ingest.metadata.keys():
            flag_array = image.get_band(ingest.metadata['flag_name']).read_as_array()
            flag_array = flag_array >> ingest.metadata['flag_bit'] & 1
        else:
            flag_array = None

        # Helper function to read a dataset, then extract and regrid to region of interest
        # NB we read using the higher level get_band, instead of get_database. This is much simpler to use, and also 
        # means that values have already had scaling applied and are converted to floats
        def get_variable(varname):
            array = image.get_band(varname).read_as_array()
            if flag_array is not None:
                array[flag_array==1] = np.nan
            array_roi = GeoTools.extract_region_and_regrid(longitude, latitude, new_lon, new_lat, array)
            return array_roi

        # Get the variables that were specified in the metadata file
        for variable in ingest.metadata['variables']:
            data[variable] = get_variable(str(variable))  # str() is needed as json returns unicode

        # Get the viewing angles
        for angle in ingest.metadata['angle_names']:
            data[angle] = get_variable(ingest.metadata['angle_names'][angle])

        # If this is MERIS reflectance, apply solar correction
        if ingest.metadata['instrument'].lower() == 'meris' and ingest.metadata['vartype'] == 'radiance':
            data = self.correct_MERIS(image, longitude, latitude, new_lon, new_lat, ingest.metadata, data)

        # If this is AATSR reflectance, apply corrections
        if ingest.metadata['instrument'].lower() == 'aatsr' and ingest.metadata['vartype'] == 'reflectance':
            data = self.correct_AATSR(image, ingest.metadata, data)

        return data, time_temp

    def correct_AATSR(self, image, metadata, data):
        """
        Apply corrections to AATSR reflectance and angles

        :param image: Open epr image object
        :param metadata: The metadata dictionary for this image
        :param data: Data dictionary of uncorrected data
        :returns: Updated data dictionary with corrected data
        """
        # ----------------------------------------
        # Correct angles: convert elevation (zenith==90)
        # to zenith angle (zenith==0)
        # ----------------------------------------
        for angle in ('SZA', 'VZA'):
            data[angle] = 90 - data[angle]

        # ----------------------------------------
        # Correct reflectance for sun zenith angle
        # ----------------------------------------
        sun_zenith = data['SZA']
        for var in metadata['variables']:
            # Only apply to the reflectance bands, not the brightness temp bands
            if 'reflec' in var:
                data[var] *= 0.01/np.cos(np.deg2rad(sun_zenith))

        # ----------------------------------------
        # Correct the 1600nm band for non linearity
        # (This has been done already usually, need
        # to check the value of the GC1 filename
        # that was used in processing)
        # ----------------------------------------
        band1600 = metadata['variables'][3]  # 1600nm is band 3 in our index
        dsd_ind = 30  # Index of the GC1 file in the DSD list
        gc1 = image.get_band(band1600).product.get_dsd_at(dsd_ind).filename
        if gc1 == 'ATS_GC1_AXVIEC20020123_073430_20020101_000000_20200101_000000':
            # Nonlinearity coefficients from pre-launch calibration
            coeffs = [-0.000027, -0.1093, 0.009393, 0.001013]
            # Convert 1.6um reflectance back to raw signal using linear conversion
            volts = data[band1600]/0.192 * -0.816
            # Convert 1.6um raw signal to reflectance using non-linear conversion function
            data[band1600] = np.pi*(coeffs[0] + coeffs[1]*volts + coeffs[2]*volts**2 + coeffs[3]*volts**3)/1.553

        # ----------------------------------------
        # Remove existing drift correction and
        # apply new one using look up table
        # ----------------------------------------
        timestr = image.get_sph().get_field(metadata['time_variable']).get_elem()
        acq_date = datetime.datetime.strptime(timestr,'%d-%b-%Y %H:%M:%S.%f')
        for band, var in enumerate(metadata['variables']):
            # Only apply to the reflectance bands, not the brightness temp bands
            if 'reflec' in var:
                uncorrected = self.aatsr_drift_remove(gc1, data[var], band, acq_date)
                data[var] = self.aatsr_drift_apply(uncorrected, band, acq_date)

        return data

    @staticmethod
    def aatsr_drift_remove(gc1, reflectance, band, acq_date):
        """
        Remove drift correction from AATSR reflectance

        :param gc1: Name of the GC1 file that was used
        :param reflectance: Array of reflectance for this band
        :param band: Index of this band (0-3)
        :param acq_date: Acquisition date for this image
        :returns: Array of reflectance with drift correction removed
        """
        # Get date of the CG1 file
        gc1_date = datetime.datetime.strptime(gc1[14:29], '%Y%m%d_%H%M%S')

        # Find which correction was applied for that date
        exp_start = datetime.datetime(2005, 11, 29, 13, 20, 26)
        exp_end = datetime.datetime(2006, 12, 18, 20 ,14, 15)
        none_start = datetime.datetime(2010, 4, 4)
        none_end = datetime.datetime(2010, 7, 13)
        if gc1_date < exp_start or (none_start <= gc1_date < none_end):
            corr = 0
        elif exp_start <= gc1_date < exp_end:
            corr = 1
        else:
            corr = 2

        # Calculate drift correction
        K = [0.034, 0.021, 0.013, 0.002]  # yearly drift rates for exponential drift
        A = np.array([[0.083,  1.5868E-3],  # Thin film drift model coefficients
                      [0.056,  1.2374E-3],
                      [0.041,  9.6111E-4]])
        ndays = (datetime.datetime(2002, 3, 1) - acq_date).days  # Days since envisat launch

        # No correction
        drift = 1.0

        # Exponential drift correction
        if (band==3 and corr==0) or (band!=3 and corr==1):
            drift = np.exp(K[band] * ndays/365.0)

        # Thin film drift correction
        if band!=3 and corr==2:
            drift = 1.0 + A[band, 0]*np.sin(A[band, 1]*ndays)**2

        uncorrected = reflectance * drift
        return uncorrected

    @staticmethod
    def aatsr_drift_apply(reflectance, band, acq_date):
        """
        Apply drift correction to AATSR reflectance

        :param reflectance: Array of the uncorrected reflectance values
        :param band: Index of this band (0-3)
        :param acq_date: Acquisition date of this image
        :returns: Array of drift corrected reflectance values
        """
        if acq_date <= datetime.datetime(2002, 3, 1):
            raise "Error: Acquisition date is before ENVISAT Launch"

        # Read in the look up table
        # Dates are in column 2, format like 01-JAN-2010
        # Columns 4+ contain the drift values. They are in pairs of drift then error for each band, so 
        # we read alternating columns to just get the drift values.
        aux_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'aux_files'))
        drift_lut_file = os.path.join(aux_path, 'AATSR_VIS_DRIFT_V02-01.DAT')
        with open(drift_lut_file) as fp:
            lines = fp.readlines()
        nhead = 5   # Header lines
        lut_dates = [datetime.datetime.strptime(line.split()[1], '%d-%b-%Y') for line in lines[nhead:]]
        lut_drift = np.array([[float(value) for value in line.split()[3::2]] for line in lines[nhead:]])

        # Convert dates to timestamps, so they can be interpolated
        acq_date = float(acq_date.strftime('%s'))
        lut_dates = [float(date.strftime('%s')) for date in lut_dates]

        # Interpolate to get drift at this acquisition date
        drift = np.interp(acq_date, lut_dates, lut_drift[:,band])

        # Apply correction
        corrected = reflectance / drift
        return corrected

    @staticmethod
    def correct_MERIS(image, old_lon, old_lat, new_lon, new_lat, metadata, data):
            """
            Correct MERIS TOA radiance according to solar irradiance model
            
            :param image: An open image file
            :param old_lon: Original longitude array (needed for regridding)
            :param old_lat: Original latitude array (needed for regridding)
            :param new_lon: New longitude array (needed for regridding)
            :param new_lat: New latitude array (needed for regridding)
            :param metadata: Image metadata dictionary
            :param data: Dictionary containing the data
            :returns: Data, with the reflectances corrected

            """
            # Get detector index
            ccd_ind = image.get_band('detector_index').read_as_array()

            # Read in solar model
            aux_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'aux_files'))
            solar_file = os.path.join(aux_path, 'MERIS_Irradiances_Model2004.txt')
            with open(solar_file) as fp:
                lines = fp.readlines()

            irr_full = []
            for line in lines[1:]:
                irr_full.append(np.array([float(s) for s in line.split()[1:]]))
            irr_full = np.vstack(irr_full)

            # Resample to reduced resolution
            irr_red = np.zeros((925, 15))
            for ind in range(irr_red.shape[0]):
                irr_red[ind,:] = np.mean(irr_full[ind*4:(ind+1)*4, :], axis=0)

            # Build the solar irradiance array
            sun_irr = irr_red[ccd_ind, :]
            sun_irr[ccd_ind<0] = np.nan  # ccd_ind=-1 are invalid pixels

            # Get date information
            timestr = image.get_sph().get_field(metadata['time_variable']).get_elem()
            date = datetime.datetime.strptime(timestr,'%d-%b-%Y %H:%M:%S.%f').replace(tzinfo=pytz.UTC)
            day_in_year = date.timetuple().tm_yday
            year_length = 365 + isleap(date.year)

            # Correct solar irradiance for earth-sun distance
            sun_irr *= (1 + 0.0167*np.cos(2*np.pi*(day_in_year-3.0)/year_length))**2

            # Apply correction to TOA reflectance
            sun_zenith = data['SZA']
            for band, varname in enumerate(metadata['variables']):
                sun_irr_band = GeoTools.extract_region_and_regrid(old_lon, old_lat, new_lon, new_lat,
                                                                  sun_irr[..., band])
                data[varname] *= np.pi * np.cos(np.deg2rad(sun_zenith))/sun_irr_band

            return data
