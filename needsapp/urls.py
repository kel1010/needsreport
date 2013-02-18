from django.conf.urls.defaults import patterns, url

from needsapp import views, sms
 
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
    # url(r'^admin/', include(admin.site.urls)),

    url(r'^a/sms$', sms.handle_sms),
    url(r'^a/map_data$', views.map_data),
    url(r'^a/loc_data$', views.loc_data),
    url(r'^a/init_data$', views.init_data),
    url(r'^a/init_data$', views.init_data),
    url(r'^a/latest_needs', views.latest_needs),

    url(r'^$', views.index),
    url(r'^robots.txt$', views.robots),    
)

