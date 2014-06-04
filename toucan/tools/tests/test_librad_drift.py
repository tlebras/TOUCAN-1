from django.test import TestCase
from tools import librad_drift
from mock import *
import datetime

class RadiometricDriftTests(TestCase):
    """
    Test the radiometric drift library
    """
    def test_extract_fields(self):
        """
        Test the extraction of fields from JSON object
        """
        # Set up test dictionary, and the result we expect to get back
        blah = 'blah'   # Arbitrary string
        date = datetime.datetime(2000, 1, 1)
        angle = 0
        testjson = ({'archive_location': blah,
                     'time': date.strftime('%Y-%m-%dT%H:%M:%S.%f'),
                     'instrument': {'name':blah},
                     'region': {'region':blah},
                    }, )  # Needs to be a list

        expected_data = {'files': blah,
                         'dates': date,
                         'SZA': angle,
                         'VZA': angle,
                         'RAA': angle,
                         'instrument': blah,
                         'region': blah,
                         }

        # Mock libtools.get_angles as that is tested elsewhere
        with patch('tools.libtools.get_angles') as mock:
            mock.return_value = (angle, angle, angle)
            data = librad_drift.RadiometricDrift.extract_fields(testjson)
        self.assertDictEqual(data, expected_data)

    def test_region_check(self):
        """
        Check that exception is raised if target and reference regions don't match
        """
        reference = {'region': 'reference'}
        target = {'region': 'target'}
        self.assertRaises(IOError, librad_drift.RadiometricDrift.check_fields, reference, target)
