"""Django views for Mermaid2 Database"""

from datetime import datetime
from Mermaid2_db.models import Deployment, Point, Instrument, Measurement, MeasurementType, InstrumentWavelength, Image     
from Mermaid2_db.forms import UploadForm, AddInstrumentForm, AddWavelengthForm, SearchMeasurementForm, SearchPointForm
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
import logging
import re
from django.core.urlresolvers import reverse
import requests
import json

logger = logging.getLogger(__name__)

def home(request):
    """Main page\n
    Simple html file
    """

    return render(request, 'Mermaid2_db/home.html')


def see_image(request):

    resp = requests.get(url='http://0.0.0.0:8000/api/v1/image/1/?format=json')

    data = json.loads(resp.text) 

    location = data['archive_location']

    return render(request, 'Mermaid2_db/see_image.html', locals())  
      

def add_image(request):

    Image(web_location='', archive_location='http://imageshack.us/a/img114/596/dscf4109bm2.jpg', top_left_point='POINT(12 45)', bot_right_point='POINT(13 46)', instrument=Instrument.objects.get(id=1)).save()
    
    return render(request, 'Mermaid2_db/home.html')
    
 
def search_point(request):

    if request.method == "POST":
        form = SearchPointForm(request.POST)
        if form.is_valid():
            top_left_lat = form.cleaned_data.get('top_left_lat')
            top_left_lon = form.cleaned_data.get('top_left_lon')
            bot_right_lat = form.cleaned_data.get('bot_right_lat')
            bot_right_lon = form.cleaned_data.get('bot_right_lon')
            
            url = get_point_url(top_left_lat, top_left_lon, bot_right_lat, bot_right_lon)  
            
            resp = requests.get(url=url)
            data = json.loads(resp.text) 
            objects = data['objects']
                       
            return render(request, 'Mermaid2_db/point_results.html', locals())

    else:
        form = SearchPointForm()    
            
    return render(request, 'Mermaid2_db/search_data.html', locals())    


def get_point_url(top_left_lat, top_left_lon, bot_right_lat, bot_right_lon): 
    url = 'http://0.0.0.0:8000/api/v1/point/?format=json&limit=0&point__within={"type":"MultiPolygon","coordinates":' + '[[[[{2},{1}],[{2},{3}],[{0},{3}],[{0},{1}],[{2},{1}]]]]'.format(top_left_lat, top_left_lon, bot_right_lat, bot_right_lon) + '}'
    
    return url     
    
   
def search_measurement(request):

    print 'ok'
    get_choices()
    
    if request.method == "POST":
        form = SearchMeasurementForm(request.POST)
        if form.is_valid():
            deployment = form.cleaned_data.get('deployment')
            measurement_type = form.cleaned_data.get('measurement_type')
            wavelengths = form.cleaned_data.get('wavelengths')
            url = get_measurement_url(deployment, measurement_type, wavelengths)
            resp = requests.get(url=url)
            data = json.loads(resp.text) 
            objects = data['objects']
                       
            return render(request, 'Mermaid2_db/measurement_results.html', locals())

    else:
        form = SearchMeasurementForm()    
            
    return render(request, 'Mermaid2_db/search_data.html', locals())
        

def get_choices():

    resp = requests.get(url='http://0.0.0.0:8000/api/v1/deployment/?format=json&limit=0')
    data = json.loads(resp.text)
    objects = data['objects']
    print objects
    
 

def get_measurement_url(deployment, measurement_type, wavelengths):
    url = 'http://0.0.0.0:8000/api/v1/measurement/?'
    
    if deployment != []:
        for dep in deployment:
            url += 'point__deployment__site__in=' + dep + '&'
    
    if measurement_type != []:
        for mes in measurement_type:
            url += 'measurementtype__type__in=' + mes + '&'
    
    if wavelengths != []:
        for wav in wavelengths:
            url += 'wavelength__in=' + wav + '&'
            
    url += 'format=json&limit=0'
    
    return url


def add_instrument(request): 
    """Add instrument page\n
    Uses the form AddInstrumentForm
    """

    # when the user sends a completed form
    if request.method == "POST":       
        form = AddInstrumentForm(request.POST)
        # get the values when it's valid
        if form.is_valid(): 
            instrument_name = form.cleaned_data.get('name')
            
            wavelengths = form.cleaned_data.get('wavelengths')
            # redirect to the wavelength form
            return HttpResponseRedirect(reverse('Mermaid2_db.views.add_wavelengths', args=[instrument_name, wavelengths]))
    # when the user access the page, create an empty form
    else:
        form = AddInstrumentForm()

    return render(request, 'Mermaid2_db/add_instrument.html', locals())


def add_wavelengths(request, instrument_name, wavelengths):
    """Add wavelengths page\n
    Uses the form AddWavelengthForm\n
    Follows the AddInstrumentForm
    """
    
    wavelengths = int(wavelengths) # value is unicode, cast it into integer
    # when the user sends a completed form
    if request.method == "POST":
        form = AddWavelengthForm(request.POST, num_wav=wavelengths)
        # create instrument instance when it's valid
        if form.is_valid():
            instrument = Instrument(name=instrument_name)
            instrument.save()
            # create instrumentwavelength instances linked to the instrument
            for wave in range(wavelengths):
                wavelength = form.cleaned_data.get('wavelength %d'%(wave+1))
                InstrumentWavelength(value=wavelength, instrument=instrument).save()
            # go home
            return HttpResponseRedirect(reverse('Mermaid2_db.views.home'))
    # when the user access the page, create an empty form
    else:
        form = AddWavelengthForm(num_wav=wavelengths)

    return render(request, 'Mermaid2_db/add_wavelength.html', locals())
     
            
def upload_data(request):
    """Upload data page\n
    Gets the data from a file posted by a user\n
    Uses the form UploadForm\n
    """

    save = False
    # when the user sends a completed form    
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        # read the file when the form is valid
        if form.is_valid():
            try:
                read_data(form.cleaned_data.get('data'), form.cleaned_data.get('name'))
                return HttpResponseRedirect(reverse('Mermaid2_db.views.home'))
            # if the file is incorrect, an IOError is raised 
            except IOError:
                print 'ERROR : bad file'
            else:
                print 'File OK'    
            save = True
    # when the user access the page, create an empty form
    else:
        form = UploadForm()
        
    return render(request, 'Mermaid2_db/upload_data.html', locals())
    
    
def read_data(file_data, instrument):
    """Fonction reading the file and uploading the data to the database
    """
    
    # create an array based on the file given
    data = read_file(file_data)
    
    # check if the file is legit
    if file_ok(data[0]) == False:
        raise IOError
    
    # create a deployment instance
    deployment = read_deployment_data(data[1])
    deployment.save()
    # create points and measurements linked to the deployment
    read_point_data(data, deployment, instrument)
    
    
def read_file(file_data):
    """Creates an array (actually a list of lists) based on the uploaded data
    """
    
    # create an empty list
    data = []
    
    # read the first line (list of values)
    line = file_data.readline().split(';')
    
    # add all lines to the list
    while line != ['']:
        line = map(lambda s: s.strip(), line) # erase the spaces in the value
        data.append(line) # add the line
        line = file_data.readline().split(';') # get the next line
   
    return data

     
def file_ok(line_1):
    """check if the file is legit\n
    to be modified
    """
    
    return(line_1[0].lower() == 'matchup_id' and
        line_1[1].lower() == 'site' and   
        line_1[2].lower() == 'pi' and  
        line_1[3].lower() == 'lat_is' and  
        line_1[4].lower() == 'lon_is' and  
        line_1[5].lower() == 'time_is' and  
        line_1[6].lower() == 'pqc' and  
        line_1[7].lower() == 'mqc' and  
        line_1[8].lower() == 'land_dist_is' and  
        (line_1[9].lower() == 'theta_s' or line_1[9].lower() == 'thetas_is'))
             

def read_deployment_data(data):
    """read the deployment data and create a deployment instance
    """

    deployment = Deployment()
    deployment.site = data[1]
    deployment.pi = data[2]
    return deployment

  
def read_point_data(data, deployment, instrument):
    """read the point data, create a point instance\n 
    read the measurement data and create measurement instances
    """
    
    # iterator for the lines
    comp = 1   
    
    # go through the whole document   
    while comp < len(data):
        #create point instance with the data
        point = Point()
        point.matchup_id = data[comp][0]
        point.point = 'POINT({0} {1})'.format(data[comp][3], data[comp][4])
        point.time_is = data[comp][5]
        point.pqc = data[comp][6]
        point.mqc = data[comp][7]
        point.land_dist_is = data[comp][8]
        point.thetas_is = data[comp][9]
        point.deployment = deployment
        point.save()
        # iterator for the columns
        comp2 = 10
        # go through all the measurements
        while comp2 < len(data[comp]):
            # checks if it's a simple or radiometric measurement
            if re.search(r"^.*_IS$", data[0][comp2]):
                Measurement(measurement_type=get_type(data[0][comp2], False), value=data[comp][comp2], point=point, instrument=Instrument.objects.get(id=instrument)).save() # create a measurement using the functions to extract the data
            elif re.search(r"^.*_IS_.*$", data[0][comp2]):
                Measurement(measurement_type=get_type(data[0][comp2], True), value=data[comp][comp2], wavelength=get_wavelength(data[0][comp2]), point=point, instrument=Instrument.objects.get(id=instrument)).save() # create a measurement using the functions to extract the data
            comp2 += 1
        comp += 1

   
def get_units(type):
    """Associate a measurement type with its units
    """

    if type.lower() == 'aeronet_chla_is':
        return 'mg.m-3'
    elif type.lower() == 'surf_press_is':
        return 'hPa'
    elif type.lower() == 'wind_speed_is':
        return 'm.s-1'
    elif type.lower() == 'o3_is':
        return 'cm-atm'
    elif type.lower() == 'rho_wn_is':
        return 'dl'
    elif type.lower() == 'lwn_is' or type.lower() == 'lw_is':
        return 'mW.m-2.nm-1.sr-1'
    elif type.lower() == 'exactwavelength_is':
        return 'nm'
    elif type.lower() == 'es_is' or type.lower() == 'ed_is':
        return 'mW.m-2.nm-1.s'
    elif type.lower() == 'thetav_is' or type.lower() == 'dphi_is':
        return 'degrees'
    elif type.lower() == 'lu_is':
        return 'uW.cm-2.nm.sr'
    elif type.lower() == 'a_is' or type.lower() == 'ap_is' or type.lower() == 'adet_is' or type.lower() == 'ag_is' or type.lower() == 'bb_is' or type.lower() == 'kd_is':
        return 'm-1'
    else:   
        return 'NA'    
   
   
def get_type(string, radiometric):
    """Read the measurement type\n
    If it doesn't exist, create it
    """
    
    type = ''
    # separate the type from the wavelength for a radiometric measurement
    if radiometric:
        for char in string:
            if not char.isdigit():
                type += char
        type = type[:-1]
    else:
        type = string 
    
    # get the right measurement corresponding to the type
    try:
        measurement_type = MeasurementType.objects.get(type=type)
    # if it doesn't exist, create it
    except MeasurementType.DoesNotExist:
        measurement_type = MeasurementType(type=type, units=get_units(type))
        measurement_type.save()       
       
    return measurement_type   
        
        
def get_wavelength(string):
    """Read the measurement wavelength
    """
    
    wavelength = ''
    for char in string:
        if char.isdigit() or char == '.': # read only digits or point
            wavelength += char
        
    wavelength = int(wavelength)    
        
    return wavelength      
    
    
    
    
    
