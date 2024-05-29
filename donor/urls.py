from django.urls import path
from . import views

urlpatterns = [
    path('blood-requests/', views.blood_requests, name='donor-blood-requests'),
    path('respond-request/<int:pk>/<str:status>/<str:rt>', views.respond_request, name='donor-respond-request'),
    path('blood-notify/', views.notify, name='donor-blood-notify'),
    path('map/<int:pk>/<str:rt>', views.map, name='donor-map'),
]