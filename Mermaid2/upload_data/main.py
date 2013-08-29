from os import environ, listdir
import sys
sys.path.append('/home/langlois/Documents/django/Mermaid2/Mermaid2_')
environ['DJANGO_SETTINGS_MODULE'] = 'Mermaid2.settings'
from Mermaid2_db.models import *
from upload import read_data
from datetime import datetime

#file_list = listdir('data')
#print file_list

# make arrays using csv reader.

#for file in file_list:  


instrument = Instrument.objects.get_or_create(name='Unknown')[0]

file = 'extraction_LISCO_step1_rhow_FULLDATASET.csv'  
  
file_data = open('data/' + file, 'r')

print type(file_data)

time_1 = datetime.now()

#read_data(file_data, instrument.id, file)

time_2 = datetime.now()
print time_2 - time_1
