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

from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn import metrics
from joblib import dump, load
import numpy as np
import csv
import pandas as pd
from home.models import RequestDonor, RequestBank
from bank.models import BankRequestDonor

from pathlib import Path
import os
BASE_DIR = Path(__file__).resolve().parent.parent

# Create your views here.
@login_required
def users(request):
    context = {
        'title': 'Registered Users',
        'users' : User.objects.all()
    }
    return render(request, 'admin/index.html', context)

@login_required
def statitics(request):
    receiver_to_donor = RequestDonor.objects.count()
    receiver_to_banks = RequestBank.objects.count()

    receiver_to_donor_accepted = RequestDonor.objects.filter(status='Accepted').count()
    receiver_to_banks_accepted = RequestBank.objects.filter(status='Accepted').count()

    receiver_to_donor_rejected = RequestDonor.objects.filter(status='Rejected').count()
    receiver_to_banks_rejected = RequestBank.objects.filter(status='Rejected').count()

    receiver_to_donor_expired = RequestDonor.objects.filter(status='Expired').count()
    receiver_to_banks_expired = RequestBank.objects.filter(status='Expired').count()

    receiver_to_donor_pending = RequestDonor.objects.filter(status='Pending').count()
    receiver_to_banks_pending = RequestBank.objects.filter(status='Pending').count()

    bank_to_donor = BankRequestDonor.objects.count()
    bank_to_donor_accepted = BankRequestDonor.objects.filter(status='Accepted').count()
    bank_to_donor_rejected = BankRequestDonor.objects.filter(status='Rejected').count()
    bank_to_donor_expired = BankRequestDonor.objects.filter(status='Expired').count()
    bank_to_donor_pending = BankRequestDonor.objects.filter(status='Pending').count()

    total = receiver_to_banks + receiver_to_donor + bank_to_donor
    accepted = receiver_to_donor_accepted + receiver_to_banks_accepted + bank_to_donor_accepted
    rejected = receiver_to_donor_rejected + receiver_to_banks_rejected + bank_to_donor_rejected
    expired = receiver_to_donor_expired + receiver_to_banks_expired + bank_to_donor_expired
    pending = receiver_to_donor_pending + receiver_to_banks_pending + bank_to_donor_pending
    context = {
        'title': 'statitics',
        'users' : User.objects.all(),
        'total' : total,
        'accepted' : accepted,
        'rejected' : rejected,
        'expired' : expired,
        'pending' : pending,
    }
    return render(request, 'admin/statitics.html', context)

@login_required
def dataset(request):
    result = None
    if request.method == 'POST':
        # file_exists = Path(str(BASE_DIR) + '/dataset/dataset.csv')
        # if file_exists.is_file():
        #     os.remove(str(BASE_DIR) + '/dataset/dataset.csv')

        # file = open(str(BASE_DIR) + '/dataset/dataset.csv', 'w')
        # file.close()

        # usage = Usage.objects.all()
        
        # with open(str(BASE_DIR) + '/dataset/dataset.csv', 'w') as csv_file:
        #     csv_writer = csv.writer(csv_file)
        #     # csv_writer.writerow(['id', 'amount', 'date', 'blood'])
        #     csv_writer.writerow(['id', 'date', 'blood'])

        # curret_date = datetime.today()
        # for i in usage:
        #     enddate = datetime.strptime(str(i.date), "%Y-%m-%d")
        #     days = enddate
        #     with open(str(BASE_DIR) + '/dataset/dataset.csv', 'a') as csv_file:
        #         csv_writer = csv.writer(csv_file)
        #         csv_writer.writerow([i.user.id, i.amount, days, i.blood_group])

        df = pd.read_csv(str(BASE_DIR) + '/dataset/dataset.csv')
        df['date'] = pd.to_datetime(df['date'])
        df['date'] = (df['date'] - df['date'].min())  / np.timedelta64(1,'D')
        df['blood'] = df['blood'].map({'A+': 1, 'B+': 2, 'AB+': 3, 'O+':4, 'A-': 5, 'B-': 6, 'AB-': 7, 'O-':8})
        print(df.head())

        feature_cols = ['id', 'date']
        X = df[feature_cols] # Features
        y = df.blood # Target variable

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=1) # 80% training and 20% test

        # Create Random Forest classifer object
        svm = SVC()
        # Train Decision Tree Classifer
        svm = svm.fit(X_train, y_train)
        dump(svm, str(BASE_DIR) + '/dataset/model_svm.pkl')
        #Predict the response for test dataset
        y_pred_svm = svm.predict(X_test)
        print("Accuracy: ", metrics.accuracy_score(y_test, y_pred_svm))
        result =  metrics.accuracy_score(y_test, y_pred_svm)
    context = {
        'title': 'Create and train dataset',
        'result' : result,
    }
    return render(request, 'admin/dataset.html', context)