from tastypie.resources import ModelResource
from tastypie import fields
from Mermaid2_db.models import *
from tastypie.constants import ALL, ALL_WITH_RELATIONS


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


class PointResource(ModelResource):
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
         
              
class MeasurementResource(ModelResource):

    point = fields.ForeignKey(PointResource, 'point', full=True)
    instrument = fields.ForeignKey(InstrumentResource, 'instrument', full=True)
    measurementtype = fields.ForeignKey(MeasurementTypeResource, 'measurement_type', full=True)
    
    class Meta:
        queryset = Measurement.objects.all()
        excludes = ['id']
        include_resource_uri = False
        filtering = { 
            'wavelength' : ALL,
            'measurementtype' : ALL_WITH_RELATIONS, 
        }
        
        
        
        
        
        
        
        
        
