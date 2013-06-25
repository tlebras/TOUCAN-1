"""Django models for Mermaid2 Database"""

#from django.db import models
from django.contrib.gis.db import models
import re
# Create your models here.

class Deployment(models.Model):
    """Class defining a deploymemt defined by :\n
    - site
    - pi : Principal Investigator
    """
     
    site = models.CharField(max_length=255)
    pi = models.CharField(max_length=255)
      
    
class DeploymentPoint(models.Model):
    """Class defining a deployment point defined by :\n
    - matchup_id : ID of in-situ point
    - lat_is : latitude in-situ
    - lon_is : longitude in-situ
    - time_is : time (mermaid format)
    - pqc : processing quality control
    - mqc : measurement quality control
    - land_dist_IS : distance from land
    - thetas_is : solar zenith angled computed from time/lat/lon 
    """
    
    matchup_id = models.CharField(max_length=255)
    lat_is = models.FloatField()
    lon_is = models.FloatField()
    time_is = models.CharField(max_length=255)
    pqc = models.CharField(max_length=255)
    mqc = models.CharField(max_length=255)
    land_dist_is = models.FloatField()
    thetas_is = models.FloatField()
    deployment = models.ForeignKey(Deployment)
    
    def lat_ok(self):
        """Returns TRUE if latitude is between -90 and +90"""
        
        return (self.lat_is < 90) & (self.lat_is > -90)

    def lon_ok(self):
        """Returns TRUE if longitude is between -180 and +180"""
            
        return (self.lon_is < 180) & (self.lon_is > -180)
        
    def time_ok(self):
        """Returns TRUE if time respects the mermaid format"""
        
        time_format = r"^[0-9]{8}T[0-9]{6}Z$"
        if re.search(time_format, self.time_is) is None:      
            return False
        else:
            return True 

    def pqc_ok(self):
        """Returns TRUE if pqc respects the mermaid format"""
        
        pqc_format = r"^P[0-9]*$"
        if re.search(pqc_format, self.pqc) is None:      
            return False
        else:
            return True 

    def mqc_ok(self):
        """Returns TRUE if mqc respects the mermaid format"""
        
        mqc_format = r"^M[0-9]*$"
        if re.search(mqc_format, self.mqc) is None:      
            return False
        else:
            return True                    
    
    
class Photo(models.Model):
    """Class defining a photo defined by :\n
    - web location
    - archive location
    """
	
    web_location = models.CharField(max_length=255)
    archive_location = models.CharField(max_length=255)	    
    point = models.ForeignKey(DeploymentPoint)


class Measurement(models.Model):
    """Class defining a measurement point defined by :\n
    - parameter
    - value
    - units
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

    parameter = models.CharField(max_length=255)
    value = models.FloatField()
    units = models.CharField(max_length=50, choices=UNITS_CHOICES)
    point = models.ForeignKey(DeploymentPoint)



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
    
    
    
    
    
