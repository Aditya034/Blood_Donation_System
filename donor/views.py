from django.shortcuts import render
from django.contrib.auth.models import User, auth
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.urls import reverse
from django.contrib import messages
from django.db import IntegrityError
from account.models import Profile, Role
from django.contrib.auth.decorators import login_required
import geopy
from geopy.geocoders import Nominatim
import geopy.distance
import folium
import random
from home.models import ReceiverRequest, RequestBank, RequestDonor
from django.shortcuts import redirect
from datetime import datetime
from bank.models import BankRequestDonor, BankRequest, NotifyDonor
from geopy.distance import geodesic as GD
from blood_donation.settings import EMAIL_HOST_USER
from django.core.mail import send_mail

# Create your views here.
@login_required
def blood_requests(request):
    check_request = RequestDonor.objects.filter(donor_id=int(request.user.id)).order_by('-id')
    check_request_banks = BankRequestDonor.objects.filter(donor_id=int(request.user.id)).order_by('-id')
    context = {
        'title': 'Your blood requests',
        'check_request' : check_request,
        'check_request_banks' : check_request_banks,
    }
    return render(request, 'donor/blood_requests.html', context)

@login_required
def respond_request(request, pk, status, rt):
    if rt == 'Receiver':
        check_request = RequestDonor.objects.get(pk=pk)
    else:
        check_request = BankRequestDonor.objects.get(pk=pk)
    check_request.status = status
    check_request.save()
    if status == 'Rejected':
        try:
            get_donor = User.objects.get(pk=check_request.donor_id)
            get_user = User.objects.get(pk=check_request.user_id)
            send_mail('Request rejected', f'Hello there! Your request for blood group {check_request.blood_group} has been rejected by {get_donor.first_name}', EMAIL_HOST_USER, [str(get_user.email)])
        except:
            pass
    messages.success(request, 'Request ' + status)
    return redirect(request.META.get('HTTP_REFERER'))


@login_required
def notify(request):
    check_request = NotifyDonor.objects.filter(donor_id=int(request.user.id)).order_by('-id')
    context = {
        'title': 'In Need blood',
        'check_request' : check_request,
    }
    return render(request, 'donor/notify.html', context)

@login_required
def map(request,pk,rt):
    data = None
    if rt == 'Receiver':
        data = ReceiverRequest.objects.get(pk=pk)
    else:
        data = BankRequest.objects.get(pk=pk)
    m = folium.Map(location=[data.latitude, data.longitude], zoom_start=7)
    folium.Marker((data.latitude, data.longitude), popup="Receiver is here", icon=folium.Icon(color="green")).add_to(m)
    cords = (request.user.profile.latitude, request.user.profile.longitude)
    folium.Marker(cords, popup="You are here").add_to(m)
    # folium.PolyLine([(request.user.profile.latitude, request.user.profile.longitude), (data.latitude, data.longitude)],
    #             color='green',
    #             weight=15,
    #             opacity=0.8).add_to(m)

    geolocator = Nominatim(user_agent="GetLoc")
    location = geolocator.reverse(f"{data.latitude},{data.longitude}")
    address = location.raw['address']
    city = address.get('city', '')

    geolocator = Nominatim(user_agent="GetLoc")
    receiver_data = (data.latitude, data.longitude)
    donor_data = (request.user.profile.latitude, request.user.profile.longitude)

    context = {
        'title': 'Map',
        'data' : data,
        'distance' : round(GD(receiver_data,donor_data).km),
        'map' : m._repr_html_(),
        'city' : city,
        'address' : address,
    }
    return render(request, 'donor/map.html', context)