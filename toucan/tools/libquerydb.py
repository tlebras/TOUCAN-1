import requests

class Querydb(object):
    """
    Perform query of the TOUCAN database, using the search parameters passed in
    """

    def __init__(self, search_list):
        self.search_list = search_list

    def get(self):
        """
        Do GET request and return objects

        :returns: JSON objects
        """
        url = "http://127.0.0.1:8000/api/v1/image/"
        params = self.construct_search_params(self.search_list)

        r = requests.get(url, params=params)

        # Raise error if status not ok
        r.raise_for_status()

        return r.json()['objects']

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
                           'end_date': 'time__lte'
                           }

        # Construct dictionary with the new search_param:value pairs
        for item in search_list:
            try:
                params[param_converter[item]] = search_list[item].lower()
            except KeyError:
                raise KeyError(item+" not a valid search parameter")

        return params
