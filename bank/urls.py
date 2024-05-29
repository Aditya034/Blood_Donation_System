from django.urls import path
from . import views

urlpatterns = [
    path('blood-reserves/', views.blood_reserves, name='blood-reserves'),
    path('blood-requests/', views.blood_requests, name='bank-blood-requests'),
    path('respond-request/<int:pk>/<str:status>', views.respond_request, name='bank-respond-request'),
    path('search-donor/<str:filterby>/<str:blood>', views.search_donor, name='bank-search-donor'),
    path('request-donor/<int:pk>/<str:blood>', views.request_donor, name='bank-request-donor'),
    path('sent-requests/', views.sent_requests, name='sent-requests'),
    path('bank-close-request/<int:pk>', views.close_request, name='bank-close-request'),
    path('bank-request-details/<int:pk>', views.request_details, name='bank-request-details'),
    path('bank-collect-blood/<int:pk>/<str:blood>/<int:donor>', views.update_blood, name='bank-collect-blood'),
    path('blood-collection/', views.collection, name='blood-collection'),
    path('blood-update-status/<int:pk>/<str:blood>', views.update_status, name='bank-update-status'),
    path('blood-usage/<int:pk>/<str:blood>', views.usage, name='bank-blood-usage'),
    path('map/<int:pk>/<str:rt>', views.map, name='bank-map'),
]