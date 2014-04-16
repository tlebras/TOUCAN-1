import os
from mock import *

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
        self.testmeta = os.path.join(self.testdir,"test.json")
        self.ingest = IngestImages()
        self.ingest.inputdir = self.testdir
    
class InjestToolsTest(InjestToolsSetup):
    # Program checks to see if there's any new images in the staging area
    
    # List the files and their associated metadata document (eg a JSON file)
    def test_list_files(self):
        """Check that get_file_list returns the correct file list
        """
        metafiles = self.ingest.get_file_list()
        self.assertEquals(len(metafiles),1)
            
    # Extract data from the JSON file
    # File type (hdf etc), coordinates of ROI, the variables to pull out, the bands
    def test_metafile_read(self):
        """Check that read_meta_file returns a dictionary with the correct values
        """
        testdict = eval(open(self.testmeta).read()) # Read json file directly as a python dictionary
        metadata = self.ingest.read_meta_file(self.testmeta)
        self.assertDictEqual(metadata, testdict)
        
    # Call an appropriate reading script, based on the file type.
    # Should probably have one test per filetype coded?
    ### Put these in a separate class below, to keep tidier
    
    # Read in the data that was requested in the JSON file
        
    def test_read_data(self):
        """
        Check that read_data returns a dictionary with the correct keys
        """
        metadata = self.ingest.read_meta_file(self.testmeta)
        data = self.ingest.read_data(metadata)
        self.assertEquals("longitude" in data.keys(), True)
        self.assertEquals("latitude" in data.keys(), True)
        for var in metadata['variables']:
            self.assertEquals(var in data.keys(), True)
    
    # Write out to a geotiff, with an appropriate directory structure
    def test_save_geotiff(self):
        """
        Check that geotiff file is created and saved to correct place
        """
        metadata = self.ingest.read_meta_file(self.testmeta)
        testdata = self.ingest.read_data(metadata)
        testoutdir = self.testdir+'../output'
        
        self.ingest.save_geotiff(str(testoutdir), metadata, testdata)
        self.assertEquals(os.path.isdir(os.path.join(testoutdir, metadata['region_name'],
                                                     metadata['instrument'], str(metadata['datetime'].year))), True)
    
    # Save an object to the database, storing the metadata and the location of the geotiff
class GeoToolsTests(InjestToolsSetup):
        
    def test_get_new_latlon(self):
        """
        Test calculation of new lat/lon coords in preparation for regridding and extracting
        """
        testlon = np.tile(np.arange(10),(10,1))
        testlat = np.tile(np.arange(10),(10,1)).T
        testregion = (4.5,7.5,3.5,6.5)
        G = GeoTools()
        new_lon, new_lat = G.get_new_lat_lon(testlon, testlat, testregion)
        self.assertTrue(np.allclose(new_lon, [3.5,5,6.5]))
        self.assertTrue(np.allclose(new_lat, [4.5,6,7.5]))
        
    def test_regrid(self):
        """
        Test the regridding/extraction
        """
        old_lon = np.tile(np.arange(10),(10,1))
        old_lat = np.tile(np.arange(10),(10,1)).T
        new_lon = [4.5,6,7.5]
        new_lat = [3.5,5,6.5]
        G = GeoTools()
        data = G.extract_region_and_regrid(old_lon, old_lat, new_lon, new_lat, np.ones(old_lon.shape))
        self.assertEqual(data.shape,(len(new_lon), len(new_lat)))
        
    def test_get_region(self):
        """
        Test extracting the region of interest, as given by lon/lat corners
        """
        testlon = np.array([[1,2,3],[1.2,2.2,3.2],[1.3,2.3,3.3]])
        testlat = np.array([[11,11.3,11.4],[12, 12.3, 12.4],[13,13.3,13.4]])
        testregion = [11.1, 12.5, 1.5, 3.1]
        G = GeoTools()
        i,j = G.extract_region(testlon, testlat, testregion)
        self.assertEquals(i,slice(0,2))
        self.assertEquals(j,slice(1,3))
    
class FiletypeTests(InjestToolsSetup):
    """Tests for the various file types, to check that the correct method is called for each one
    """
    def test_call_aatsr_read(self):
        """Check that read_n1 is called when instrument type is AATSR
        """
        metadata = {'instrument':'AATSR'}
        with patch('ingest_data.ingest_images.DataReaders.read_n1') as mock:
            self.ingest.read_data(metadata)
        mock.assert_called_with(self.ingest.inputdir,metadata)
        
    def test_call_meris_read(self):
        """Check that read_n1 is called when instrument type is MERIS
        """
        metadata = {'instrument':'MERIS'}
        with patch('ingest_data.ingest_images.DataReaders.read_n1') as mock:
            self.ingest.read_data(metadata)
        mock.assert_called_with(self.ingest.inputdir,metadata)
        
    def test_call_viirs_read(self):
        """Check that read_hdf is called when instrument type is VIIRS
        """
        metadata = {'instrument':'VIIRS'}
        with patch('ingest_data.ingest_images.DataReaders.read_hdf_pyhdf') as mock:
            self.ingest.read_data(metadata)
        mock.assert_called_with(self.ingest.inputdir,metadata )
        
    def test_filetype_not_coded(self):
        """Check that IOError is thrown if user tries to ingest an instrument that we haven't coded in
        """
        metadata = {"instrument":"blahblahblah"}
        self.assertRaises(IOError, self.ingest.read_data, metadata)
        
class FunctionalTests(InjestToolsSetup):
    """Functional test running the whole ingestion routine as the user will do it
    """
    def test_ingest_image(self):
        self.ingest.ingest_images(self.testdir, self.testdir+'../output')