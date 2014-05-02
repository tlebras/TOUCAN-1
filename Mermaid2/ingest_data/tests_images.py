import os
from mock import *
import numpy as np

from django.test import TestCase

from ingest_data.ingest_images import *
from ingest_data.ingest_images_file_readers import *
from ingest_data.ingest_images_geo_tools import *

class InjestToolsSetup(TestCase):
    """Setup the test directory and files
    """
    def setUp(self):
        self.testdir = "/home/mermaid2/mermaid2/Mermaid2/ingest_data/images/input/"
        self.testdata = os.path.join(self.testdir,"NPP_VMAE_L1.A2013302.1140.P1_03001.2013302210836.gscs_000500784042.hdf")
        self.testmeta = os.path.join(self.testdir,"viirs.json")
        self.ingest = IngestImages(self.testdir, self.testdir+'../output')

class InjestToolsTest(InjestToolsSetup):
    # Program checks to see if there's any new images in the staging area
    
    # List the files and their associated metadata document (eg a JSON file)
    def test_list_files(self):
        """Check that get_file_list returns the correct file list
        """
        metafiles = self.ingest.get_file_list()
        self.assertEquals(len(metafiles),3)
            
    # Extract data from the JSON file
    # File type (hdf etc), coordinates of ROI, the variables to pull out, the bands
    def test_metafile_read(self):
        """Check that read_meta_file returns a dictionary with the correct values
        """
        testdict = eval(open(self.testmeta).read()) # Read json file directly as a python dictionary
        self.ingest.read_meta_file(self.testmeta)
        self.assertDictEqual(self.ingest.metadata, testdict)
        
    # Call an appropriate reading script, based on the file type.
    # Should probably have one test per filetype coded?
    ### Put these in a separate class below, to keep tidier
    
    # Read in the data that was requested in the JSON file
        
    def test_read_data(self):
        """
        Check that read_data returns a dictionary with the correct keys
        """
        self.ingest.metadata = eval(open(self.testmeta).read())
        self.ingest.read_data()
        self.assertEquals("longitude" in self.ingest.data.keys(), True)
        self.assertEquals("latitude" in self.ingest.data.keys(), True)
        for var in self.ingest.metadata['variables']:
            self.assertEquals(var in self.ingest.data.keys(), True)
    
    # Write out to a geotiff, with an appropriate directory structure
    def test_save_geotiff(self):
        """
        Check that geotiff file is created and saved to correct place
        """
        self.ingest.metadata = eval(open(self.testmeta).read())
        self.ingest.read_data()
        self.ingest.save_geotiff()
        self.assertEquals(os.path.isdir(
                          os.path.join(self.ingest.outdir, self.ingest.metadata['region_name'].upper(),
                                       self.ingest.metadata['instrument'].upper(),str(self.ingest.metadata['datetime'].year))),
                          True)

    def test_make_quicklook(self):
        """
        Test creation of jpeg quicklook
        """
        import datetime
        self.ingest.metadata = {'region_name': 'region',
                                'instrument': 'instrument',
                                'filename': 'test.hdf',
                                'variables': ('var1', 'var2', 'var3', 'longitude', 'latitude'),
                                'datetime': datetime.datetime(2000, 1, 1),
                                'wavelengths': [665.0, 560.0, 480.0],
                                }
        self.ingest.data = {}
        for var in self.ingest.metadata['variables']:
            self.ingest.data[var] = np.empty((2,2))
        outfile = os.path.join(self.ingest.outdir, 'REGION/INSTRUMENT/2000/test.jpg')

        with patch('ingest_data.ingest_images.plt.imshow') as mock1:
            with patch('ingest_data.ingest_images.plt.savefig') as mock2:
                self.ingest.make_quicklook()
        mock1.assert_called()
        mock2.assert_called_with(outfile)

    # Save an object to the database, storing the metadata and the location of the geotiff
class GeoToolsTests(InjestToolsSetup):

    def test_get_new_latlon(self):
        """
        Test calculation of new lat/lon coords in preparation for regridding and extracting
        """
        testlon = np.tile(np.arange(10),(10,1))
        testlat = np.tile(np.arange(10),(10,1)).T
        testregion = (4.5, 7.5, 3.5, 6.5)
        new_lon, new_lat = GeoTools.get_new_lat_lon(testlon, testlat, testregion)
        self.assertTrue(np.allclose(new_lon, [3.5, 5, 6.5]))
        self.assertTrue(np.allclose(new_lat, [4.5, 6, 7.5]))

    def test_regrid(self):
        """
        Test the regridding/extraction
        """
        old_lon = np.tile(np.arange(10),(10,1))
        old_lat = np.tile(np.arange(10),(10,1)).T
        new_lon = [4.5, 6, 7.5]
        new_lat = [3.5, 5, 6.5]
        data = GeoTools.extract_region_and_regrid(old_lon, old_lat, new_lon, new_lat, np.ones(old_lon.shape))
        self.assertEqual(data.shape,(len(new_lon), len(new_lat)))


class FiletypeTests(InjestToolsSetup):
    """Tests for the various file types, to check that the correct method is called for each one
    """
    def test_call_aatsr_read(self):
        """Check that read_n1 is called when instrument type is AATSR
        """
        self.ingest.metadata = {'instrument':'AATSR'}
        with patch('ingest_data.ingest_images.DataReaders.read_aatsr') as mock:
            self.ingest.read_data()
        mock.assert_called_with(self.ingest)

    def test_call_meris_read(self):
        """Check that read_n1 is called when instrument type is MERIS
        """
        self.ingest.metadata = {'instrument':'MERIS'}
        with patch('ingest_data.ingest_images.DataReaders.read_meris') as mock:
            self.ingest.read_data()
        mock.assert_called_with(self.ingest)

    def test_call_viirs_read(self):
        """Check that read_hdf is called when instrument type is VIIRS
        """
        self.ingest.metadata = {'instrument':'VIIRS'}
        with patch('ingest_data.ingest_images.DataReaders.read_viirs') as mock:
            self.ingest.read_data()
        mock.assert_called_with(self.ingest)

    def test_filetype_not_coded(self):
        """Check that IOError is thrown if user tries to ingest an instrument that we haven't coded in
        """
        self.ingest.metadata = {"instrument":"blahblahblah"}
        self.assertRaises(IOError, self.ingest.read_data)


class FunctionalTests(InjestToolsSetup):
    """Functional tests running the ingestion routines as the user will
    """
    def test_ingest_single_image(self):
        """Ingest all the images in the input directory
        """
        I = IngestImages(self.testdir, self.testdir+'../output')
        I.ingest_image(self.testmeta)

    def test_ingest_all_images(self):
        """Ingest a single image, from the specified metadata file
        """
        I = IngestImages(self.testdir, self.testdir+'../output')
        I.ingest_all()