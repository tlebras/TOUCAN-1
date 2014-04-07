from Mermaid2_db.models import *
import glob
import datetime
import pytz
import json

class ingest_images:
    
    def __init__(self):
        pass
    
    def get_file_list(self, inputdir):
        """Get a list of all the data files, and all the metadata files in the specified directory
        We assume metadata files have extension .json, and data files are anything else in the directory
        :param inputdir : The directory to search
        Returns two lists: datafiles and metafiles
        """
        metafiles = glob.glob(inputdir+"/*.json")
        return metafiles
    
    def read_meta_file(self, file):
        metadata = json.load(open(file))
        return metadata
    
    def read_data(self, metadata):
        if metadata["filetype"]=="hdf":
            self.read_hdf(metadata)
        else:
            raise IOError("That filetype is not coded")
    
    def read_hdf(self, metadata):
        pass
        