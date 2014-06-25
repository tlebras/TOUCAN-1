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
            supersensor.data = {'reference': {'reflectance': None}, 'target': {'reflectance': None},}
            mock.return_value = y
            poly = supersensor.fit_polynomial(None, x, 2)
            # Use numpy allclose, as we don't get exactly zero for the 0th and 1st power coeffs
        self.assertTrue(np.allclose(poly, [1, 0, 0]))

    def test_recalibrate_band(self):
        """
        Check recalibration returns expected result
        """
        # Pretend our target sensor is always 10x the reference sensor
        # Recalibrated result should then be an array equal to the reference sensor
        dates = [datetime.datetime.fromtimestamp(d) for d in xrange(10)]
        poly = (0, 0, 9.0)  # (target - reference)/reference == always 9
        reference = np.arange(1.0, 11.0)
        target = reference * 10.0

        supersensor = libsupersensor.SuperSensor()
        supersensor.data = {'target': {'dates': dates,
                                       'reflectance': target}
                            }
        result = supersensor.recalibrate_band(poly)
        self.assertTrue(np.allclose(result, reference))

    def test_combine(self):
        """
        Check that recalibrated data are correctly combined
        """
        band_list = {'a': [100.0, ],
                     'b': [150.0, ]}

        dum = [np.zeros((2, 2)), ]   # Method expects a list here
        recalibrated = {'a': {100.0: dum},
                        'b': {150.0: dum}}

        # Output should expand the band lists for each sensor, replacing missing bands with nan arrays
        expected_bands = sorted(band_list['a'] + band_list['b'])
        nan_arr = [x * np.nan for x in dum]
        expected_combined = {'a': {100.0: dum, 150.0: nan_arr},
                             'b': {100.0: nan_arr, 150.0: dum}}

        bands, combined = libsupersensor.SuperSensor.combine_recalibrated(band_list, recalibrated)
        self.assertEqual(expected_bands, bands)
        np.testing.assert_equal(expected_combined, combined)

    def test_make_geotiff(self):
        """
        Check that correct arguments are passed to array2raster to create the geotiff
        """
        # Set up all the fields that make_geotiffs expects
        supersensor = libsupersensor.SuperSensor()
        supersensor.instrument = {'reference': 'reference'}
        supersensor.all_metadata = {'top_left_point': (0, 1),
                                    'bot_right_point': (1, 0),
                                    'region': 'region',
                                    'sensor': {'files': ('old_nadir.tif',),
                                               'dates': (datetime.datetime(2000, 1, 1),),
                                               },
                                    }
        bands = (1,)
        dum = np.zeros((2, 2))
        data_all = {'sensor': {1: (dum,)}}

        with patch('ingest_images_geo_tools.GeoTools.array2raster') as mock:
            with patch('os.mkdir') as _:  # Avoid creating a directory

                supersensor.make_geotiffs(data_all, bands)

                # Arguments that we expect array2raster to be called with
                direct = '/home/TOUCAN/toucan/tools/images/output/'
                new_file = direct + 'REGION/SUPER_REF_REFERENCE/2000/super_sensor_ref_reference_2000-01-01_nadir.tif'
                origin = (0, 0)
                dx, dy = 1, 1
                data = {'longitude': [0, 1],
                        'latitude': [0, 1],
                        1: dum}

                # Check they are the same
                mock.assert_called_with(new_file, origin, dx, dy, data, bands)