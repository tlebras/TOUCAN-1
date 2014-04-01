from os import environ, listdir
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))
#sys.path.append('/home/mermaid2/Mermaid2/Mermaid2')
environ['DJANGO_SETTINGS_MODULE'] = 'Mermaid2.settings'
from Mermaid2_db.models import *
from ingest import read_data
from datetime import datetime

file_list = listdir('data')

instrument = Instrument.objects.get_or_create(name='Unknown')[0]

for file in file_list:

    print file
        
    file_data = open('data/' + file, 'r')

    time_1 = datetime.now()

    read_data(file_data, instrument.id, file)

    time_2 = datetime.now()
    
    print time_2 - time_1

