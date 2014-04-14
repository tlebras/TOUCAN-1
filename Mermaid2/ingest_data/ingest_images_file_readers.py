from ingest_images_geo_tools import GeoTools
import os

class DataReaders():
    '''
    Class to hold all of our different readers for different data file types
    '''
    def read_hdf_pyhdf(self, inputdir, metadata):
        """Read an HDF format data file (eg VIIRS), using pyhdf package
        
        Returns a dictionary containing the parameters that were requested in the metadata file
        (plus coordinates) for the specified region.
        :param metadata : the dictionary containing the metadata
        """
        import pyhdf.SD

        data={}
        hdf = pyhdf.SD.SD(os.path.join(inputdir,str(metadata['filename']))) # str() is needed as json returns unicode
        longitude = hdf.select('Longitude').get()
        latitude = hdf.select('Latitude').get()
        
        # Extract the indices for the region of interest. Specify using keywords so there can't be any
        # confusion about the order of lon and lat
        G = GeoTools()
        islice,jslice = G.extract_region(lon_array=longitude, lat_array=latitude, region=metadata['region_coords'])
        
        # Now subset coordinates and save to our data array
        data['longitude'] = longitude[islice,jslice]
        data['latitude'] = latitude[islice,jslice]
        # Do same for all the variables that were specified in the metadata file
        for variable in metadata['variables']:
            data[variable] = hdf.select(str(variable)).get()[islice,jslice] # str() is needed as json returns unicode
        hdf.end()
        return data
    
    def read_hdf_gdal(self, inputdir, metadata):
        """Read an HDF format data file (eg VIIRS), using GDAL package
        
        Returns a dictionary containing the parameters that were requested in the metadata file
        (plus coordinates) for the specified region.
        :param metadata : the dictionary containing the metadata
        """
        from osgeo import gdal

        data={}
        hdf = gdal.Open(os.path.join(inputdir,str(metadata['filename'])))
        datasets = hdf.GetSubDatasets()
        ds = [ds for ds,descr in datasets if ' Longitude ' in descr][0]
        longitude = gdal.Open(ds).ReadAsArray()
        ds = [ds for ds,descr in datasets if ' Latitude ' in descr][0]
        latitude = gdal.Open(ds).ReadAsArray()
        
        # Extract the indices for the region of interest. Specify using keywords so there can't be any
        # confusion about the order of lon and lat
        G = GeoTools()
        islice,jslice = G.extract_region(lon_array=longitude, lat_array=latitude, region=metadata['region_coords'])
        
        # Now subset coordinates and save to our data array
        data['longitude'] = longitude[islice,jslice]
        data['latitude'] = latitude[islice,jslice]
        # Do same for all the variables that were specified in the metadata file
        for variable in metadata['variables']:
            ds = [ds for ds,descr in datasets if ' '+variable+' ' in descr][0]
            data[variable] = gdal.Open(ds).ReadAsArray()
        del ds, hdf
        return data