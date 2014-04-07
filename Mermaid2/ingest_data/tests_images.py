from django.test import TestCase
from ingest_data.ingest_images import *
import os
from mock import MagicMock

class InjestToolsTest(TestCase):

    def setUp(self):
        self.testdir = "ingest_data/images/"
        self.testdata = os.path.join(self.testdir,'input/',"NPP_VMAE_L1.A2013302.1140.P1_03001.2013302210836.gscs_000500784042.hdf")
        self.testmeta = os.path.join(self.testdir,'input/',"test.json")
        self.ingest = ingest_images()
    
    # Program checks to see if there's any new images in the staging area
    
    # List the files and their associated metadata document (eg a JSON file)
    def test_list_files(self):
        """Check that get_file_list returns the correct file lists
        """
        metafiles = self.ingest.get_file_list(self.testdir+'/input')
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
    def test_call_hdf_read(self):
        """Check that read_hdf is called when filetype=="hdf"
        """
        self.ingest.read_hdf = MagicMock(return_value=3)
        metadata = {"filetype":"hdf"}
        self.ingest.read_data(metadata)
        self.ingest.read_hdf.assert_called_with(metadata)
    
    def test_filetype_not_coded(self):
        """Check that IOError is thrown if user tries to ingest a filetype that
        we haven't coded in
        """
        metadata = {"filetype":"blahblahblah"}
        self.assertRaises(IOError, self.ingest.read_data, metadata)       
    
    
    # Read in the data that was requested in the JSON file
        
    # Extract a subset containing our region of interest
    
    # Write out to a geotiff, with an appropriate directory structure
    
    # Save an object to the database, storing the metadata and the location of the geotiff
 