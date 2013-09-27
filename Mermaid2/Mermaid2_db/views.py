"""Django views for Mermaid2 Database"""

from datetime import datetime
from Mermaid2_db.models import *
from Mermaid2_db.forms import UploadForm, AddInstrumentForm, AddWavelengthForm, SearchMeasurementForm, SearchPointForm
from ingest_data.ingest import read_data as read_data_2
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
import logging
import re
from django.core.urlresolvers import reverse
import requests
import json
import datetime

#logger = logging.getLogger(__name__)


def home(request):
    """Main page\n
    Simple html file\n
    :param request:
    """

    return render(request, 'Mermaid2_db/home.html')


#def see_image(request):
#    """
#
#    :param request:
#    :return:
#    """
#    resp = requests.get(url='http://0.0.0.0:8000/api/v1/image/1/?format=json')
#
#    data = json.loads(resp.text)
#
#    location = data['archive_location']
#
#    return render(request, 'Mermaid2_db/see_image.html', locals())


#def add_image(request):
#    """
#
#    :param request:
#    :return:
#    """
#    Image(web_location='', archive_location='http://imageshack.us/a/img114/596/dscf4109bm2.jpg',
#         top_left_point='POINT(12 45)', bot_right_point='POINT(13 46)', instrument=Instrument.objects.get(id=1)).save()
#
#    return render(request, 'Mermaid2_db/home.html')


def search_point(request):
    """

    :param request:
    :return:
    """
    if request.method == "POST":
        form = SearchPointForm(request.POST)
        if form.is_valid():
            # get the lat/long from the form
            top_left_lat = form.cleaned_data.get('top_left_lat')
            top_left_lon = form.cleaned_data.get('top_left_lon')
            bot_right_lat = form.cleaned_data.get('bot_right_lat')
            bot_right_lon = form.cleaned_data.get('bot_right_lon')
            # get the url corresponding to the lat/long
            url = get_point_url(top_left_lat, top_left_lon, bot_right_lat, bot_right_lon)
            # request the api
            resp = requests.get(url=url)
            # read the data
            data = json.loads(resp.text)
            objects = data['objects']
            # load the template
            return render(request, 'Mermaid2_db/point_results.html', locals())

    else:
        form = SearchPointForm()

    return render(request, 'Mermaid2_db/search_data.html', locals())


def get_point_url(top_left_lat, top_left_lon, bot_right_lat, bot_right_lon):
    """
    Get the right url for the selected lat/long
    :param top_left_lat:
    :param top_left_lon:
    :param bot_right_lat:
    :param bot_right_lon:
    :return:
    """
    url = 'http://0.0.0.0:8000/api/v1/point/?format=json&point__within={"type":"MultiPolygon","coordinates":' + \
          '[[[[{2},{1}],[{2},{3}],[{0},{3}],[{0},{1}],[{2},{1}]]]]'.format(top_left_lat, top_left_lon, bot_right_lat,
                                                                           bot_right_lon) + '}'

    return url


def search_measurement(request):
    """

    :param request:
    :return:
    """
    d_choices = get_deployment_choices()
    m_choices = get_measurement_type_choices()
    w_choices = get_wavelengths_choices()

    if request.method == "POST":
        form = SearchMeasurementForm(request.POST, deployment_choices=d_choices, measurement_type_choices=m_choices,
                                     wavelengths_choices=w_choices)
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
        form = SearchMeasurementForm(deployment_choices=d_choices, measurement_type_choices=m_choices,
                                     wavelengths_choices=w_choices)

    return render(request, 'Mermaid2_db/search_data.html', locals())


def get_deployment_choices():
    """


    :return:
    """
    deployment_choices = []
    temp_choices = []
    resp = requests.get(url='http://0.0.0.0:8000/api/v1/deployment/?format=json')
    data = json.loads(resp.text)
    objects = data['objects']

    for deployment in objects:
        temp_choices.append(deployment['site'])
        temp_choices.append(deployment['site'])
        deployment_choices.append(temp_choices)
        temp_choices = []
    return deployment_choices


def get_measurement_type_choices():
    """


    :return:
    """
    measurement_type_choices = []
    temp_choices = []
    resp = requests.get(url='http://0.0.0.0:8000/api/v1/measurementtype/?format=json')
    data = json.loads(resp.text)
    objects = data['objects']

    for measurementtype in objects:
        temp_choices.append(measurementtype['type'])
        temp_choices.append(measurementtype['type'])
        measurement_type_choices.append(temp_choices)
        temp_choices = []
        
    return measurement_type_choices


def get_wavelengths_choices():
    """


    :return:
    """
    wavelengths_choices = []
    temp_choices = []
    resp = requests.get(url='http://0.0.0.0:8000/api/v1/measurementwavelength/?format=json')
    data = json.loads(resp.text)
    objects = data['objects']

    for wavelength in objects:
        temp_choices.append(wavelength['wavelength'])
        temp_choices.append(wavelength['wavelength'])
        wavelengths_choices.append(temp_choices)
        temp_choices = []

    return wavelengths_choices


def get_measurement_url(deployment, measurement_type, wavelengths):
    """

    :param deployment:
    :param measurement_type:
    :param wavelengths:
    :return:
    """
    url = 'http://0.0.0.0:8000/api/v1/measurement/?'

    if deployment:
        for dep in deployment:
            url += 'point__deployment__site__in=' + dep + '&'

    if measurement_type:
        for mes in measurement_type:
            url += 'measurementtype__type__in=' + mes + '&'

    if wavelengths:
        for wav in wavelengths:
            url += 'wavelength__in=' + wav + '&'

    url += 'format=json'

    return url


def add_instrument(request):
    """Add instrument page\n
    Uses the form AddInstrumentForm
    :param request:
    """

    # when the user sends a completed form
    if request.method == "POST":
        form = AddInstrumentForm(request.POST)
        # get the values when it's valid
        if form.is_valid():
            instrument_name = form.cleaned_data.get('name')

            wavelengths = form.cleaned_data.get('wavelengths')
            # redirect to the wavelength form
            return HttpResponseRedirect(
                reverse('Mermaid2_db.views.add_wavelengths', args=[instrument_name, wavelengths]))
    # when the user access the page, create an empty form
    else:
        form = AddInstrumentForm()

    return render(request, 'Mermaid2_db/add_instrument.html', locals())


def add_wavelengths(request, instrument_name, wavelengths):
    """Add wavelengths page\n
    Uses the form AddWavelengthForm\n
    Follows the AddInstrumentForm
    :param request:
    :param instrument_name:
    :param wavelengths:
    """

    wavelengths = int(wavelengths)  # value is unicode, cast it into integer
    # when the user sends a completed form
    if request.method == "POST":
        form = AddWavelengthForm(request.POST, num_wav=wavelengths)
        # create instrument instance when it's valid
        if form.is_valid():
            instrument = Instrument(name=instrument_name)
            instrument.save()
            # create instrumentwavelength instances linked to the instrument
            for wave in range(wavelengths):
                wavelength = form.cleaned_data.get('wavelength %d' % (wave + 1))
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
    :param request:
    """

    save = False
    # when the user sends a completed form    
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        # read the file when the form is valid
        if form.is_valid():
            try:
                # get the name of the file
                for filename, file in request.FILES.iteritems():
                    name = request.FILES[filename].name
                    # read the file using the ingestion script in the ingest_data directory
                read_data_2(form.cleaned_data.get('data'), form.cleaned_data.get('name'), name)
                # go back home
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

