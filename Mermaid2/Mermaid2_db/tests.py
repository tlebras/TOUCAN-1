"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from Mermaid2_db.models import Deployment, DeploymentPoint, Photo

class SimpleTest(TestCase):


    def test_pi_value(self):
        """checks if pi is alphanumeric"""
        
        deployment = Deployment(site="GiuseppeZibordi")
        self.assertEqual(deployment.site.isalnum(), True)
        deployment = Deployment(site="Giuseppe Zibordi")
        self.assertEqual(deployment.site.isalnum(), False)  

    def test_site_value(self):
        """checks if site is alphanumeric"""
        
        deployment = Deployment(site="HelsinkiLighthouse")
        self.assertEqual(deployment.site.isalnum(), True)
        deployment = Deployment(site="Helsinki Lighthouse")
        self.assertEqual(deployment.site.isalnum(), False)  

    def test_lat_value(self):
        """checks if latitude value is between -90 and +90 deg"""
    
        point = DeploymentPoint(lat_is=100)
        self.assertEqual(point.lat_ok(), False)
        point = DeploymentPoint(lat_is=-100)
        self.assertEqual(point.lat_ok(), False) 
        point = DeploymentPoint(lat_is=50)       
        self.assertEqual(point.lat_ok(), True)        
        
    def test_lon_value(self):
        """checks if longitude value is between -180 and +180 deg""" 
        
        point = DeploymentPoint(lon_is=200)
        self.assertEqual(point.lon_ok(), False)
        point = DeploymentPoint(lon_is=-200)
        self.assertEqual(point.lon_ok(), False) 
        point = DeploymentPoint(lon_is=50)       
        self.assertEqual(point.lon_ok(), True) 
        
    def test_time_value(self):
        """checks if time respects the mermaid format"""
        
        point = DeploymentPoint(time_is="20060517T061844Z")
        self.assertEqual(point.time_ok(), True)        
        point = DeploymentPoint(time_is="123456789")
        self.assertEqual(point.time_ok(), False)         
        
    def test_pqc_value(self):
        """checks if pqc respects the mermaid format"""        
        
        point = DeploymentPoint(pqc="P10000000")
        self.assertEqual(point.pqc_ok(), True)
        point = DeploymentPoint(time_is="abc123")
        self.assertEqual(point.pqc_ok(), False)
        
    def test_mqc_value(self):
        """checks if mqc respects the mermaid format"""        
        
        point = DeploymentPoint(mqc="M110100001110030101")
        self.assertEqual(point.mqc_ok(), True)
        point = DeploymentPoint(time_is="abc123")
        self.assertEqual(point.mqc_ok(), False)        
        
                  
        
        
        
                
