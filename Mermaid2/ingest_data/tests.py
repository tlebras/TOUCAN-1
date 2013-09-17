"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from ingest_data.ingest import *

class InjestToolsTest(TestCase):

    def setUp(self):
        self.sampleData = open("/home/mermaid2/mermaid2/Mermaid2/injest_data/extraction_Test_.csv", "r")
        self.instrument = Instrument.objects.get_or_create(name='Unknown')[0]
        
    def test_read_file(self):    
        read_data(self.sampleData, self.instrument.id, "extraction_Test_.csv")  
        
