from django.shortcuts import render
from django.contrib.auth.models import User, auth
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.urls import reverse
from django.contrib import messages
from django.db import IntegrityError
from account.models import Profile, Role
from django.contrib.auth.decorators import login_required

def add_roles():
    roles = Role.objects.count()
    if roles < 1:
        role = Role()
        role.name = 'Admin'
        role.save()
        role = Role()
        role.name = 'Donor'
        role.save()
        role = Role()
        role.name = 'Blood Bank'
        role.save()
        role = Role()
        role.name = 'Receiver'
        role.save()

# Create your views here.
def login(request):
    add_roles()

    check_admin = Profile.objects.filter(role_id=1).count()
    if check_admin < 1:
        user = User.objects.create_user(username = 'admin', password='admin', email='admin@gmail.com', first_name='Admin')
        user.save()
        last_user = User.objects.latest('id')
        profile = Profile()
        profile.mobile = '9090909090'
        profile.role = Role.objects.get(pk=1)
        profile.user = User.objects.get(pk=int(last_user.id))
        profile.save()

    if request.method == 'POST':
        user = auth.authenticate(username=request.POST['username'], password=request.POST['password'])
        if user is not None:
            auth.login(request, user)
            return HttpResponseRedirect(reverse('index'))
        else:
            messages.error(request, "Invalid credentials.")
            return HttpResponseRedirect(reverse('login'))
    context = {
        'title': 'Login',
    }
    return render(request, 'account/login.html', context)

def signup(request):
    add_roles()
    if request.method == 'POST':
        user = User.objects.create_user(username = request.POST['username'], password=request.POST['password'], email=request.POST['email'], first_name=request.POST['name'])
        user.save()
        last_user = User.objects.latest('id')
        profile = Profile()
        profile.mobile = request.POST['mobile']
        profile.role = Role.objects.get(pk=int(request.POST['role']))
        profile.user = User.objects.get(pk=int(last_user.id))
        profile.save()
        messages.success(request, "Signup successfully. You can login now.")
        return HttpResponseRedirect(reverse('login'))
    context = {
        'title': 'Signup',
    }
    return render(request, 'account/signup.html', context)

def logout(request):
    auth.logout(request)
    return HttpResponseRedirect(reverse('login'))

@login_required
def location(request):
    profile = Profile.objects.filter(user_id=int(request.user.id)).first()
    if request.method == 'POST':
        profile.latitude = float(request.POST['latitude'])
        profile.longitude = float(request.POST['longitude'])
        profile.save()
        messages.success(request, 'Location details updated')
        profile = Profile.objects.filter(user_id=int(request.user.id)).first()
    context = {
        'title': 'Location Update',
        'profile' : profile
    }
    return render(request, 'account/location.html', context)

@login_required
def blood_group(request):
    profile = Profile.objects.filter(user_id=int(request.user.id)).first()
    if request.method == 'POST':
        profile.blood_group = request.POST['blood_group']
        profile.save()
        messages.success(request, 'Blood group details updated')
        profile = Profile.objects.filter(user_id=int(request.user.id)).first()
    context = {
        'title': 'Blood Update',
        'profile' : profile
    }
    return render(request, 'account/blood_group.html', context)