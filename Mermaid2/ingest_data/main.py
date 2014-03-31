from os import environ, listdir
import sys
sys.path.append('/home/langlois/Documents/django/Mermaid2/Mermaid2')
#sys.path.append('/home/mermaid2/Mermaid2/Mermaid2')
environ['DJANGO_SETTINGS_MODULE'] = 'Mermaid2.settings'
from Mermaid2_db.models import *
from ingest import read_data
from datetime import datetime
import timeit

file_list = listdir('data')

instrument = Instrument.objects.get_or_create(name='Unknown')[0]

for file in file_list:

    print file
        
    file_data = open('data/' + file, 'r')

    tic = timeit.default_timer()

    read_data(file_data, instrument.id, file)

    toc = timeit.default_timer()
    
    print toc - tic

