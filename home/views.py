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
from django.db.models import Sum
import smtplib
from blood_donation.settings import EMAIL_HOST_USER
from django.core.mail import send_mail

@login_required
def index(request):
    if request.user.profile.role_id == 2 or request.user.profile.role_id == 3 or request.user.profile.role_id == 4:
        profile = Profile.objects.filter(user_id=int(request.user.id)).first()
        if profile.latitude is None or profile.longitude is None:
            return HttpResponseRedirect(reverse('location-update'))
    
    donors = Profile.objects.filter(role_id=2).count()
    banks = Profile.objects.filter(role_id=3).count()
    users = Profile.objects.filter(role_id=4).count()
        
    if request.method == 'POST':
        lati = request.POST['latitude']
        longi = request.POST['longitude']
        filterby = request.POST['filter_by']
        blood = request.POST['blood_group']
        if request.user.profile.role_id == 4:
            return HttpResponseRedirect(reverse('search-donor', kwargs={'lati':lati,'longi':longi,'filterby':filterby,'blood':blood}))
        elif request.user.profile.role_id == 3:
            return HttpResponseRedirect(reverse('bank-search-donor', kwargs={'filterby':filterby,'blood':blood}))
        else:
            return HttpResponseForbidden()
    context = {
        'title': 'Welcome to Blood Donation Portal',
        'donors' : donors,
        'banks' : banks,
        'users' : users,
    }
    return render(request, 'index.html', context)

@login_required
def search_donor(request, lati, longi, filterby, blood):
    if request.user.profile.role_id == 2:
        return HttpResponseRedirect(reverse('index'))
    
    lati = request.user.profile.latitude
    longi = request.user.profile.longitude
    
    geolocator = Nominatim(user_agent="GetLoc")
    location = geolocator.reverse(f"{lati},{longi}")
    address = location.raw['address']
    city = address.get('city', '')

    donors = Profile.objects.filter(role_id=2, blood_group=blood)

    m = folium.Map(location=[19.7515,75.7139], zoom_start=7)

    coordinates = []
    folium.Marker((lati,longi), popup="Your are here", icon=folium.Icon(color="red")).add_to(m)
    for d in donors:
        if d.latitude is not None:
            coordinates.append((float(d.latitude), float(d.longitude)))
            cords = (d.latitude, d.longitude)
            folium.Marker(cords, popup=d.user.first_name + " - " + d.role.name).add_to(m)

    coordinate = (lati, longi)
    pts = [geopy.Point(p[0],p[1]) for p in coordinates]
    onept = geopy.Point(coordinate[0],coordinate[1])
    alldist = [ (p,geopy.distance.distance(p, onept).km) for p in pts ]
    nearest_point = sorted(alldist, key=lambda x: (x[1]))
    # dd(nearest_point)

    near_locations_list_ids = []
    for n in nearest_point:
        lati_n = n[0].latitude
        longi_n = n[0].longitude
        profile = Profile.objects.filter(latitude=lati_n, longitude=longi_n, role_id = 2).first()
        if profile:
            near_locations_list_ids.append(profile.id)

    if filterby == 'Rating':
        donors = Profile.objects.filter(role_id=2, blood_group=blood, id__in=near_locations_list_ids).order_by('-rating')
    else:
        donors = Profile.objects.filter(role_id=2, blood_group=blood, id__in=near_locations_list_ids)

    # check_request = ReceiverRequest.objects.filter(blood_group=blood, user_id=int(request.user.id), status='Open').last()
    # donors_request = []
    # if check_request:
    #     donors_request = RequestDonor.objects.filter(receiver_request_id=check_request.id)

    donors_list = []
    expired_count = 0
    check_request = None
    for d in donors:
        check_request = ReceiverRequest.objects.filter(blood_group=blood, user_id=int(request.user.id), status='Open').last()
        if check_request:
            donors_request = RequestDonor.objects.filter(receiver_request_id=check_request.id, donor_id = d.user.id).first()
            if donors_request:
                start_date_time = donors_request.datetime
                start_date_time = str(start_date_time).split(" ")
                start_date_time[-1] = start_date_time[-1][:5]
                start_date_time = " ".join(start_date_time)
                start_date_time = datetime.strptime(start_date_time, "%Y-%m-%d %H:%M")

                end_date_time = datetime.now()
                end_date_time = str(end_date_time).split(" ")
                end_date_time[-1] = end_date_time[-1][:5]
                end_date_time = " ".join(end_date_time)
                end_date_time = datetime.strptime(end_date_time, "%Y-%m-%d %H:%M")

                difference_of_datetime = (end_date_time - start_date_time).total_seconds() // 60

                if difference_of_datetime >= 30 and donors_request.status == 'Pending':
                    expired_count += 1
                    donors_request.status = "Expired"
                    donors_request.save()
                    donor_dict = {'userid':d.user.id,'name':d.user.first_name,'username':d.user.username,'lati':d.latitude,'longi':d.longitude,'status':2}
                elif donors_request.status == 'Rejected':
                    expired_count += 1
                    donor_dict = {'userid':d.user.id,'name':d.user.first_name,'username':d.user.username,'lati':d.latitude,'longi':d.longitude,'status':3}
                else:
                    donor_dict = {'userid':d.user.id,'name':d.user.first_name,'username':d.user.username,'lati':d.latitude,'longi':d.longitude,'status':1}
            else:
                donor_dict = {'userid':d.user.id,'name':d.user.first_name,'username':d.user.username,'lati':d.latitude,'longi':d.longitude,'status':0}    
        else:
            donor_dict = {'userid':d.user.id,'name':d.user.first_name,'username':d.user.username,'lati':d.latitude,'longi':d.longitude,'status':0}
        donors_list.append(donor_dict)
    context = {
        'title': 'Search results for donors',
        'map' : m._repr_html_(),
        'donors' : donors,
        'blood' : blood,
        'donors_dict' : donors_list,
        'expired_count' : expired_count,
        'check_request' : check_request,
        'lati' : lati,
        'longi' : longi,
        'filterby' : filterby
    }
    return render(request, 'search_donor.html', context)

def generate_token_id():
    token_id = random.randint(1000000000,9999999999)
    check_token = ReceiverRequest.objects.filter(token_id=token_id).first()
    if check_token is not None:
        generate_token_id()
    else:
        return token_id

@login_required
def request_donor(request, pk, blood):
    if request.method == 'POST':
        check_request = ReceiverRequest.objects.filter(blood_group=blood, user_id=int(request.user.id), status='Open').last()
        if check_request is None:
            token_id = generate_token_id()
            new_request = ReceiverRequest()
            new_request.user = User.objects.get(pk = int(request.user.id))
            new_request.token_id = token_id
            new_request.blood_group = blood
            new_request.latitude = float(request.POST['lati'])
            new_request.longitude = float(request.POST['longi'])
            new_request.save()
        
        check_request = ReceiverRequest.objects.filter(blood_group=blood, user_id=int(request.user.id), status='Open').last()
        req_donor = RequestDonor()
        req_donor.user = User.objects.get(pk = int(request.user.id))
        req_donor.donor = User.objects.get(pk = pk)
        req_donor.receiver_request = ReceiverRequest.objects.get(pk = int(check_request.id))
        req_donor.blood_group = blood
        req_donor.save()
        messages.success(request, 'Request sent')
        try:
            get_donor = User.objects.get(pk=pk)
            send_mail('Request for blood', f'Hello there! I\'m looking for blood group {blood} and I found that your blood is also the same. Can you please donate your blood? Please accept my request on the portal. Thank you', EMAIL_HOST_USER, [str(get_donor.email)])
        except:
            pass
        return redirect(request.META.get('HTTP_REFERER'))
    
@login_required
def search_bank(request, lati, longi, filterby, blood):
    if request.user.profile.role_id == 2:
        return HttpResponseRedirect(reverse('index'))
    
    lati = request.user.profile.latitude
    longi = request.user.profile.longitude
    
    geolocator = Nominatim(user_agent="GetLoc")
    location = geolocator.reverse(f"{lati},{longi}")
    address = location.raw['address']
    city = address.get('city', '')

    banks = Profile.objects.filter(role_id=3)

    m = folium.Map(location=[19.7515,75.7139], zoom_start=7)

    coordinates = []
    folium.Marker((lati,longi), popup="Your are here", icon=folium.Icon(color="red")).add_to(m)
    for d in banks:
        if d.latitude is not None:
            coordinates.append((float(d.latitude), float(d.longitude)))
            cords = (d.latitude, d.longitude)
            folium.Marker(cords, popup=d.user.first_name + " - " + d.role.name).add_to(m)

    coordinate = (lati, longi)
    pts = [geopy.Point(p[0],p[1]) for p in coordinates]
    onept = geopy.Point(coordinate[0],coordinate[1])
    alldist = [ (p,geopy.distance.distance(p, onept).km) for p in pts ]
    nearest_point = sorted(alldist, key=lambda x: (x[1]))
    # dd(nearest_point)

    near_locations_list_ids = []
    for n in nearest_point:
        lati_n = n[0].latitude
        longi_n = n[0].longitude
        profile = Profile.objects.filter(latitude=lati_n, longitude=longi_n, role_id=3).first()
        if profile:
            near_locations_list_ids.append(profile.id)
    # print(near_locations_list_ids)

    if filterby == 'Rating':
        banks = Profile.objects.filter(role_id=3, id__in=near_locations_list_ids).order_by('-rating')
    else:
        banks = Profile.objects.filter(role_id=3, id__in=near_locations_list_ids)

    # check_request = ReceiverRequest.objects.filter(blood_group=blood, user_id=int(request.user.id), status='Open').last()
    # banks_request = []
    # if check_request:
    #     banks_request = Requestbank.objects.filter(receiver_request_id=check_request.id)

    banks_list = []
    expired_count = 0
    check_request = None
    for d in banks:
        check_request = ReceiverRequest.objects.filter(blood_group=blood, user_id=int(request.user.id), status='Open').last()
        if check_request:
            banks_request = RequestBank.objects.filter(receiver_request_id=check_request.id, bank_id = d.user.id).first()
            if banks_request:
                bank_dict = {'userid':d.user.id,'name':d.user.first_name,'username':d.user.username,'lati':d.latitude,'longi':d.longitude,'status':1}
            else:
                bank_dict = {'userid':d.user.id,'name':d.user.first_name,'username':d.user.username,'lati':d.latitude,'longi':d.longitude,'status':0}    
        else:
            bank_dict = {'userid':d.user.id,'name':d.user.first_name,'username':d.user.username,'lati':d.latitude,'longi':d.longitude,'status':0}
        banks_list.append(bank_dict)
    context = {
        'title': 'Search results for banks',
        'map' : m._repr_html_(),
        'banks' : banks,
        'blood' : blood,
        'banks_dict' : banks_list,
        'expired_count' : expired_count,
        'check_request' : check_request,
        'lati' : lati,
        'longi' : longi,
    }
    return render(request, 'search_bank.html', context)
    
@login_required
def request_bank(request, pk, blood):
    if request.method == 'POST':
        check_request = ReceiverRequest.objects.filter(blood_group=blood, user_id=int(request.user.id), status='Open').last()
        if check_request is None:
            token_id = generate_token_id()
            new_request = ReceiverRequest()
            new_request.user = User.objects.get(pk = int(request.user.id))
            new_request.token_id = token_id
            new_request.blood_group = blood
            new_request.latitude = float(request.POST['lati'])
            new_request.longitude = float(request.POST['longi'])
            new_request.save()
        
        check_request = ReceiverRequest.objects.filter(blood_group=blood, user_id=int(request.user.id), status='Open').last()
        req_bank = RequestBank()
        req_bank.user = User.objects.get(pk = int(request.user.id))
        req_bank.bank = User.objects.get(pk = pk)
        req_bank.receiver_request = ReceiverRequest.objects.get(pk = int(check_request.id))
        req_bank.blood_group = blood
        req_bank.save()

        try:
            get_donor = User.objects.get(pk=pk)
            send_mail('Request for blood', f'Hello there! I\'m looking for blood group {blood} and I found that your blood is also the same. Can you please donate your blood? Please accept my request on the portal. Thank you', EMAIL_HOST_USER, [str(get_donor.email)])
        except:
            pass
        messages.success(request, 'Request sent')
        return redirect(request.META.get('HTTP_REFERER'))
    

@login_required
def blood_requests(request):
    check_request = ReceiverRequest.objects.filter(user_id=int(request.user.id)).order_by('-id')
    context = {
        'title': 'Your blood requests',
        'check_request' : check_request,
    }
    return render(request, 'blood_requests.html', context)

@login_required
def close_request(request, pk):
    check_request = ReceiverRequest.objects.get(pk=pk)
    check_request.status = 'Closed'
    check_request.save()
    messages.success(request, 'Request closed')
    return redirect(request.META.get('HTTP_REFERER'))

@login_required
def request_details(request, pk):
    check_request = ReceiverRequest.objects.get(pk=pk)
    donors_details = RequestDonor.objects.filter(receiver_request_id = pk)
    banks_details = RequestBank.objects.filter(receiver_request_id = pk)
    context = {
        'title': 'Request ID: ' + str(check_request.token_id),
        'check_request' : check_request,
        'donors' : donors_details,
        'banks' : banks_details,
    }
    return render(request, 'request_details.html', context)

@login_required
def feedback(request, pk, role):
    check_request = None
    get_user = None
    ratings = 0
    ratings_count = 0
    if role == 'Donor':
        check_request = RequestDonor.objects.get(pk = pk)
    else:
        check_request = RequestBank.objects.get(pk = pk)

    if request.method == 'POST':
        check_request.rating = float(request.POST['rating'])
        check_request.feedback = request.POST['feedback']
        check_request.save()

        if role == 'Donor':
            get_user = Profile.objects.filter(user_id=check_request.donor_id).first()
            ratings = RequestDonor.objects.filter(donor_id=check_request.donor_id).aggregate(Sum('rating'))
            ratings_count = RequestDonor.objects.filter(donor_id=check_request.donor_id).exclude(rating = None).count()
        else:
            get_user = Profile.objects.filter(user_id=check_request.bank_id).first()
            ratings = RequestBank.objects.filter(bank_id=check_request.bank_id).aggregate(Sum('rating'))
            ratings_count = RequestBank.objects.filter(bank_id=check_request.bank_id).exclude(rating = None).count()

        now_rating = float(ratings['rating__sum']) / ratings_count
        get_user.rating = now_rating
        get_user.save()
    context = {
        'title': 'Provide feedback to this ' + role,
        'check_request' : check_request,
        'role' : role,
        'id' : pk,
        'rating' : check_request.rating,
        'feedback' : check_request.feedback,
    }
    return render(request, 'feedback.html', context)

# def compatibility_chart(request):
#     context = {
#         'title': 'Compatibility Chart'
#     }
#     return render(request, 'compatibility_chart.html', context)
