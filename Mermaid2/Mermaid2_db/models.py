"""Django models for Mermaid2 Database"""

from django.contrib.gis.db import models


class Campaign(models.Model):
    """Campaign model defined by :\n
    - campaign : name of the campaign (CharField)
    """
    campaign = models.CharField(max_length=255)


class Deployment(models.Model):
    """Deployment model defined by :\n
    - site (CharField)
    - PI : Principal Investigator (CharField)
    - campaign (ForeignKey)
    """

    site = models.CharField(max_length=255)
    pi = models.CharField(max_length=255)
    campaign = models.ForeignKey(Campaign)


class Point(models.Model):
    """Point model defined by :\n
    - matchup_id : ID of in-situ point (CharField)
    - point : coordinates (lat lon) (PointField)
    - time_is : time (mermaid format) (CharField)
    - PQC : Processing Quality Control (CharField)
    - MQC : Measurement Quality Control (CharField)
    - land_dist_is : land distance (FloatField)
    - thetas_is : Solar zenith angled computed from time/lat/lon (FloatField)
    - deployment (ForeignKey)
    """

    matchup_id = models.CharField(max_length=255)
    point = models.PointField()
    time_is = models.DateTimeField()
    pqc = models.CharField(max_length=255)
    mqc = models.CharField(max_length=255)
    land_dist_is = models.FloatField()
    thetas_is = models.FloatField()
    deployment = models.ForeignKey(Deployment)

    objects = models.GeoManager()


class Instrument(models.Model):
    """Instrument model defined by :\n
    - name (CharField)
    """

    name = models.CharField(max_length=255)


class MeasurementType(models.Model):
    """Measurement type model defined by :\n
    - type (CharField)
    - units (CharField)
    - long_name (CharField)
    """

    type = models.CharField(max_length=255)
    units = models.CharField(max_length=255)
    long_name = models.CharField(max_length=255)

class MeasurementWavelength(models.Model):
    """Measurement wavelength model defined by :\n
    - wavelength (FloatField)
    """

    wavelength = models.FloatField()


class Measurement(models.Model):
    """Measurement model defined by :\n
    - value (FloatField)
    - measurement_type (ForeignKey)
    - point (ForeignKey)
    - wavelength (optional) (ForeignKey)
    - instrument (ForeignKey)
    """

    value = models.FloatField()
    measurement_type = models.ForeignKey(MeasurementType)
    point = models.ForeignKey(Point)
    wavelength = models.ForeignKey(MeasurementWavelength, blank=True, null=True)
    instrument = models.ForeignKey(Instrument)


class InstrumentWavelength(models.Model):
    """Instrument Wavelength model defined by :\n
    - value (FloatField)
    - instrument (ForeignKey)
    """

    value = models.FloatField()
    instrument = models.ForeignKey(Instrument)


class Image(models.Model):
    """Image model defined by :\n
    - web location
    - archive location
    - lat/lon min
    - lat/lon max
    - point
    - instrument

    model not finished
"""

    web_location = models.CharField(max_length=255)
    archive_location = models.CharField(max_length=255)	        
    top_left_point = models.PointField()
    bot_right_point = models.PointField() 
    #point = models.ForeignKey(Point)  
    instrument = models.ForeignKey(Instrument, blank=True, null=True)
