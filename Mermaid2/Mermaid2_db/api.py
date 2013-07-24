from tastypie.resources import ModelResource
from tastypie.contrib.gis.resources import ModelResource as ModelResourceGeoDjango
from tastypie import fields
from Mermaid2_db.models import *
from tastypie.constants import ALL, ALL_WITH_RELATIONS
import math


class DeploymentResource(ModelResource):
    class Meta:
        queryset = Deployment.objects.all()
        excludes = ['id']
        include_resource_uri = False
        filtering = { 
            'site' : ALL,
            'pi' : ALL, 
        }
        

class InstrumentResource(ModelResource):
    class Meta:
        queryset = Instrument.objects.all()
        excludes = ['id']
        include_resource_uri = False   
        filtering = { 
            'name' : ALL,
            'instrumentwavelength' : ALL_WITH_RELATIONS, 
        }     


class PointResource(ModelResourceGeoDjango):

    deployment = fields.ForeignKey(DeploymentResource, 'deployment', full=True)
    
    class Meta:
        queryset = Point.objects.all()
        excludes = ['id']
        include_resource_uri = False
        filtering = { 
            'matchup_id' : ALL,
            'deployment' : ALL_WITH_RELATIONS, 
            'point' : ALL,
        }
      
         
class MeasurementTypeResource(ModelResource):
    class Meta:
        queryset = MeasurementType.objects.all()
        excludes = ['id']
        include_resource_uri = False 
        filtering = { 
            'type' : ALL, 
        }


class MeasurementWavelengthResource(ModelResource):
    class Meta:
        queryset = MeasurementWavelength.objects.all()
        excludes = ['id']
        include_resource_uri = False 
        filtering = { 
            'wavelength' : ALL, 
        }
        
                     
class MeasurementResource(ModelResource):

    point = fields.ForeignKey(PointResource, 'point', full=True)
    instrument = fields.ForeignKey(InstrumentResource, 'instrument', full=True)
    measurementtype = fields.ForeignKey(MeasurementTypeResource, 'measurement_type', full=True)
    wavelength = fields.ForeignKey(MeasurementWavelengthResource, 'measurement_wavelength', full=True, blank=True, null=True)
    
    class Meta:
        queryset = Measurement.objects.all()
        excludes = ['id']
        include_resource_uri = False
        filtering = { 
            'wavelength' : ALL_WITH_RELATIONS,
            'measurementtype' : ALL_WITH_RELATIONS,
            'point' : ALL_WITH_RELATIONS, 
        }

    def dehydrate(self, bundle):
        if math.isnan(bundle.data['value']):
            bundle.data['value'] = -999

        return bundle       
        
        
class ImageResource(ModelResource):

    #point = fields.ForeignKey(PointResource, 'point', full=True)  
    instrument = fields.ForeignKey(InstrumentResource, 'instrument', full=True, blank=True, null=True)        
        
    class Meta:
        queryset = Image.objects.all()
        excludes = ['id']
        include_resource_uri = False
        filtering = { 
            'top_left_point' : ALL,
            'bot_right_point' : ALL,
            'instrument' : ALL_WITH_RELATIONS,
            'point' : ALL_WITH_RELATIONS, 
        }        
        
        
