import sys, os
sys.path.append('/home/langlois/Documents/django/Mermaid2/Mermaid2')
os.environ['DJANGO_SETTINGS_MODULE'] = 'Mermaid2.settings'
from Mermaid2_db.models import *
from upload import *
from unittest import TestCase
#from django.test import TestCase

class UploadToolsTest(TestCase):

    def setUp(self):
        self.sampleData = open("extraction_Test_.csv", "r")
        self.instrument = Instrument.objects.get_or_create(name='Unknown')[0]
                        
    def test_read_file(self):    
        read_data(self.sampleData, self.instrument.id, "extraction_Test_.csv")  
    
#if __name__ == '__main__':
    #unittest.main()
    
