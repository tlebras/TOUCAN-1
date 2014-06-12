import requests

class Querydb(object):
    """
    Perform queries on the TOUCAN database
    """

    def __init__(self):
        pass

    @staticmethod
    def get(url, params):
        """
        Do GET request and return objects
        
        :param url: The base URL for the query
        :param params: Dictionary of search parameters, format search_parameter:value
        :returns: JSON objects returned by the query
        """
        r = requests.get(url, params=params)
        # Raise error if status not ok
        r.raise_for_status()
        return r.json()['objects']

    def get_wavelengths(self, instrument):
        """
        Get the wavelengths associated with the specified instrument

        :param instrument: Instrument name, as it is spelled in the database
        :returns: List of wavelengths
        """
        url = "http://127.0.0.1:8000/api/v1/instrumentwavelength/"
        params = {'instrument__name': instrument.lower()}
        r = self.get(url, params)

        wavelengths = [result['value'] for result in r]
        return wavelengths

    def get_images(self, search_list):
        """
        Get list of images, given the input search parameters
        
        :param search_list: Dictionary of search parameters
        :returns: JSON query results
        """
        url = "http://127.0.0.1:8000/api/v1/image/"
        params = self.construct_search_params(search_list)
        r = self.get(url, params)
        return r

    @staticmethod
    def construct_search_params(search_list):
        """
        Query url needs to have things in the right 'namespace', but we don't
        want the other tools to have to know what that is.

        This method converts user friendly search parameters into the ones that 
        django needs. Also allows for multiple ways of searching - can request
        "region" or "site" for the region name, and "instrument" or "sensor"

        :param search_list: Dictionary of search terms to include in this query
        :returns: Dictionary with same search values, but formatted correctly for tastypie to handle
        """
        params = {}

        # Dictionary holding conversion from user friendly names to django url names
        param_converter = {'region': 'region__region',
                           'site': 'region__region',
                           'instrument': 'instrument__name',
                           'sensor': 'instrument__name',
                           'start_date': 'time__gte',
                           'end_date': 'time__lte',
                           'order_by': 'order_by',
                           }

        # Construct dictionary with the new search_param:value pairs
        for item in search_list:
            try:
                params[param_converter[item]] = search_list[item].lower()
            except KeyError:
                raise KeyError(item+" not a valid search parameter")

        return params
