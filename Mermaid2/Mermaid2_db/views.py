"""Django views for Mermaid2 Database"""

from datetime import datetime
from Mermaid2_db.models import *
from Mermaid2_db.forms import UploadForm, AddInstrumentForm, AddWavelengthForm, SearchMeasurementForm, SearchPointForm
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
    Simple html file
    """

    return render(request, 'Mermaid2_db/home.html')


def see_image(request):
    resp = requests.get(url='http://0.0.0.0:8000/api/v1/image/1/?format=json')

    data = json.loads(resp.text)

    location = data['archive_location']

    return render(request, 'Mermaid2_db/see_image.html', locals())


def add_image(request):
    Image(web_location='', archive_location='http://imageshack.us/a/img114/596/dscf4109bm2.jpg',
          top_left_point='POINT(12 45)', bot_right_point='POINT(13 46)', instrument=Instrument.objects.get(id=1)).save()

    return render(request, 'Mermaid2_db/home.html')


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
    temp_choices2 = []
    resp = requests.get(url='http://0.0.0.0:8000/api/v1/measurement/?format=json')
    data = json.loads(resp.text)
    objects = data['objects']

    for measurement in objects:
        temp_choices.append(measurement['wavelength'])
    temp_choices = sorted(list(set(temp_choices)))

    for wavelength in temp_choices:
        temp_choices2.append(wavelength)
        temp_choices2.append(wavelength)
        wavelengths_choices.append(temp_choices2)
        temp_choices2 = []
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
            time_1 = datetime.datetime.now()
            try:
                # get the name of the file
                for filename, file in request.FILES.iteritems():
                    name = request.FILES[filename].name
                    # read the file
                read_data(form.cleaned_data.get('data'), form.cleaned_data.get('name'), name)
                # go back home
                time_2 = datetime.datetime.now()
                print time_2 - time_1
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


def read_data(file_data, instrument, filename):
    """Function reading the file and uploading the data to the database
    :param file_data:
    :param instrument:
    :param filename:
    """

    # create an array based on the file given
    data = read_file(file_data)

    # check if the file is legit
    if not file_ok(data[0]):
        raise IOError

    # create a campaign object and read the name of the campaign
    campaign = Campaign()
    campaign.campaign = read_campaign_name(filename)
    campaign.save()

    # create a deployment instance
    read_deployment_data(data, campaign, instrument)

    # create points and measurements linked to the deployment
    #read_point_data(data, deployment, instrument)


def read_file(file_data):
    """Creates an array (actually a list of lists) based on the uploaded data
    :param file_data:
    """

    # create an empty list
    data = []

    # read the first line (list of values)
    line = file_data.readline().split(';')

    # add all lines to the list
    while line != ['']:
        line = map(lambda s: s.strip(), line)  # erase the spaces in the value
        if line[-1] == '':
            line = line[:-1]
        data.append(line)  # add the line
        line = file_data.readline().split(';')  # get the next line

    return data


def file_ok(line_1):
    """check if the file is legit\n
    to be modified
    :param line_1:
    """

    return (line_1[0].lower() == 'matchup_id' and
            line_1[1].lower() == 'site' and
            line_1[2].lower() == 'pi' and
            line_1[3].lower() == 'lat_is' and
            line_1[4].lower() == 'lon_is' and
            line_1[5].lower() == 'time_is' and
            line_1[6].lower() == 'pqc' and
            line_1[7].lower() == 'mqc' and
            line_1[8].lower() == 'land_dist_is' and
            (line_1[9].lower() == 'theta_s' or line_1[9].lower() == 'thetas_is'))


def read_campaign_name(filename):
    """

    :param filename:
    :return:
    """
    campaign_name = ''

    i = 11

    while filename[i] != '_':
        campaign_name += filename[i]
        i += 1

    return campaign_name


def read_deployment_data(data, campaign, instrument):
    """read the deployment data and create a deployment instance
    :param data:
    :param campaign:
    :param instrument:
    """

    i = 1
    while i < len(data):
        try:
            deployment = Deployment.objects.get(site=data[i][1], pi=data[i][2], campaign=campaign)
        except Deployment.DoesNotExist:
            deployment = Deployment(site=data[i][1], pi=data[i][2], campaign=campaign)
            deployment.save()

        read_point_data(data[i], deployment, instrument, data[0])
        i += 1


def read_point_data(data, deployment, instrument, header):
    """read the point data, create a point instance\n 
    read the measurement data and create measurement instances
    :param data:
    :param deployment:
    :param instrument:
    :param header:
    """

    point = Point()
    point.matchup_id = data[0]
    point.point = 'POINT({0} {1})'.format(data[3], data[4])
    point.time_is = data[5]
    point.pqc = data[6]
    point.mqc = data[7]
    point.land_dist_is = data[8]
    point.thetas_is = data[9]
    point.deployment = deployment
    point.save()

    # iterator for the columns
    i = 10
    # go through all the measurements
    while i < len(data):
        # checks if it's a simple or radiometric measurement
        if re.search(r"^.*_IS$", header[i]):
            Measurement(measurement_type=get_type(header[i], False), value=data[i], point=point,
                        instrument=Instrument.objects.get(
                            id=instrument)).save() # create a measurement using the functions to extract the data
        elif re.search(r"^.*_IS_.*$", header[i]):
            Measurement(measurement_type=get_type(header[i], True), value=data[i], wavelength=get_wavelength(header[i]),
                        point=point, instrument=Instrument.objects.get(
                    id=instrument)).save() # create a measurement using the functions to extract the data
        i += 1


def get_units(type):
    """Associate a measurement type with its units
    :param type:
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
    elif type.lower() == 'a_is' or type.lower() == 'ap_is' or type.lower() == 'adet_is' or type.lower() == 'ag_is' \
        or type.lower() == 'bb_is' or type.lower() == 'kd_is':
        return 'm-1'
    else:
        return 'NA'


def get_type(string, radiometric):
    """Read the measurement type\n
    If it doesn't exist, create it
    :param string:
    :param radiometric:
    """

    type = ''
    # separate the type from the wavelength for a radiometric measurement
    if radiometric:
        for char in string:
            if not char.isdigit() and char != '.':
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
    :param string:
    """

    wavelength = ''
    for char in string:
        if char.isdigit() or char == '.':  # read only digits or point
            wavelength += char

    wavelength = float(wavelength)

    try:
        measurement_wavelength = MeasurementWavelength.objects.get(wavelength=wavelength)
    except MeasurementWavelength.DoesNotExist:
        measurement_wavelength = MeasurementWavelength(wavelength=wavelength)
        measurement_wavelength.save()

    return measurement_wavelength
