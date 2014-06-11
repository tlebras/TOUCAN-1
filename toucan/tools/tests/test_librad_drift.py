from django.test import TestCase
from tools import librad_drift
from mock import *
import datetime
import numpy as np

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
        Check that exception is raised if target and reference regions don't match (and not if they do)
        """
        reference = {'region': 'reference'}
        target = {'region': 'target'}

        # Check that IOError is raised for nonmatching regions
        self.assertRaises(IOError, librad_drift.RadiometricDrift.check_fields, reference, target)

        # Check no error raised if regions match
        librad_drift.RadiometricDrift.check_fields(reference, reference)

    def test_get_drift_timeseries(self):
        """
        Check that expected reflectance ratio timeseries is returned
        """
        # NB inputs need to be to be lists
        ref1 = 1.0
        ref2 = 2.0
        data = {'target': {'reflectance': [ref1,]},
                'reference': {'reflectance': [ref2,]}
                }
        doublet = ([0, 0], )
        result = librad_drift.RadiometricDrift.get_drift_timeseries(data, doublet)
        self.assertEquals(result, [ref1/ref2, ])  # Output will be a list

    def test_plot_drift(self):
        """
        Test the radiometric drift plot
        """
        with patch('matplotlib.pyplot.show') as mock:  # don't display the figure
            with patch('matplotlib.pyplot.savefig') as mock2:  # don't display the figure
                times = (datetime.datetime(2000, 1, 1), datetime.datetime(2001, 1, 1), datetime.datetime(2002, 1, 1))
                ref_ratio = (1, 2, 3)

                plot = librad_drift.RadiometricDrift.plot_radiometric_drift
                # Test without optional arguments
                plot(times, ref_ratio, 'target', 'reference', band=0)

                # Test with optional arguments
                plot(times, ref_ratio, 'target', 'reference', band=0, savename='plot.png')
