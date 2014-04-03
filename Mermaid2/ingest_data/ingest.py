import re
from Mermaid2_db.models import *
import datetime
import pytz

def read_data(file_data, instrument, filename):
    """Function reading the file and uploading the data to the database\n
    :param file_data: file object to be read (file)
    :param instrument: id of the instrument used for the measurement (int)
    :param filename: name of the file, the name of the campaign is extracted form it (string)
    """

    # Read the cvs file (turn the string into an array)
    data = read_file(file_data)

    # Check if the file is legit
    if not file_ok(data[0]):
        raise IOError

    # Create new, or get matching, campaign object
    campaign = get_campaign(filename)
    
    # Create list of measurements, which will then all be saved in one go at the end
    measurements_to_bulk_save = []

    i = 1
    j = 10 # The first measurement column (after all the Point metadata ones)
    header = data[0]

    # Loop over all the rows in the file
    while i < len(data):
        deployment = get_deployment(site=data[i][1], pi=data[i][2], campaign=campaign)
        point_id = get_point(data[i][:j], deployment.id)

        # Loop through all the measurement columns on this row
        while j < len(data[i]):
            if re.search(r"^.*_IS$", header[j]):  # all simple measurements must look like XXX_IS
                measurement = Measurement(measurement_type=get_type(header[j], False),
                                          value=data[i][j],
                                          point=Point(id=point_id),
                                          instrument=Instrument(id=instrument)
                                          )  # create a measurement using the functions to extract the data
            elif re.search(r"^.*_IS_.*$", header[j]):  # all radiometric measurements must look like XXX_IS_YYY
                measurement = Measurement(measurement_type=get_type(header[j], True),
                                          value=data[i][j],
                                          wavelength=get_wavelength(header[j]),
                                          point=Point(id=point_id),
                                          instrument=Instrument(id=instrument)
                                          )  # create a measurement using the functions to extract the data

            measurements_to_bulk_save.append(measurement)
            j += 1

        i += 1
        j = 10

    # save all the measurements into the database
    Measurement.objects.bulk_create(measurements_to_bulk_save)


def read_file(file_data):
    """Creates an array (actually a list of lists) based on the uploaded data\n
    :param file_data: file object to be read (file)
    """

    # create an empty list to store the data
    data = []

    # read the first line, values are separated by a semicolon
    line = file_data.readline().split(';')

    # add all lines to the list
    while line != ['']:
        line = map(lambda s: s.strip(), line)  # erase the blanks in the string
        if line[-1] == '':  # fixes a bug for one file (NOMAD) where there is an extra semicolon at the end of each line
            line = line[:-1]
        data.append(line)  # add the line to the array
        line = file_data.readline().split(';')  # get the next line

    return data


def file_ok(line_1):
    """check if the file is legit\n
    to be modified, this function is not enough to check the integrity of the file given\n
    :param line_1: first line of the csv file, only the header is checked (array)
    """

    # only check performed : the first ten elements must match the following :
    return (line_1[0].lower() == 'matchup_id' and
            line_1[1].lower() == 'site' and
            line_1[2].lower() == 'pi' and
            line_1[3].lower() == 'lat_is' and
            line_1[4].lower() == 'lon_is' and
            line_1[5].lower() == 'time_is' and
            line_1[6].lower() == 'pqc' and
            line_1[7].lower() == 'mqc' and
            line_1[8].lower() == 'land_dist_is' and
            (line_1[9].lower() == 'theta_s' or line_1[
                9].lower() == 'thetas_is'))  # found two different values in the csv files


def read_campaign_name(filename):
    """
    Get the name of the campaign from the name of the file (this function may should be rewritten or completed)\n
    :param filename: name of the file (string)
    """
    # we assume that the name of the file begins with "extraction_XXXXX_"
    # XXXXX being the name of the campaign

    # string containing the name of the campaign
    campaign_name = ''

    # the first letter is the eleventh
    i = 11

    # read the name of the file
    # stop reading when underscore is found
    while filename[i] != '_':
        campaign_name += filename[i]  # add the character the the campaign name
        i += 1

    return campaign_name

def get_campaign(filename):
    """
    Get the campaign name, and check to see if we already have this campaign in the database
    If we don't: Create it
    If we do: Return this campaign
    
    :param filename: Name of the file, which contains the campaign name
    
    :return campaign: the campaign object found or created
    
    """
    campaign_name = read_campaign_name(filename)
    campaign = Campaign.objects.get_or_create(campaign=campaign_name)[0]
    return campaign        

def get_deployment(site, pi, campaign):
    """
    Check to see if we already have this campaign in the database
    If we don't: Create it
    If we do: Return this campaign
    
    :param site: Name of the deployment site
    :param pi: Name of the PI
    :param campaign: Campaign object this deployment is attached to
    
    :return deployment: the Deployment object found or created
    
    """
    deployment = Deployment.objects.get_or_create(site=site, pi=pi, campaign=campaign)[0]       
    return deployment
 
def get_point(data, dep_id):
    """
    Check to see if the current point has already been created. If so, return the point id. If not, create a new point.
    To be regarded as the same point, ALL of the model's fields (matchup_id, point, time_is, etc) must be the same.
    
    :param data: Data array containing the 10 field values
    :param dep_id:   Id number of the deployment this point is attached to
    
    :return point_id: the point id of either the point that was found, or the new one created
    """
    matchup_id = data[0]
    point = 'POINT({0} {1})'.format(data[3], data[4])
    time_is = datetime.datetime.strptime(data[5],'%Y%m%dT%H%M%SZ').replace(tzinfo=pytz.utc)
    pqc = data[6]
    mqc = data[7]
    land_dist_is = data[8]
    thetas_is = data[9]
    deployment = Deployment.objects.get(id=dep_id)
        
    thispoint = Point.objects.get_or_create(matchup_id=matchup_id, point=point, time_is=time_is, pqc=pqc, mqc=mqc,
                          land_dist_is=land_dist_is, thetas_is=thetas_is, deployment=deployment)[0]
    point_id = thispoint.id

    return point_id


def units_and_name(type):
    """Using a dictionary, return the units and long name associate with a measurement type
    :param type: measurement type (string), as taken from the input spreadsheet headings
    
    Returns a dictionary with keys "units" and "long_name"
    If the input type isn't coded, sets units = "NA" and long name = type
    """
    types={ 
            'a_is': ('m-1', 'Total absorption coefficient'),
            'adet_is': ('m-1', 'Detrital (non-algal) absorption coefficient'),
            'aeronet_chla_is': ('mg.m-3', 'Chlorophyll-a (from AERONET)'),
            'ag_is': ('m-1', 'In-situ CDOM'),
            'alpha_nir_is': ('dl', 'AERONET aerosol Angstrom exponents'),
            'aot_is': ('dl', 'AERONET aerosol optical thickness as band b'),
            'ap_is': ('m-1', 'Total particulate absorption'),
            'aph_is': ('m-1', 'Total algal pigment absorption'),
            'bb_is': ('m-1', 'Total backscattering'),
            'dphi_is': ('degrees', 'Viewing azimuth angle'),
            'ed_is': ('mW.m-2.nm-1.s', 'Downwelling surface irradiance'),
            'es_is': ('mW.m-2.nm-1.s', 'Spectral surface irradiance'),
            'exactwavelength_is': ('nm', 'Exact wavelength of Lwn of named spectral band'),
            'hplc_chla_total_is': ('mg.m-3', 'Chlorophyll-a (total from HPLC pigment analysis)'),
            'kd_is': ('m-1', 'Diffuse attenuation coefficient for backscattering'),       
            'lu_is': ('uW.cm-2.nm.sr', 'Upwelling radiance'),
            'lw_is': ('mW.m-2.nm-1.sr-1', 'Water-leaving radiance'),
            'lwn_is': ('mW.m-2.nm-1.sr-1', 'Water-leaving radiance (normalised)'),
            'msm_is': ('g,m3', 'Mineral suspended matter'),
            'o3_is': ('cm-atm', 'Ozone concentration'),
            'osm_is': ('g.m3', 'Organic suspended matter'),
            'rho_w_is': ('dl', 'Water reflectance (unnormalised)'),
            'rho_wn_is': ('dl', 'Water reflectance (normalised)'),
            'surf_press_is': ('hPa', 'Surface pressure'),
            'spect_chla_is': ('mg.m-3', 'Chlorophyll-a (spectrophotometric)'),
            'thetav_is': ('degrees', 'Viewing zenith angle'),
            'time_is': ('UTC', 'AERONET measurement time'),
            'tsm_is': ('g.m3', 'Total suspended matter (mineral + organic)'),
            'wind_speed_is': ('m.s-1', 'Wind speed'),
    }
    
    try:
        return {'units':types[type.lower()][0], 'long_name':types[type.lower()][1]}
    except KeyError:
        return {'units':'NA', 'long_name': type.lower()}

def get_type(string, radiometric):
    """Read the measurement type from the string read, if it doesn't exist, create it\n
    Force the type to be lower case, so that we don't get duplicates with just differences in case
    :param string: string containing the measurement type, i.e. in "Rho_wn_IS_412" the type is "Rho_wn_IS"
    :param radiometric: boolean, true if the measurement is radiometric, meaning the string contains the wavelength
    """

    type = ''
    # separate the type from the wavelength for a radiometric measurement
    if radiometric:
        for char in string:  # read all the characters in the string
            if not char.isdigit() and char != '.':  # if the character if a digit or a point, it is considered part
            #  of the wavelength
            # (may be modified)
                type += char
        type = type[:-1]  # delete the underscore at the end of the string
    # 
    else:
        type = string

    # get the right measurement type object from the database
    try:
        measurement_type = MeasurementType.objects.get(type=type.lower())
    # if it does not exist, create it
    except MeasurementType.DoesNotExist:
        measurement_type = MeasurementType(type=type.lower(), units=units_and_name(type)['units'],
                                           long_name=units_and_name(type)['long_name'])
        measurement_type.save()

    return measurement_type


def get_wavelength(string):
    """Read the measurement wavelength from the string, if it doesn't exist, create it\n
    :param string: string containing the wavelength, i.e. in "Rho_wn_IS_412" the type is "412"
    """

    wavelength = ''
    for char in string:
        if char.isdigit() or char == '.':  # if the character if a digit or a point, it is considered part of
        # the wavelength
        # (may be modified)
            wavelength += char

    # convert the string to float
    wavelength = float(wavelength)

    # get the right wavelength object from the database
    try:
        measurement_wavelength = MeasurementWavelength.objects.get(wavelength=wavelength)
    except MeasurementWavelength.DoesNotExist:
    # if it does not exist, create it
        measurement_wavelength = MeasurementWavelength(wavelength=wavelength)
        measurement_wavelength.save()

    return measurement_wavelength
