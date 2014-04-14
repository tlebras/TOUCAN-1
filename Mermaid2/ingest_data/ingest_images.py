from Mermaid2_db.models import *
import glob
import datetime
import pytz
import json
import numpy as np
import pyhdf.SD
import os
from osgeo import gdal, osr

class ingest_images:
    
    def __init__(self):
        pass
    
    def ingest_images(self, inputdir, outdir):
        """
        Main ingestion routine, which loops through all the files in the given input directory
        and processes them
        :param inputdir : directory containing the input files
        """
        self.inputdir = inputdir
        outdir = outdir
        files = self.get_file_list()
        for file in files:
            metadata = self.read_meta_file(file)
            data = self.read_data(metadata)
            self.save_geotiff(outdir, metadata, data)
        
    def get_file_list(self):
        """Get a list of all the data files, and all the metadata files in the specified directory
        We assume metadata files have extension .json, and data files are anything else in the directory
        :param inputdir : The directory to search
        Returns two lists: datafiles and metafiles
        """
        metafiles = glob.glob(self.inputdir+"/*.json")
        return metafiles
    
    def read_meta_file(self, file):
        metadata = json.load(open(file))
        return metadata
    
    def read_data(self, metadata):
        """
        Read in data from the data file (coordinates, and the parameters that were specified in the meta file)
        This method is a wrapper to call various others depending on the file type
        :param metadata: The metadata dictionary for this file
        Returns a dictionary "data" holding all the data
        """
        if metadata["filetype"]=="hdf":
            data = self.read_hdf_pyhdf(metadata)
        else:
            raise IOError("That filetype is not coded")
        
        return data
    
    def save_geotiff(self, outdir, metadata, data):
        """
        Create an appropriate directory structure within the output dir (outdir/region_name/instrument/year),
        and save the data to a geotiff file.
        :param outdir: the top output directory. Region and year subfolders will be created in here
        :param metadata: the metadata dictionary for this file, read earlier
        :param data: the data dictionary for this file 
        """
        savedir = os.path.join(outdir,metadata['region_name'],metadata['instrument'],str(metadata['year']))
        if not os.path.exists(savedir):
            os.makedirs(savedir)
        outfile = os.path.join(savedir,os.path.splitext(metadata['filename'])[0]+'.tif')
        
        rasterOrigin=(data['longitude'][-1,-1], data['latitude'][-1,-1])
        dx = data['longitude'][0,0]-data['longitude'][0,-1]
        dy = data['latitude'][0,0]-data['latitude'][0,-1]
        G = GeoTiffTools()
        G.array2raster(outfile, rasterOrigin, 0.008969, -0.0065295, data,
                                  metadata['variables'],rotate=np.arctan(dy/dx) )
        
    
    def read_hdf_pyhdf(self, metadata):
        """Read an HDF format data file (eg VIIRS), and return a dictionary containing
        the parameters that were requested in the metadata file (plus coordinates) for the 
        specified region        
        :param metadata : the dictionary containing the metadata
        """
        data={}
        hdf = pyhdf.SD.SD(os.path.join(self.inputdir,str(metadata['filename']))) # str() is needed as json returns unicode
        longitude = hdf.select('Longitude').get()
        latitude = hdf.select('Latitude').get()
        
        # Extract the indices for the region of interest. Specify using keywords so there can't be any
        # confusion about the order of lon and lat
        islice,jslice = self.extract_region(lon_array=longitude, lat_array=latitude, region=metadata['region_coords'])
        
        # Now subset coordinates and save to our data array
        data['longitude'] = longitude[islice,jslice]
        data['latitude'] = latitude[islice,jslice]
        # Do same for all the variables that were specified in the metadata file
        for variable in metadata['variables']:
            data[variable] = hdf.select(str(variable)).get()[islice,jslice] # str() is needed as json returns unicode
        hdf.end()
        return data
    
    def read_hdf_gdal(self, metadata):
        """Read an HDF format data file (eg VIIRS), and return a dictionary containing
        the parameters that were requested in the metadata file (plus coordinates) for the 
        specified region        
        :param metadata : the dictionary containing the metadata
        """
        
        data={}
        hdf = gdal.Open(os.path.join(self.inputdir,str(metadata['filename'])))
        datasets = hdf.GetSubDatasets()
        ds = [ds for ds,descr in datasets if ' Longitude ' in descr][0]
        longitude = gdal.Open(ds).ReadAsArray()
        ds = [ds for ds,descr in datasets if ' Latitude ' in descr][0]
        latitude = gdal.Open(ds).ReadAsArray()
        
        # Extract the indices for the region of interest. Specify using keywords so there can't be any
        # confusion about the order of lon and lat
        islice,jslice = self.extract_region(lon_array=longitude, lat_array=latitude, region=metadata['region_coords'])
        
        # Now subset coordinates and save to our data array
        data['longitude'] = longitude[islice,jslice]
        data['latitude'] = latitude[islice,jslice]
        # Do same for all the variables that were specified in the metadata file
        for variable in metadata['variables']:
            ds = [ds for ds,descr in datasets if ' '+variable+' ' in descr][0]
            data[variable] = gdal.Open(ds).ReadAsArray()
        del ds, hdf
        return data
    
    def extract_region(self, lon_array, lat_array, region):
        """
        Find which points are inside the region of interest.
        Returns two slice objects: islice, jslice
        :param lon_array: A numpy array containing the longitudes
        :param lat_array: A numpy array containing the latitudes
        :param region: A list containing the ROI corners: min lat, max lat, min lon, max lon
        """
        i,j = np.where((region[0]<=lat_array) & (lat_array<=region[1]) &
                       (region[2]<=lon_array) & (lon_array<=region[3]))
        islice = slice(i.min(),i.max()+1)
        jslice = slice(j.min(),j.max()+1)
        return islice, jslice
        
class GeoTiffTools():
        
    def array2raster(self, newRasterfn,rasterOrigin,pixelWidth,pixelHeight, data, variables, rotate=0):
        '''
        Convert data dictionary (of arrays) into a multiband GeoTiff
        :param newRasterfn: filename to save to
        :param rasterOrigin: location of top left corner
        :param pixelWidth: e-w pixel size
        :param pixelHeight: n-s pixel size
        :param data: dictionary containing the data arrays
        :param variables: list of which keys from the dictionary to output
        :param rotate: Optional rotation angle (in radians)
        '''
        array = data[data.keys()[0]]
        cols = array.shape[1]
        rows = array.shape[0]
        originX = rasterOrigin[0]
        originY = rasterOrigin[1]
    
        we_res = np.cos(rotate) * pixelWidth
        rotX = np.sin(rotate) * pixelWidth
        rotY = -np.sin(rotate) * pixelHeight
        ns_res = np.cos(rotate) * pixelHeight
    
        driver = gdal.GetDriverByName('GTiff')
        nbands = len(variables)
        outRaster = driver.Create(newRasterfn, cols, rows, nbands, gdal.GDT_UInt16)
        outRaster.SetGeoTransform((originX, we_res, rotX, originY, rotY, ns_res))
        for band,key in enumerate(variables, 1):
            outband = outRaster.GetRasterBand(band)
            outband.WriteArray(data[key])
            outband.FlushCache()
        outRasterSRS = osr.SpatialReference()
        outRasterSRS.ImportFromEPSG(4326)
        outRaster.SetProjection(outRasterSRS.ExportToWkt())