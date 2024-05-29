from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout, name='logout'),
    path('location-update/', views.location, name='location-update'),
    path('blood-group-update/', views.blood_group, name='blood-group-update'),
]