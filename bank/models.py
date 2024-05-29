from django.db import models
from django.contrib.auth.models import User

class BloodReserve(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    blood_group = models.CharField(max_length=10)
    amount = models.FloatField(default=0)
    status = models.CharField(max_length=20)
   
    def __str__(self):
        return self.user.name

    class Meta:
        db_table = 'blood_reserves'


class BankRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bank_user_id')
    blood_group = models.CharField(max_length=10)
    token_id = models.BigIntegerField()
    status = models.CharField(max_length=20, default='Open')
    date = models.DateField(auto_now_add=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
   
    def __str__(self):
        return self.user.first_name

    class Meta:
        db_table = 'bank_request'

class BankRequestDonor(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='brd_user_id')
    donor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='brd_donor_id')
    bank_request = models.ForeignKey(BankRequest, on_delete=models.CASCADE)
    blood_group = models.CharField(max_length=10)
    status = models.CharField(max_length=20, default='Pending')
    datetime = models.DateTimeField(auto_now_add=True)
    feedback = models.TextField(blank=True)
    rating = models.FloatField(blank=True, null=True)
   
    def __str__(self):
        return self.user.first_name

    class Meta:
        db_table = 'bank_request_donor'

class CollectBlood(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='upd_user_id')
    donor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='upd_donor_id')
    bank_request = models.ForeignKey(BankRequest, on_delete=models.CASCADE, null=True, blank=True)
    blood_group = models.CharField(max_length=10)
    amount = models.FloatField()
    datetime = models.DateTimeField(auto_now_add=True)
   
    def __str__(self):
        return self.user.first_name

    class Meta:
        db_table = 'blood_collection_from_donor'

class NotifyDonor(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='n_user_id')
    donor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='n_donor_id')
    blood_group = models.CharField(max_length=10)
    datetime = models.DateTimeField(auto_now_add=True)
   
    def __str__(self):
        return self.user.first_name

    class Meta:
        db_table = 'notify_donor'

class Usage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    blood_group = models.CharField(max_length=10)
    date = models.DateField(auto_now_add=True)
    amount = models.FloatField(null=True, blank=True)
   
    def __str__(self):
        return self.user.first_name

    class Meta:
        db_table = 'blood_usage'