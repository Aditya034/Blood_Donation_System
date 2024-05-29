from django.urls import path
from . import views

urlpatterns = [
    path('users', views.users, name='admin-users'),
    path('dataset', views.dataset, name='admin-dataset'),
    path('statitics', views.statitics, name='admin-statitics'),
]