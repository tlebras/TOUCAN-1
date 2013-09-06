from os import environ, listdir
import sys
sys.path.append('/home/langlois/Documents/django/Mermaid2/Mermaid2')
#sys.path.append('/home/mermaid2/Mermaid2/Mermaid2')
environ['DJANGO_SETTINGS_MODULE'] = 'Mermaid2.settings'
from Mermaid2_db.models import *
from upload_ import read_data
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


#import os
#import sys
#sys.path.append('/path/to/the/directory/above/your/project')
#os.environ['DJANGO_SETTINGS_MODULE'] = 'yourproject.settings'
#from  yourproject.yourapp.models import YourModel

