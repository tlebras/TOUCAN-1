import glob
import json
import os

from Mermaid2_db.models import *
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
            self.add_to_database(metadata)
        
    def get_file_list(self):
        """Get a list of all the metadata files in the specified directory
        
        We assume metadata files have extension .json
        :param inputdir : The directory to search
        Returns two lists: datafiles and metafiles
        """
        metafiles = glob.glob(self.inputdir+"/*.json")
        return metafiles
    
    def read_meta_file(self, file):
        """
        Read a JSON formatted metadata file, returning a dictionary
        """
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
        instrument = metadata["instrument"].lower()
        if instrument=="viirs":
            data = reader.read_hdf_pyhdf(self.inputdir,metadata)
        elif (instrument=='meris')|(instrument=='aatsr'):
            data = reader.read_n1(self.inputdir,metadata)
        else:
            raise IOError("That filetype is not coded")
        
        return data
    
    def save_geotiff(self, outdir, metadata, data):
        """
        Save data to a geoTiff file, after creating appropriate directory structure

        :param outdir: the top output directory. Region/Instrument/Year subfolders will be created in here
        :param metadata: the metadata dictionary for this file, read earlier
        :param data: the data dictionary for this file 
        """
        savedir = os.path.join(outdir,metadata['region_name'],metadata['instrument'],str(metadata['datetime'].year))
        if not os.path.exists(savedir):
            os.makedirs(savedir)
        outfile = os.path.join(savedir,os.path.splitext(metadata['filename'])[0]+'.tif')
        metadata['archive_location'] = outfile # Save for later when we add to database
        
        # We give the origin as bottom left corner, then treat both dx and dy as +ve.
        rasterOrigin=(data['longitude'].min(), data['latitude'].min())
        dx = data['longitude'][1]-data['longitude'][0]
        dy = data['latitude'][1]-data['latitude'][0]
        G = GeoTools()
        G.array2raster(outfile, rasterOrigin, dx, dy, data, metadata['variables'])

    def add_to_database(self, metadata):
        """
        Add this image to the database
        
        Create new instances of ImageRegion and/or Instrument as required, otherwise fetch existing ones.
        Then add all the metadata to a new Image instance.
        :param metadata: the metadata dictionary
        """
        # Store region name as lower case, for consistency
        image_region,_ = ImageRegion.objects.get_or_create(region=metadata['region_name'].lower())
        instrument,_ = Instrument.objects.get_or_create(name=metadata['instrument'])
        
        image = Image(region=image_region, instrument=instrument, 
                      archive_location=os.path.join(metadata['archive_location']),
                      web_location = 'web_location',
                      top_left_point = 'POINT({0} {1})'.format(metadata['region_coords'][2], metadata['region_coords'][1]),
                      bot_right_point = 'POINT({0} {1})'.format(metadata['region_coords'][3], metadata['region_coords'][0]),
                      time=metadata['datetime'],
                      )
        image.save()