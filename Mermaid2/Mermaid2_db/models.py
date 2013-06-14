#from django.db import models
from django.contrib.gis.db import models

# Create your models here.


class Deploymemt(models.Model):
    """Class defining a deploymemt
    """
    
    matchup_id = models.CharField(max_length=255)
    site = models.CharField(max_length=255)
    principal_investigator = models.CharField(max_length=255)
    lat_is = models.FloatField()
    lon_is = models.FloatField()
    time_is = models.TimeField()
    pqc = models.CharField(max_length=255)
    mqc = models.CharField(max_length=255)
    thetas_is = models.FloatField()
    point = models.PointField()
	
class Photo(models.Model):
    """Class defining a photo defined by :
    - web location
    - archive location
    """
	
    web_location = models.CharField(max_length=255)
    archive_location = models.CharField(max_length=255)	


class MeasurementTypeManager(models.Manager):
    """Management class for ScientificMeasurementType."""

    def get_by_natural_key(self, normalised_name):
        """Accessor to query for type based on normalised name.
        :returns: object with given natural key.
        """
        return self.get(normalised_name=normalised_name)


class MeasurementType(models.Model):
    """A type of Scientific Measurement (ie salinity).
    This is used to store validation information about a measurement
    type as well as the units and general description.
    """
    objects = MeasurementTypeManager()

    normalised_name = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=50, unique=True)

    max_value = models.FloatField()
    min_value = models.FloatField()

    description = models.TextField()

    UNITS_CHOICES = (
        ('ppm', 'ppm'),
        ('ms', 'm s<sup>-1</sup>'),
        ('m', 'm'),
        ('cel', '&ordm;C'),
        ('rad', 'radians'),
        ('deg', '&ordm;'),
        ('psu', 'PSU'),
        ('dbar', 'dbar'),
        ('umoll', 'umol/l'),
        ('umolk', 'umol/kg'),
        ('mgm3', 'mg/m<sup>3</sup>'),
    )

    units = models.CharField(max_length=5, choices=UNITS_CHOICES)

    def natural_key(self):
        """Returns the natural key of the measurement type.
        :returns: tuple representing the natural key
        """
        return (self.normalised_name, )

    def __unicode__(self):
        return u"{0} - {1}".format(self.display_name, self.units)
        

class PointMeasurememt(models.Model):
    """Class defining a basic measurememt point definided by :
    - latitude, longitude, depth
    - measurememt type
    - image
    """
	
    #try to use PointField
    latitude = models.FloatField()
    longitude = models.FloatField()
    depth = models.FloatField()
    measurement = models.ManyToManyField(MeasurementType)
    photo = models.ForeignKey(Photo)




#class ScientificImageMeasurement(models.Model):
#    """Scientific Measurement relating to an image."""
#    measurement_type = models.ForeignKey(ScientificMeasurementType)
#    image = models.ForeignKey(Image)
#    value = models.FloatField()
#
#    class Meta:
#        """Defines Metaparameters of the model."""
#        unique_together = (('measurement_type', 'image'), )



