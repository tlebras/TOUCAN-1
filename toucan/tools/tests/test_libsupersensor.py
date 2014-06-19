import datetime
import numpy as np
from django.test import TestCase
from mock import *
from tools import libsupersensor 
import tools

class SuperSensorTests(TestCase):
    """
    Test the super sensor library
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
            data = libsupersensor.SuperSensor.extract_fields(testjson)
        self.assertDictEqual(data, expected_data)

    def test_fit_polynomial(self):
        """
        Check that polynomial fitting returns expected result
        """
        # fit_polynomial expects datetime objects for the x data.
        x0 = np.arange(10)
        x = [datetime.datetime.fromtimestamp(d) for d in x0]
        # Make y = x**2, so we know what output we should get from polyfit
        y = x0**2

        with patch('tools.libtools.get_sensor_bias', create=True) as mock:
            supersensor = libsupersensor.SuperSensor()
            supersensor.data = {'reference': {'reflectance': None}, 'calibration': {'reflectance': None},}
            mock.return_value = y
            poly = supersensor.fit_polynomial(None, x, 2)
            # Use numpy allclose, as we don't get exactly zero for the 0th and 1st power coeffs
        self.assertTrue(np.allclose(poly, [1, 0, 0]))