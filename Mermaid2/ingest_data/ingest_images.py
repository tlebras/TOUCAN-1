from Mermaid2_db.models import *
import glob
import json
import numpy as np
import os
from ingest_images_file_readers import DataReaders
from ingest_images_geo_tools import GeoTools

class IngestImages():
    
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
        """Get a list of all the metadata files in the specified directory
        
        We assume metadata files have extension .json
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
        reader = DataReaders()
        filetype = metadata["filetype"]
        if filetype=="hdf":
            data = reader.read_hdf_pyhdf(self.inputdir,metadata)
        else:
            raise IOError("That filetype is not coded")
        
        return data
    
    def save_geotiff(self, outdir, metadata, data):
        """
        Save data to a geoTiff file, after creating approproate directory structure

        :param outdir: the top output directory. Region/Instrument/Year subfolders will be created in here
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
        G = GeoTools()
        G.array2raster(outfile, rasterOrigin, 0.008969, -0.0065295, data,
                                  metadata['variables'],rotate=np.arctan(dy/dx) )
