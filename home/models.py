from django.db import models
from django.contrib.auth.models import User

class ReceiverRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_id')
    blood_group = models.CharField(max_length=10)
    token_id = models.BigIntegerField()
    status = models.CharField(max_length=20, default='Open')
    date = models.DateField(auto_now_add=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
   
    def __str__(self):
        return self.user.first_name

    class Meta:
        db_table = 'receiver_request'

class RequestDonor(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rd_user_id')
    donor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rd_donor_id')
    receiver_request = models.ForeignKey(ReceiverRequest, on_delete=models.CASCADE)
    blood_group = models.CharField(max_length=10)
    status = models.CharField(max_length=20, default='Pending')
    datetime = models.DateTimeField(auto_now_add=True)
    feedback = models.TextField(blank=True)
    rating = models.FloatField(blank=True, null=True)
   
    def __str__(self):
        return self.user.first_name

    class Meta:
        db_table = 'request_donor'

class RequestBank(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rb_user_id')
    bank = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rb_bank_id')
    receiver_request = models.ForeignKey(ReceiverRequest, on_delete=models.CASCADE)
    blood_group = models.CharField(max_length=10)
    status = models.CharField(max_length=20, default='Pending')
    datetime = models.DateTimeField(auto_now_add=True)
    feedback = models.TextField(blank=True)
    rating = models.FloatField(blank=True, null=True)
   
    def __str__(self):
        return self.user.first_name

    class Meta:
        db_table = 'request_bank'