import glob
import json
import os
import numpy as np

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
        :param inputdir : Directory containing the input files
        :param outputdir : Top level archive directory to save geotiffs to
                           (region/instrument/year subdirectories will be automatically created)
        """
        self.inputdir = inputdir
        self.outdir = outdir
        files = self.get_file_list()
        for thisfile in files:
            self.read_meta_file(thisfile)
            data = self.read_data()
            self.save_geotiff(data)
            self.add_to_database(data)
        
    def get_file_list(self):
        """Get a list of all the metadata files in the specified directory
        
        We assume metadata files have extension .json
        Returns list of metafiles
        """
        metafiles = glob.glob(self.inputdir+"/*.json")
        return metafiles
    
    def read_meta_file(self, file):
        """
        Read a JSON formatted metadata file, returning a dictionary
        """
        self.metadata = json.load(open(file))
    
    def read_data(self):
        """
        Read in data from the data file (coordinates, and the parameters that were specified in the meta file)
        
        This method is a wrapper to call various others depending on the file type
        Returns a dictionary "data" holding all the data
        """
        reader = DataReaders()
        instrument = self.metadata["instrument"].lower()
        if instrument=="aatsr":
            data = reader.read_aatsr(self)
        elif (instrument=='meris'):
            data = reader.read_meris(self)
        elif (instrument=='viirs'):
            data = reader.read_viirs(self)
        else:
            raise IOError("That instrument is not coded")
        
        return data
    
    def save_geotiff(self, data):
        """
        Save data to a geoTiff file, after creating appropriate directory structure

        :param data: the data dictionary for this file 
        """
        savedir = os.path.join(self.outdir, self.metadata['region_name'].upper(), self.metadata['instrument'].upper(),
                               str(self.metadata['datetime'].year))
        if not os.path.exists(savedir):
            os.makedirs(savedir)
        outfile = os.path.join(savedir, os.path.splitext(self.metadata['filename'])[0]+'.tif')
        self.metadata['archive_location'] = outfile # Save for later when we add to database
        
        # We give the origin as bottom left corner, then treat both dx and dy as +ve.
        rasterOrigin=(data['longitude'].min(), data['latitude'].min())
        dx = data['longitude'][1]-data['longitude'][0]
        dy = data['latitude'][1]-data['latitude'][0]
        GeoTools.array2raster(outfile, rasterOrigin, dx, dy, data, self.metadata['variables'])

        # Save the viewing angles in a separate file
        outfile = os.path.join(savedir, os.path.splitext(self.metadata['filename'])[0]+'_view_angles.tif')
        GeoTools.array2raster(outfile, rasterOrigin, dx, dy, data, self.metadata['angle_names'].keys())


    def add_to_database(self, data):
        """
        Add this image to the database
        
        Create new instances of ImageRegion and/or Instrument as required, otherwise fetch existing ones.
        Then add all the metadata to a new Image instance.
        :param data: the data dictionary
        """
        # Store region name as lower case, for consistency
        image_region,_ = ImageRegion.objects.get_or_create(region=self.metadata['region_name'].lower())
        instrument,_ = Instrument.objects.get_or_create(name=self.metadata['instrument'])

        # If current instrument is AATSR, we have separate nadir/forward datasets
        # and need to the append direction name when retrieving angles from the dictionary
        if self.metadata['instrument'].lower() == 'aatsr':
            directions = self.aatsr_directions
        else:  # Leave direction blank for other instruments
            directions = ('',)  # Needs to be a list so we can iterate over it

        # Create the image object, making separate ones for each direction if required
        coords = self.metadata['region_coords']
        for direction in directions:
            image = Image(region=image_region,
                          instrument=instrument,
                          archive_location=os.path.join(self.metadata['archive_location']),
                          web_location='web_location',
                          top_left_point='POINT({0} {1})'.format(coords[2], coords[1]),
                          bot_right_point='POINT({0} {1})'.format(coords[3], coords[0]),
                          time=self.metadata['datetime'],
                          SZA=np.nanmean(data['SZA'+direction]),
                          SAA=np.nanmean(data['SAA'+direction]),
                          VZA=np.nanmean(data['VZA'+direction]),
                          VAA=np.nanmean(data['VAA'+direction])
                          )
            # For images with a direction, add this as an attribute to the Image object
            if direction.isalnum():
                image.direction = direction
            
            image.save()