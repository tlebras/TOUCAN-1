from ingest_images_geo_tools import GeoTools
import os
import datetime
import pytz


class DataReaders():
    """
    Class to hold all of our different readers for different instruments and filetypes
    """
    def read_aatsr(self, ingest):
        """
        Read an AATSR file (.N1 format) and extract data for our region of interest

        :param ingest : An IngestImages object instance, which contains metadata and inputdir variables
        Returns data: Dictionary containing all the data arrays
        """
        # AATSR files have two directions, with separate viewing angle arrays
        ingest.aatsr_directions = ('nadir','fward')
        ingest.metadata['angle_names']={}

        for direction in ingest.aatsr_directions:
            # Define the names of the viewing angle datasets
            ingest.metadata['angle_names'].update({'VZA'+direction: 'view_elev_'+direction,
                                                   'VAA'+direction: 'view_azimuth_'+direction,
                                                   'SZA'+direction: 'sun_elev_'+direction,
                                                   'SAA'+direction: 'sun_azimuth_'+direction})
        # Define name of the time variable
        ingest.metadata['time_variable'] = 'FIRST_LINE_TIME'

        # Read in the data (extracting ROI and regridding at same time)
        data, time_temp = self.read_n1(ingest)

        # Convert time to python datetime object
        ingest.metadata['datetime'] = datetime.datetime.strptime(time_temp,'%d-%b-%Y %H:%M:%S.%f').replace(tzinfo=pytz.UTC)

        return data

    def read_meris(self, ingest):
        """
        Read a MERIS file (.N1 format) and extract data for our region of interest

        :param ingest : An IngestImages object instance, which contains metadata and inputdir variables
        Returns data: Dictionary containing all the data arrays
        """
        # Define the names of the viewing angle datasets
        ingest.metadata['angle_names'] = {'VZA': 'view_zenith',
                                          'VAA': 'view_azimuth',
                                          'SZA': 'sun_zenith',
                                          'SAA': 'sun_azimuth'}

        # Define name of the time variable
        ingest.metadata['time_variable'] = 'FIRST_LINE_TIME'

        # Read in the data (extracting ROI and regridding at same time)
        data, time_temp = self.read_n1(ingest)

        # Convert time to python datetime object
        ingest.metadata['datetime'] = datetime.datetime.strptime(time_temp,'%d-%b-%Y %H:%M:%S.%f').replace(tzinfo=pytz.UTC)

        return data

    def read_viirs(self, ingest):
        """
        Read a VIIRS file (.hdf format) and extract data for our region of interest

        :param ingest : An IngestImages object instance, which contains metadata and inputdir variables
        Returns data: Dictionary containing all the data arrays
        """
        # Define the names of the viewing angle datasets
        ingest.metadata['angle_names'] = {'VZA': 'SatelliteZenithAngle',
                                          'VAA': 'SatelliteAzimuthAngle',
                                          'SZA': 'SolarZenithAngle',
                                          'SAA': 'SolarAzimuthAngle'}
        # Define name of the time variable
        ingest.metadata['time_variable'] = 'Beginning_Time_IET'

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
        :param ingest : An IngestImages object instance, which contains metadata and inputdir variables
        Returns:
            data: dictionary containing the coordinates and data arrays
            time_temp: The value of whichever variable was specified by ingest.metadata['time_variable'].
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
            array = gdal.Open(ds).ReadAsArray()
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

        :param ingest : An IngestImages object instance, which contains metadata and inputdir variables
        Returns:
            data: dictionary containing the coordinates and data arrays
            time_temp: The value of whichever variable was specified by ingest.metadata['time_variable'].
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

        def get_variable(varname):
            array = image.get_band(varname).read_as_array()
            array_roi = GeoTools.extract_region_and_regrid(longitude, latitude, new_lon, new_lat, array)
            return array_roi

        # Get the variables that were specified in the metadata file
        for variable in ingest.metadata['variables']:
            data[variable] = get_variable(str(variable))  # str() is needed as json returns unicode

        # Get the viewing angles
        for angle in ingest.metadata['angle_names']:
            data[angle] = get_variable(ingest.metadata['angle_names'][angle])

        return data, time_temp