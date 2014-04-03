"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from ingest_data.ingest import *
import os

class InjestToolsTest(TestCase):

    def setUp(self):
        self.filename='extraction_Test_.csv'
        self.testfile = os.path.join('ingest_data', self.filename)
        self.sampleData = open(self.testfile, "r")
        self.instrument = Instrument.objects.get_or_create(name='Unknown')[0]
        
    def test_read_file(self):  
        """Check that read_data runs ok"""
        read_data(self.sampleData, self.instrument.id, self.filename)  
        
    def test_point_duplication(self):
        """Check that read_data prevents duplicate points being created"""
        read_data(self.sampleData, self.instrument.id, self.filename)  
        self.sampleData = open(self.testfile, "r") # Need to reopen the file
        read_data(self.sampleData, self.instrument.id, self.filename)  
        self.assertTrue(len(Point.objects.all())==1)  
        
    def test_deployment_duplication(self):
        """Check that read_data prevents duplicate deployments being created"""
        read_data(self.sampleData, self.instrument.id, self.filename)  
        self.sampleData = open(self.testfile, "r") # Need to reopen the file
        read_data(self.sampleData, self.instrument.id, self.filename)  
        self.assertTrue(len(Deployment.objects.all())==1)  
        
    def test_campaign_duplication(self):
        """Check that read_data prevents duplicate campaigns being created"""
        read_data(self.sampleData, self.instrument.id, self.filename)  
        self.sampleData = open(self.testfile, "r") # Need to reopen the file
        read_data(self.sampleData, self.instrument.id, self.filename)  
        self.assertTrue(len(Campaign.objects.all())==1)  
        
    def test_units_and_name(self):
        """Check that units_and_name returns the right format
        (a dictionary with keys 'units' and 'long_name', which both point to strings)
        """
        result = units_and_name('rho_w_IS')
        self.assertTrue( isinstance(result['units'], basestring) and isinstance(result['long_name'], basestring))
        