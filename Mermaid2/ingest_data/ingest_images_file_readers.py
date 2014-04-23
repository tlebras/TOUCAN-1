from ingest_images_geo_tools import GeoTools
import os
import datetime
import pytz


class DataReaders():
    """
    Class to hold all of our different readers for different data file types
    """
    def read_hdf_gdal(self, inputdir, metadata):
        """Read an HDF format data file (eg VIIRS), using GDAL package

        Extract the region of interest, and at the same time regrid to a regular grid.
        Returns a dictionary containing the parameters that were requested in the metadata file
        (plus coordinates) for the specified region.
        :param inputdir : Directory location of the file
        :param metadata : the dictionary containing the metadata
        """
        from osgeo import gdal

        data = {}
        hdf = gdal.Open(os.path.join(inputdir,str(metadata['filename'])))

        # Get the time 
        if metadata['instrument'].lower()=='viirs':
            # microseconds since 00:00 1st Jan 1958
            micros = float(hdf.GetMetadataItem('Beginning_Time_IET'))
            epoch = datetime.datetime(1958,1,1)
            metadata['datetime'] = (epoch + datetime.timedelta(microseconds=micros)).replace(tzinfo=pytz.utc)

        # Regrid coordinates and extract region of interest
        datasets = hdf.GetSubDatasets()
        ds = [ds for ds,descr in datasets if ' Longitude ' in descr][0]
        longitude = gdal.Open(ds).ReadAsArray()
        ds = [ds for ds,descr in datasets if ' Latitude ' in descr][0]
        latitude = gdal.Open(ds).ReadAsArray()

        new_lon, new_lat = GeoTools.get_new_lat_lon(longitude, latitude, metadata['region_coords'])
        data['longitude'] = new_lon
        data['latitude'] = new_lat

        # Helper function to read a dataset, then extract and regrid to region of interest
        def get_variable(varname):
            ds = [ds for ds,descr in datasets if ' '+varname+' ' in descr][0]
            array = gdal.Open(ds).ReadAsArray()
            array_roi = GeoTools.extract_region_and_regrid(longitude, latitude, new_lon, new_lat, array)
            return array_roi

        # Get the variables that were specified in the metadata file
        for variable in metadata['variables']:
            data[variable] = get_variable(str(variable))  # str() is needed as json returns unicode

        del ds, hdf
        return data

    def read_n1(self, inputdir, metadata):
        """
        Read N1 file (eg MERIS or AATSR), using pyepr package
        """
        import epr

        data = {}
        image = epr.open(os.path.join(inputdir,str(metadata['filename'])))

        # Get date/time (is a string like '06-APR-2012 09:00:56.832999')
        datestr = image.get_sph().get_field('FIRST_LINE_TIME').get_elem()
        metadata['datetime'] = datetime.datetime.strptime(datestr,'%d-%b-%Y %H:%M:%S.%f').replace(tzinfo=pytz.UTC)

        # Regrid coordinates and extract region of interest
        longitude = image.get_band('longitude').read_as_array()
        latitude = image.get_band('latitude').read_as_array()
        new_lon, new_lat = GeoTools.get_new_lat_lon(longitude, latitude, metadata['region_coords'])
        data['longitude'] = new_lon
        data['latitude'] = new_lat

        def get_variable(varname):
            array = image.get_band(varname).read_as_array()
            array_roi = GeoTools.extract_region_and_regrid(longitude, latitude, new_lon, new_lat, array)
            return array_roi

        # Get the variables that were specified in the metadata file
        for variable in metadata['variables']:
            data[variable] = get_variable(str(variable))  # str() is needed as json returns unicode

        return data