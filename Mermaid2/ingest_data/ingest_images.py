from Mermaid2_db.models import *
import glob
import datetime
import pytz
import json
import numpy as np
import pyhdf.SD
import os

class ingest_images:
    
    def __init__(self):
        pass
    
    def ingest_images(self, inputdir):
        """
        Main ingestion routine, which loops through all the files in the given input directory
        and processes them
        :param inputdir : directory containing the input files
        """
        self.inputdir = inputdir
        files = self.get_file_list()
        for file in files:
            metadata = self.read_meta_file(file)
            data = self.read_data(metadata)
        
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
        if metadata["filetype"]=="hdf":
            data = self.read_hdf(metadata)
        else:
            raise IOError("That filetype is not coded")
        
        return data
    
    def read_hdf(self, metadata):
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
        islice,jslice = self.extract_region(lon_array=longitude, lat_array=latitude, region=metadata['region'])
        
        # Now subset coordinates and save to our data array
        data['longitude'] = longitude[islice,jslice]
        data['latitude'] = latitude[islice,jslice]
        # Do same for all the variables that were specified in the metadata file
        for variable in metadata['variables']:
            data[variable] = hdf.select(str(variable)).get()[islice,jslice] # str() is needed as json returns unicode
        
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
        