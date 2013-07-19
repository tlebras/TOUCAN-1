"""Django models for Mermaid2 Database"""

from django.contrib.gis.db import models
import re


class Deployment(models.Model):
    """Deployment model defined by :\n
    - site
    - PI : Principal Investigator
    """
    
    site = models.CharField(max_length=255)
    pi = models.CharField(max_length=255)
    
    
class Point(models.Model):
    """Point model defined by :\n
    - matchup_id : ID of in-situ point
    - point : coordinates (lat lon)
    - time_is : time (mermaid format)
    - PQC : Processing Quality Control
    - MQC : Measurment Quality Control
    - land_dist_is : land distance
    - thetas_is : Solar zenith angled computed from time/lat/lon 
    - deployment
    """
    
    matchup_id = models.CharField(max_length=255)
    point = models.PointField()
    time_is = models.CharField(max_length=255) 
    pqc = models.CharField(max_length=255)
    mqc = models.CharField(max_length=255)
    land_dist_is = models.FloatField()
    thetas_is = models.FloatField()
    deployment = models.ForeignKey(Deployment)
 
    objects = models.GeoManager()
     
        
class Instrument(models.Model):
    """Instrument model defined by :\n
    - name
    """

    name = models.CharField(max_length=255)  
 
              
class MeasurementType(models.Model):
    """Measurement type model defined by :\n
    - type
    - units
    """
    
    type = models.CharField(max_length=255)     
    units = models.CharField(max_length=255) 
 
 
class Measurement(models.Model):
    """Measurement model defined by :\n
    - value
    - point
    - wavelength (optional filed)
    - instrument
    """

    value = models.FloatField()
    measurement_type = models.ForeignKey(MeasurementType)    
    point = models.ForeignKey(Point)
    wavelength = models.FloatField(blank=True, null=True)
    instrument = models.ForeignKey(Instrument)     
     
                   
class InstrumentWavelength(models.Model):
    """Instrument Wavelength model defined by :\n
    - value
    - instrument
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
	"""
	
    web_location = models.CharField(max_length=255)
    archive_location = models.CharField(max_length=255)	        
    top_left_point = models.PointField()
    bot_right_point = models.PointField() 
    #point = models.ForeignKey(Point)  
    instrument = models.ForeignKey(Instrument, blank=True, null=True) 
 
    
    
    
          
  

