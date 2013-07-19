"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from Mermaid2_db.models import Deployment, Point
import re

def lat_lon_ok(point):

    return (point.x <= 90 and 
            point.x >= -90 and
            point.y <= 180 and 
            point.y >= -180 
    )
    
    
def time_ok(time):

    exp = r"^[0-9]{8}T[0-9]{6}Z$"
    if re.search(exp, time) is None:
        return False
    else:
        return True

def pqc_ok(pqc):

    exp = r"^P[0-9]{8}$"
    if re.search(exp, pqc) is None:
        return False
    else:
        return True


def mqc_ok(mqc):

    exp = r"^M[0-9]{18}$"
    if re.search(exp, mqc) is None:
        return False
    else:
        return True


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


    def test_lat_lon_value(self):
        """checks if latitude value is between -90 and +90 deg"""
    
        point = Point(point = 'POINT(100 100)')
        self.assertEqual(lat_lon_ok(point.point), False)
        point = Point(point = 'POINT(50 200)')
        self.assertEqual(lat_lon_ok(point.point), False) 
        point = Point(point = 'POINT(90 100)')
        self.assertEqual(lat_lon_ok(point.point), True)        
        
        
    def test_time_value(self):
        """checks if time respects the mermaid format"""
        
        point = Point(time_is="20060517T061844Z")
        self.assertEqual(time_ok(point.time_is), True)        
        point = Point(time_is="123456789")
        self.assertEqual(time_ok(point.time_is), False)         
      
        
    def test_pqc_value(self):
        """checks if pqc respects the mermaid format"""        
        
        point = Point(pqc="P10000000")
        self.assertEqual(pqc_ok(point.pqc), True)
        point = Point(pqc="abc123")
        self.assertEqual(pqc_ok(point.pqc), False)
     
        
    def test_mqc_value(self):
        """checks if mqc respects the mermaid format"""        
       
        point = Point(mqc="M110100001110030101")
        self.assertEqual(mqc_ok(point.mqc), True)
        point = Point(time_is="abc123")
        self.assertEqual(mqc_ok(point.mqc), False)        
        
                  
        
        
        
    
    
                
