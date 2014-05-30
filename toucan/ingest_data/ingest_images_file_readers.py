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

        return data, time_temp

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
            timestr = image.get_sph().get_field('FIRST_LINE_TIME').get_elem()
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
