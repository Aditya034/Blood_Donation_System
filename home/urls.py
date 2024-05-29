from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    # path('compatibility-chart/', views.compatibility_chart, name='compatibility-chart'),
    path('search-donor/<str:lati>/<str:longi>/<str:filterby>/<str:blood>', views.search_donor, name='search-donor'),
    path('request-donor/<int:pk>/<str:blood>', views.request_donor, name='request-donor'),
    path('search-bank/<str:lati>/<str:longi>/<str:filterby>/<str:blood>', views.search_bank, name='search-bank'),
    path('request-bank/<int:pk>/<str:blood>', views.request_bank, name='request-bank'),
    path('blood-requests/', views.blood_requests, name='blood-requests'),
    path('close-request/<int:pk>', views.close_request, name='close-request'),
    path('request-details/<int:pk>', views.request_details, name='request-details'),
    path('feedback/<int:pk>/<str:role>', views.feedback, name='feedback'),
]