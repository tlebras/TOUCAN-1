from os import environ, listdir
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))
environ['DJANGO_SETTINGS_MODULE'] = 'toucan.settings'
from toucan_db.models import *
from ingest import read_data
from datetime import datetime
import timeit

file_list = listdir('data')

instrument = Instrument.objects.get_or_create(name='Unknown')[0]

for file in file_list:

    print file
        
    file_data = open(os.path.join('data', file), 'r')

    tic = timeit.default_timer()

    read_data(file_data, instrument.id, file)

    toc = timeit.default_timer()
    
    print toc - tic

