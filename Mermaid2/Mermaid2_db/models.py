#from django.db import models
from django.contrib.gis.db import models

# Create your models here.


class Measurement(models.Model):
    """Measurements types availables :
    - normalised water reflectance (dl)
    - spectral water-leaving radiance (mW.m-2.nm-1.sr-1)
    - mean spectral total water leaving radiance (mW.m-2.nm-1.sr-1)
    - spectral sky radiance (mW.m-2.nm-1.sr-1)
    - water reflectance (dl)
    """
    
    UNITS_CHOICES = (
        ('dl', 'dl'),
        ('mW.m-2.nm-1.sr-1', 'mW.m<sup>-2</sup>.nm<sup>-1</sup>.sr<sup>-1</sup>'),
        ('uW.cm-2.nm.sr', 'uW.cm<sup>-2</sup>.nm.sr'),
        ('mW.m-2.nm-1.s', 'mW.m<sup>-2</sup>.nm<sup>-1</sup>.s'),
        ('nm', 'nm'),
        ('m-1', 'm<sup>-1</sup>'),
        ('W.m-2', 'W.m<sup>-2</sup>'),
        ('m', 'm'),
        ('mg.m-3', 'mg.m<sup>-3</sup>'),
        ('g.m-3', 'g.m<sup>-3</sup>'),  
        ('gC.m-3', 'gC.m<sup>-3</sup>'), 
        ('UTC', 'UTC'),
        ('cm', 'cm'),
        ('deg', '&ordm;'), 
    )
    
    #normalised water reflectance
    rho_wn_is = models.FloatField()
    rho_wn_is_unit = models.CharField(max_length=50, choices=UNITS_CHOICES, default='dl')
	
    #spectral water-leaving radiance
    lw_is = models.FloatField()	
    lw_is_unit = models.CharField(max_length=50, choices=UNITS_CHOICES, default='mWm-2nm-1sr-1')

    #mean spectral total water leaving radiance
    lt_is = models.FloatField()	
    lt_is_units = models.CharField(max_length=50, choices=UNITS_CHOICES, default='mWm-2nm-1sr-1')

    #spectral sky radiance
    lsky_is = models.FloatField()    
    lsky_is_units = models.CharField(max_length=50, choices=UNITS_CHOICES, default='mWm-2nm-1sr-1')
    
    #water reflectance
    rho_w_is = models.FloatField()
    rho_w_is = models.CharField(max_length=50, choices=UNITS_CHOICES, default='dl')

	
class Photo(models.Model):
    """Class defining a photo defined by :
    - web location
    - archive location
    """
	
    web_location = models.CharField(max_length=255)
    archive_location = models.CharField(max_length=255)	


class DeploymentPoint(models.Model):
    """Class defining a deploymemt point defined by :
    - matchup_ id : ID of in-situ point
    - site
    - pi : principal investigator
    - lat_is : latitude in-situ
    - lon_is : longitude in-situ
    - time_is : time (mermaid format)
    - pqc : processing quality control
    - mqc : measurement quality control
    - thetas_is : solr zenith angled computed from time/lat/lon 
    - measurements   
    """
    
    matchup_id = models.CharField(max_length=255)
    site = models.CharField(max_length=255)
    pi = models.CharField(max_length=255)
    lat_is = models.FloatField()
    lon_is = models.FloatField()
    time_is = models.TimeField()
    pqc = models.CharField(max_length=255)
    mqc = models.CharField(max_length=255)
    thetas_is = models.FloatField()
    measurements = models.ManyToManyField(Measurement)
    photo = models.ForeignKey(Photo)




#class MeasurementTypeManager(models.Manager):
#    """Management class for MeasurementType."""
#
#    def get_by_natural_key(self, normalised_name):
#        """Accessor to query for type based on normalised name.
#        :returns: object with given natural key.
#        """
#        return self.get(normalised_name=normalised_name)


#class MeasurementType(models.Model):
#    """A type of Scientific Measurement (ie salinity).
#    This is used to store validation information about a measurement
#    type as well as the units and general description.
#    """
#    objects = MeasurementTypeManager()

#    normalised_name = models.CharField(max_length=50, unique=True)
#    display_name = models.CharField(max_length=50, unique=True)

#    max_value = models.FloatField()
#    min_value = models.FloatField()

#    description = models.TextField()

#    UNITS_CHOICES = (
#        ('ppm', 'ppm'),
#        ('ms', 'm s<sup>-1</sup>'),
#        ('m', 'm'),
#        ('cel', '&ordm;C'),
#        ('rad', 'radians'),
#        ('deg', '&ordm;'),
#        ('psu', 'PSU'),
#        ('dbar', 'dbar'),
#        ('umoll', 'umol/l'),
#        ('umolk', 'umol/kg'),
#        ('mgm3', 'mg/m<sup>3</sup>'),
#    )

#    units = models.CharField(max_length=5, choices=UNITS_CHOICES)

#    def natural_key(self):
#        """Returns the natural key of the measurement type.
#        :returns: tuple representing the natural key
#        """
#        return (self.normalised_name, )

#    def __unicode__(self):
#        return u"{0} - {1}".format(self.display_name, self.units)
        

#class PointMeasurememt(models.Model):
#    """Class defining a basic measurememt point defined by :
#    - latitude, longitude, depth
#    - measurememt type
#    - image
#    """
	
#    latitude = models.FloatField()
#    longitude = models.FloatField()
#    depth = models.FloatField()
#    measurement = models.ManyToManyField(MeasurementType)
#    photo = models.ForeignKey(Photo)
    
    
    
    
    
