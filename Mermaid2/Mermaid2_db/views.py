# Create your views here.

from datetime import datetime
from Mermaid2_db.models import DeploymentPoint, Measurement, Photo, Deployment 
from Mermaid2_db.forms import UploadForm 
from django.http import HttpResponse
from django.shortcuts import render
import logging

logger = logging.getLogger(__name__)

#def add_point(request):

#    d1 = Deployment(site="HelsinkiLighthouse", pi="GiuseppeZibordi")
#    d1.save()
#    p1=DeploymentPoint(matchup_id="HLH_0_b_oc", lat_is=59.949, lon_is=24.926, time_is="20060517T061844Z", pqc="P10000000", mqc="M110100001110030101", land_dist_is=19, thetas_is=58.295, deployment=d1)
#    p2=DeploymentPoint(matchup_id="HLH_1_b_oc", lat_is=59.949, lon_is=24.926, time_is="20060517T064842Z", pqc="P10000000", mqc="M110100001110030101", land_dist_is=19, thetas_is=54.775, deployment=d1)
#    p1.save()
#    p2.save()
#    m11 = Measurement(parameter="Rho_wn_IS_412.5", units='dl', value=0.003822, point=p1)	
#    m12 = Measurement(parameter="LwN_IS_412.5", units='mW.m-2.nm-1.sr-1', value=0.208064, point=p1)
#    m13 = Measurement(parameter="Es_IS_412.5", units='mW.m-2.nm-1.s', value=631.750335, point=p1)
#    m21 = Measurement(parameter="Rho_wn_IS_412.5", units='dl', value=0.000674, point=p2)
#    m22 = Measurement(parameter="LwN_IS_412.5", units='mW.m-2.nm-1.sr-1', value=0.036671, point=p2) 
#    m23 = Measurement(parameter="Es_IS_412.5", units='mW.m-2.nm-1.s', value=714.189597, point=p2)       	
#    m11.save()
#    m12.save()
#    m13.save()
#    m21.save()
#    m22.save()
#    m23.save()
#    ph1 = Photo(web_location="http://web_location1.com", archive_location="/archive/location/1")
#    ph2 = Photo(web_location="http://web_location2.com", archive_location="/archive/location/2")
#    ph1.point = p1
#    ph2.point = p2
#    ph1.save()
#    ph2.save()

#    return HttpResponse("OK")
    
    
def upload_data(request):
    """View used to get the data from a file posted by a user.\n
    Uses the form UploadForm."""

    save = False
    
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            
            read_mandatory_data(form.cleaned_data.get('data'))

            save = True

    else:
        form = UploadForm()
    return render(request, 'Mermaid2_db/upload_data.html', locals())
    
    
def read_mandatory_data(file_data):
  
#    data = file_data.readline().split(';')
#    fields = DeploymentPoint._meta.get_all_field_names()
        
#    for i in range(len(data)):
#        if data[i].lower() in fields:
#            mandatory_limit = i+1
#
#    data = file_data.readline().split(';')

#    mandatory_data = data[:mandatory_limit]
    file_data.readline().split(';') 
    data = file_data.readline().split(';')
    
    deployment_data = data[1:3]   
    point_data = list()
    point_data.append(data[0])
    point_data += data[3:10]
       
    deployment = Deployment() 
    deployment.site = deployment_data[0]
    deployment.pi = deployment_data[1]
    deployment.save()
               
    point = DeploymentPoint()
    point.matchup_id = point_data[0]
    point.lat_is = point_data[1]
    point.lon_is = point_data[2]
    point.time_is = point_data[3]
    point.pqc = point_data[4]
    point.mqc = point_data[5]
    point.land_dist_is = point_data[6]
    point.thetas_is = point_data[7]
    point.deployment = deployment
    point.save() 
       
    for i in range(20):
        data = file_data.readline().split(';') 
        point_data = list()
        point_data.append(data[0])
        point_data += data[3:10]       
        point = DeploymentPoint()
        point.matchup_id = point_data[0]
        point.lat_is = point_data[1]
        point.lon_is = point_data[2]
        point.time_is = point_data[3]
        point.pqc = point_data[4]
        point.mqc = point_data[5]
        point.land_dist_is = point_data[6]
        point.thetas_is = point_data[7]
        point.deployment = deployment
        point.save()         

        
        
    
    
    
