from django.conf.urls.defaults import patterns, include, url
from django.conf import settings

from django.contrib import admin

from needs import views
 
import os

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'needs.views.home', name='home'),
    # url(r'^needs/', include('needs.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    url(r'^a/sms$', views.sms),
    url(r'^a/map_data$', views.map_data),
    url(r'^a/loc_data$', views.loc_data),
    url(r'^a/init_data$', views.init_data),    
)
