from django.conf.urls import url

import views

urlpatterns = [
    url(r'add-view/$', views.edit, name='edit'),
    url(r'edit-view/(?P<view_id>[0-9]+)/$', views.edit, name='edit'),
    url(r'delete-view/(?P<view_id>[0-9]+)/$', views.delete_view, name='delete_view'),
    url(r'deep-analysis/$', views.deep_analysis, name='deep_analysis'),
    url(r'deep-analysis/(?P<view_id>[0-9]+)/$', views.deep_analysis, name='deep_analysis'),
    url(r'view-management/$', views.view_management, name='view_management'),
    url(r'^$', views.index, name='index')
]