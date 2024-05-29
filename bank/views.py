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
from bank.models import BloodReserve, BankRequest, BankRequestDonor, CollectBlood, NotifyDonor, Usage
from geopy.distance import geodesic as GD
from joblib import dump, load

from pathlib import Path
import os
BASE_DIR = Path(__file__).resolve().parent.parent

import smtplib
from blood_donation.settings import EMAIL_HOST_USER
from django.core.mail import send_mail

@login_required
def blood_reserves(request):
    reserves = BloodReserve.objects.filter(user_id=int(request.user.id))

    predict_val = None

    first_usage = Usage.objects.filter(user_id=int(request.user.id)).first()
    if first_usage:
        last_usage = Usage.objects.filter(user_id=int(request.user.id)).last()
        firstdate = datetime.strptime(str(first_usage.date), "%Y-%m-%d")
        enddate = datetime.strptime(str(last_usage.date), "%Y-%m-%d")
        diff = abs((enddate-firstdate).days)

        if diff > 0:
            # Predict
            model = load(str(BASE_DIR) + '/dataset/model_svm.pkl')
            predict = model.predict([[int(request.user.id), diff]])
            print(predict)
            if predict == 1:
                predict_val = 'A+'
            elif predict == 2:
                predict_val = 'B+'
            elif predict == 3:
                predict_val = 'AB+'
            elif predict == 4:
                predict_val = 'O+'
            elif predict == 5:
                predict_val = 'A-'
            elif predict == 6:
                predict_val = 'B-'
            elif predict == 7:
                predict_val = 'AB-'
            elif predict == 8:
                predict_val = 'O-'

    if request.method == 'POST':
        blood_group = request.POST['blood_group']
        amount = float(request.POST['amount'])
        status = request.POST['status']
        pre_check = BloodReserve.objects.filter(user_id=int(request.user.id), blood_group=blood_group).first()
        if pre_check:
            pre_check.amount = pre_check.amount + (amount)
            pre_check.status = status
            pre_check.save()
        else:
            br = BloodReserve()
            br.user = User.objects.get(pk=int(request.user.id))
            br.blood_group = blood_group
            br.amount = amount
            br.status = status
            br.save()
        messages.success(request, 'Blood reserves details updated')
        
    context = {
        'title': 'Blood Reserves',
        'reserves' : reserves,
        'predict_val' : predict_val,
    }
    return render(request, 'bank/blood_reserves.html', context)

@login_required
def blood_requests(request):
    check_request = RequestBank.objects.filter(bank_id=int(request.user.id)).order_by('-id')
    context = {
        'title': 'Your blood requests',
        'check_request' : check_request,
    }
    return render(request, 'bank/blood_requests.html', context)

@login_required
def respond_request(request, pk, status):
    check_request = RequestBank.objects.get(pk=pk)
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

def generate_token_id():
    token_id = random.randint(1000000000,9999999999)
    check_token = BankRequest.objects.filter(token_id=token_id).first()
    if check_token is not None:
        generate_token_id()
    else:
        return token_id
    
@login_required
def search_donor(request, filterby, blood):
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

    donors = Profile.objects.filter(role_id=2, blood_group=blood, id__in=near_locations_list_ids).order_by('-rating')

    # check_request = ReceiverRequest.objects.filter(blood_group=blood, user_id=int(request.user.id), status='Open').last()
    # donors_request = []
    # if check_request:
    #     donors_request = RequestDonor.objects.filter(bank_request_id=check_request.id)

    donors_list = []
    expired_count = 0
    check_request = None
    for d in donors:
        check_request = BankRequest.objects.filter(blood_group=blood, user_id=int(request.user.id), status='Open').last()
        if check_request:
            donors_request = BankRequestDonor.objects.filter(bank_request_id=check_request.id, donor_id = d.user.id).first()
            if donors_request:
                # start_date_time = donors_request.datetime
                # start_date_time = str(start_date_time).split(" ")
                # start_date_time[-1] = start_date_time[-1][:5]
                # start_date_time = " ".join(start_date_time)
                # start_date_time = datetime.strptime(start_date_time, "%Y-%m-%d %H:%M")

                # end_date_time = datetime.now()
                # end_date_time = str(end_date_time).split(" ")
                # end_date_time[-1] = end_date_time[-1][:5]
                # end_date_time = " ".join(end_date_time)
                # end_date_time = datetime.strptime(end_date_time, "%Y-%m-%d %H:%M")

                # difference_of_datetime = (end_date_time - start_date_time).total_seconds() // 60

                # if difference_of_datetime >= 30 and donors_request.status == 'Pending':
                #     expired_count += 1
                #     donors_request.status = "Expired"
                #     donors_request.save()
                #     donor_dict = {'userid':d.user.id,'name':d.user.first_name,'username':d.user.username,'lati':d.latitude,'longi':d.longitude,'status':2}
                # else:
                #     donor_dict = {'userid':d.user.id,'name':d.user.first_name,'username':d.user.username,'lati':d.latitude,'longi':d.longitude,'status':1}
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
    return render(request, 'bank/search_donor.html', context)

@login_required
def request_donor(request, pk, blood):
    if request.method == 'POST':
        check_request = BankRequest.objects.filter(blood_group=blood, user_id=int(request.user.id), status='Open').last()
        if check_request is None:
            token_id = generate_token_id()
            new_request = BankRequest()
            new_request.user = User.objects.get(pk = int(request.user.id))
            new_request.token_id = token_id
            new_request.blood_group = blood
            new_request.save()
        
        check_request = BankRequest.objects.filter(blood_group=blood, user_id=int(request.user.id), status='Open').last()
        req_donor = BankRequestDonor()
        req_donor.user = User.objects.get(pk = int(request.user.id))
        req_donor.donor = User.objects.get(pk = pk)
        req_donor.bank_request = BankRequest.objects.get(pk = int(check_request.id))
        req_donor.blood_group = blood
        req_donor.save()

        try:
            get_donor = User.objects.get(pk=pk)
            send_mail('Request for blood', f'Hello there! We\'re looking for blood group {blood} and we found that your blood is also the same. Can you please donate your blood? Please accept our request on the portal. Thank you', EMAIL_HOST_USER, [str(get_donor.email)])
        except:
            pass
        messages.success(request, 'Request sent')
        return redirect(request.META.get('HTTP_REFERER'))
    
@login_required
def sent_requests(request):
    check_request = BankRequest.objects.filter(user_id=int(request.user.id)).order_by('-id')
    context = {
        'title': 'Your blood requests',
        'check_request' : check_request,
    }
    return render(request, 'bank/sent_requests.html', context)
    
@login_required
def close_request(request, pk):
    check_request = BankRequest.objects.get(pk=pk)
    check_request.status = 'Closed'
    check_request.save()
    messages.success(request, 'Request closed')
    return redirect(request.META.get('HTTP_REFERER'))

@login_required
def request_details(request, pk):
    check_request = BankRequest.objects.get(pk=pk)
    donors_details = BankRequestDonor.objects.filter(bank_request_id = pk)
    context = {
        'title': 'Request ID: ' + str(check_request.token_id),
        'check_request' : check_request,
        'donors' : donors_details,
    }
    return render(request, 'bank/request_details.html', context)


@login_required
def update_blood(request, pk, blood, donor):
    details = BankRequest.objects.filter(pk = pk)
    donor_data = User.objects.get(pk=donor)

    if request.method == 'POST':
        amount = float(request.POST['amount'])

        pre_check = BloodReserve.objects.filter(user_id=int(request.user.id), blood_group=blood).first()
        if pre_check:
            pre_check.amount = pre_check.amount + (amount)
            pre_check.save()
        else:
            br = BloodReserve()
            br.user = User.objects.get(pk=int(request.user.id))
            br.amount = amount
            br.save()

        collect = CollectBlood()
        collect.user = User.objects.get(pk=int(request.user.id))
        collect.donor = User.objects.get(pk=donor)
        collect.bank_request = BankRequest.objects.get(pk=pk)
        collect.amount = amount
        collect.blood_group = blood
        collect.save()
    context = {
        'title': f'Update {blood} collecting from {donor_data.first_name}',
        'details' : details,
        'donor' : donor_data,
        'pk' : pk,
        'blood' : blood,
        'donor_id' : donor
    }
    return render(request, 'bank/update_blood.html', context)

@login_required
def collection(request):
    data = CollectBlood.objects.filter(user_id=int(request.user.id)).order_by('-id')
    print(data)
    context = {
        'title': 'Blood Collections',
        'data' : data,
    }
    return render(request, 'bank/collection.html', context)

@login_required
def update_status(request, pk, blood):
    pre_check = BloodReserve.objects.filter(id=pk).first()
    if request.method == 'POST':
        status = request.POST['status']

        get_donors_id = []
        my_donors = CollectBlood.objects.filter(user_id=int(request.user.id), blood_group=blood)
        for m in my_donors:
            get_donors_id.append(m.donor_id)
        donor_ids = set(get_donors_id)
        
        if status == 'In Need':
            for d in donor_ids:
                notify = NotifyDonor()
                notify.user = User.objects.get(pk=int(request.user.id))
                notify.donor = User.objects.get(pk=d)
                notify.blood_group = blood
                notify.save()
                try:
                    get_donor = User.objects.get(pk=d)
                    send_mail('Need for blood', f'Hello there! We\'re looking for blood group {blood} as we are in need for it. Thank you', EMAIL_HOST_USER, [str(get_donor.email)])
                except:
                    pass

                check_request = BankRequest.objects.filter(blood_group=blood, user_id=int(request.user.id), status='Open').last()
                if check_request is None:
                    token_id = generate_token_id()
                    new_request = BankRequest()
                    new_request.user = User.objects.get(pk = int(request.user.id))
                    new_request.token_id = token_id
                    new_request.blood_group = blood
                    new_request.save()
                
                check_request = BankRequest.objects.filter(blood_group=blood, user_id=int(request.user.id), status='Open').last()
                req_donor = BankRequestDonor()
                req_donor.user = User.objects.get(pk = int(request.user.id))
                req_donor.donor = User.objects.get(pk = d)
                req_donor.bank_request = BankRequest.objects.get(pk = int(check_request.id))
                req_donor.blood_group = blood
                req_donor.save()

                # try:
                #     get_donor = User.objects.get(pk=d)
                #     send_mail('Request for blood', f'Hello there! We\'re looking for blood group {blood} and we found that your blood is also the same. Can you please donate your blood? Please accept our request on the portal. Thank you', EMAIL_HOST_USER, [str(get_donor.email)])
                # except:
                #     pass
        pre_check.status = status
        pre_check.save()
    context = {
        'title': 'Update status for ' + blood,
        'pre_check' : pre_check,
        'pk' : pk,
        'blood' : blood
    }
    return render(request, 'bank/update_status.html', context)

@login_required
def usage(request, pk, blood):
    blood_data = BloodReserve.objects.filter(user_id=int(request.user.id), blood_group=blood).first()
    usage_data = Usage.objects.filter(user_id=int(request.user.id), blood_group=blood).order_by('-id')
    if request.method == 'POST':
        amount = float(request.POST['amount'])

        blood_data.amount = blood_data.amount - (amount)
        blood_data.save()

        usage_now = Usage()
        usage_now.user = User.objects.get(pk=int(request.user.id))
        usage_now.amount = amount
        usage_now.blood_group = blood
        usage_now.save()
    context = {
        'title': 'Usage of blood ' + blood,
        'blood_data' : blood_data,
        'usage_data' : usage_data,
        'pk' : pk,
        'blood' : blood,
    }
    return render(request, 'bank/usage.html', context)

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
    return render(request, 'bank/map.html', context)