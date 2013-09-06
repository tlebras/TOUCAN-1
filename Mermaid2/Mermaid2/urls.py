from django.conf.urls import patterns, include, url
from Mermaid2_db.api import *
from tastypie.api import Api
from django.conf.urls.static import static
from django.conf import settings
# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

v1_api = Api(api_name='v1')
v1_api.register(DeploymentResource())
v1_api.register(PointResource())
v1_api.register(InstrumentResource())
v1_api.register(MeasurementTypeResource())
v1_api.register(MeasurementWavelengthResource())
v1_api.register(MeasurementResource())
v1_api.register(ImageResource())

urlpatterns = patterns('',
    # Examples:
    #url(r'^$', 'Mermaid2_db.views.upload_data'),
    url(r'^$', 'Mermaid2_db.views.home'),
    #url(r'^search_data/$', 'Mermaid2_db.views.search_data'),
    #url(r'^add_data/$', 'Mermaid2_db.views.add_data'),
    url(r'^add_data/$', 'Mermaid2_db.views.upload_data'),
    url(r'^add_instrument/$', 'Mermaid2_db.views.add_instrument'),
    url(r'^add_wavelengths/(\w+)/(\d+)$', 'Mermaid2_db.views.add_wavelengths'),
    #(r'^search/', include('haystack.urls')),
    url(r'^search_measurement/$', 'Mermaid2_db.views.search_measurement'),
    url(r'^search_point/$', 'Mermaid2_db.views.search_point'),
    
    #url(r'^add_image/$', 'Mermaid2_db.views.add_image'),
    #url(r'^see_image/$', 'Mermaid2_db.views.see_image'),
    
    (r'^api/', include(v1_api.urls)),
    # url(r'^Mermaid2/', include('Mermaid2.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)

