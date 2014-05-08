import glob
import json
import os
import numpy as np
import matplotlib.pyplot as plt

from Mermaid2_db.models import *
from ingest_images_file_readers import DataReaders
from ingest_images_geo_tools import GeoTools

class IngestImages():
    
    def __init__(self, inputdir, outdir):
        """
        Initialise ingestion object with the input and output directory locations
        :param inputdir : Directory containing the input files
        :param outputdir : Top level archive directory to save geotiffs to
                           (region/instrument/year subdirectories will be automatically created)
        """
        self.inputdir = inputdir
        self.outdir = outdir

    def ingest_all(self):
        """
        Loop through all the files in the given input directory and ingest them
        """
        self.filelist = self.get_file_list()
        for thisfile in self.filelist:
            self.ingest_image(thisfile)
        
    def ingest_image(self, thisfile):
        """
        Ingest a single image. This method is called by ingest_all, or it can be called manually to ingest one file
        :param thisfile : The metadata file for the image to be ingested (including full directory path)
        """
        self.metafile = thisfile
        self.read_meta_file()
        self.read_data()
        self.save_geotiff()
        self.make_quicklook()
        self.add_to_database()
        self.tidy_up()
        
    def get_file_list(self):
        """Get a list of all the metadata files in the specified directory
        
        We assume metadata files have extension .json
        Returns list of metafiles
        """
        metafiles = glob.glob(self.inputdir+"/*.json")
        return metafiles
    
    def read_meta_file(self):
        """
        Read a JSON formatted metadata file (name in self.metafile), returning a dictionary
        """
        self.metadata = json.load(open(self.metafile))
    
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

        self.data = data
    
    def save_geotiff(self):
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
        rasterOrigin=(self.data['longitude'].min(), self.data['latitude'].min())
        dx = self.data['longitude'][1] - self.data['longitude'][0]
        dy = self.data['latitude'][1] - self.data['latitude'][0]
        GeoTools.array2raster(outfile, rasterOrigin, dx, dy, self.data, self.metadata['variables'])

        # Save the viewing angles in a separate file
        outfile = os.path.join(savedir, os.path.splitext(self.metadata['filename'])[0]+'_view_angles.tif')
        GeoTools.array2raster(outfile, rasterOrigin, dx, dy, self.data, self.metadata['angle_names'].keys())

    def make_quicklook(self):
        """
        Make a jpg for quick checking of the data

        Define reference wavelengths for R,G,B and pick out whichever instrument bands are closest to these.
        Pull out the relevant data arrays, then normalise values to be between 0 and 1 (which plt.imshow needs).
        """
        savedir = os.path.join(self.outdir, self.metadata['region_name'].upper(), self.metadata['instrument'].upper(),
                               str(self.metadata['datetime'].year))
        outfile = os.path.join(savedir, os.path.splitext(self.metadata['filename'])[0]+'.jpg')
        self.metadata['web_location'] = outfile

        # Define wavelengths to use as RGB bands
        bands = {'r':665.0, 'g':560.0, 'b':480.0}
        for i, band in enumerate(('r', 'g', 'b')):
            # Find which instrument band is closest, and extract corresponding data array
            # (assumes variables list is in same order as wavelengths list)
            varidx = np.argmin(np.abs(np.array(self.metadata['wavelengths']) - bands[band]))
            varname = self.metadata['variables'][varidx]

            temp = self.data[varname]
            if i == 0:
                rgb = np.empty((temp.shape[0], temp.shape[1],3))
            # Normalise the array to within 0-1, for plotting
            temp -= np.nanmin(temp)
            temp /= np.nanmax(temp)

            rgb[..., i] = temp

        plt.imshow(rgb, origin='lower', interpolation='None',
                   extent=[self.data['longitude'].min(), self.data['longitude'].max(),
                           self.data['latitude'].min(), self.data['latitude'].max()])
        plt.savefig(outfile)

    def add_to_database(self):
        """
        Add this image to the database
        
        Create new instances of ImageRegion and/or Instrument as required, otherwise fetch existing ones.
        Then add all the metadata to a new Image instance.
        :param data: the data dictionary
        """
        # Store region name as lower case, for consistency
        image_region,_ = ImageRegion.objects.get_or_create(region=self.metadata['region_name'].lower())
        instrument,_ = Instrument.objects.get_or_create(name=self.metadata['instrument'])
        for band in self.metadata['wavelengths']:
            wavelength,_ = InstrumentWavelength.objects.get_or_create(value=band, instrument=instrument)

        # If current instrument is AATSR, we have separate nadir/forward datasets
        # and need to the append direction name when retrieving angles from the dictionary
        if self.metadata['instrument'].lower() == 'aatsr':
            directions = self.aatsr_directions
        else:  # Leave direction blank for other instruments
            directions = ('',)  # Needs to be a list so we can iterate over it

        # Create the image object, making separate ones for each direction if required. Use get_or_create
        # to prevent duplicate records being created
        coords = self.metadata['region_coords']
        for direction in directions:
            image, new = Image.objects.get_or_create(region=image_region,
                                                     instrument=instrument,
                                                     archive_location=os.path.join(self.metadata['archive_location']),
                                                     web_location=os.path.join(self.metadata['web_location']),
                                                     top_left_point='POINT({0} {1})'.format(coords[2], coords[1]),
                                                     bot_right_point='POINT({0} {1})'.format(coords[3], coords[0]),
                                                     time=self.metadata['datetime'],
                                                     SZA=np.nanmean(self.data['SZA'+direction]),
                                                     SAA=np.nanmean(self.data['SAA'+direction]),
                                                     VZA=np.nanmean(self.data['VZA'+direction]),
                                                     VAA=np.nanmean(self.data['VAA'+direction]),
                                                     direction=(direction if direction.isalnum() else None))
            if not new:
                print "Image already ingested!"

    def tidy_up(self):
        """
        Move files to an "ingested" folder once they are processed, ready to be deleted later
        """
        # Create the ingested folder if necessary
        ingested_dir = os.path.join(self.inputdir,'ingested')
        if not os.path.isdir(ingested_dir):
            os.mkdir(ingested_dir)

        # Make sure the geotiff was created before moving files
        if os.path.isfile(self.metadata['archive_location']):
            # Metadata file
            os.rename(os.path.join(self.inputdir,self.metafile),
                      os.path.join(ingested_dir,self.metafile))
            # Data file
            os.rename(os.path.join(self.inputdir,self.metadata['filename']),
                      os.path.join(ingested_dir,self.metadata['filename']))