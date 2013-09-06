import re
from Mermaid2_db.models import *


def read_data(file_data, instrument, filename):
    """Function reading the file and uploading the data to the database\n
    :param file_data: file object to be read (file)
    :param instrument: id of the instrument used for the measurement (int)
    :param filename: name of the file, the name of the campaign is extracted form it (string)
    """

    # read the cvs file (turn the string into an array)
    data = read_file(file_data)

    # check if the file is legit
    if not file_ok(data[0]):
        raise IOError

    # create a campaign object and read the name of the campaign
    campaign = Campaign()
    campaign.campaign = read_campaign_name(filename)
    campaign.save()

    # create deployment object(s) linked to the campaign
    read_deployment_data(data, campaign, instrument)


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


def read_deployment_data(data, campaign, instrument):
    """Read the deployment data and create a deployment object\n
    :param data: array containing the data
    :param campaign: campaign object to be linked with the deployment(s) (Campaign model)
    :param instrument: database id of the instrument to be linked with the measurements (int)
    """

    # we assume (since the file has been considered legit) that the deployment elements are in columns 1 (site)
    #  and 2 (PI) of the array
    i = 1
    # read the file until the end
    while i < len(data):
        # for each line, get the deployment in the database
        try:
            deployment = Deployment.objects.get(site=data[i][1], pi=data[i][2], campaign=campaign)
        # if it does not exists, create it
        except Deployment.DoesNotExist:
            deployment = Deployment(site=data[i][1], pi=data[i][2], campaign=campaign)
            deployment.save()
            # then link the correct points to it
        read_point_data(data[i], deployment, instrument, data[0])
        i += 1


def read_point_data(data, deployment, instrument, header):
    """Read the point data, create point objects, read the measurement data and create measurement objects linked to \
     the point\n
    :param data: line of the array we read (array)
    :param deployment: deployment object to be linked with the points (Deployment model)
    :param instrument: database id of the instrument to be linked with the measurements (int)
    :param header: first line of the array containing the measurement types (array)
    """

    # we assume that the required elements are in the correct order   
    # one line in the csv file = one point (except header)
    # create the point object
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

    # then get all the measurement to be linked with this point

    # iterator for the columns
    i = 10
    # go through all the measurements
    while i < len(data):
        # checks if it's a simple or radiometric measurement
        if re.search(r"^.*_IS$", header[i]):  # all simple measurements must look like XXX_IS
            Measurement(measurement_type=get_type(header[i], False),
                        value=data[i],
                        point=point,
                        instrument=Instrument.objects.get(id=instrument)
                        ).save()  # create a measurement using the functions to extract the data
        elif re.search(r"^.*_IS_.*$", header[i]):  # all radiometric measurements must look like XXX_IS_YYY
            Measurement(measurement_type=get_type(header[i], True),
                        value=data[i],
                        wavelength=get_wavelength(header[i]),
                        point=point,
                        instrument=Instrument.objects.get(id=instrument)
                        ).save()  # create a measurement using the functions to extract the data
        i += 1


def get_units(type):
    """Associate a measurement type with its units, to be completed with new types\n
    :param type: measurement type (string)
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
        return 'NA'  # if the measurement type is unknown, set units to NA


def get_type(string, radiometric):
    """Read the measurement type from the string read, if it doesn't exist, create it\n
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
        measurement_type = MeasurementType.objects.get(type=type)
    # if it does not exist, create it
    except MeasurementType.DoesNotExist:
        measurement_type = MeasurementType(type=type, units=get_units(type))
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
