from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Role(models.Model):
    name = models.CharField(max_length=10)
   
    def __str__(self):
        return self.name

    class Meta:
        db_table = 'roles'

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mobile = models.CharField(max_length=10, unique=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    rating = models.FloatField(default=0)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    blood_group = models.CharField(max_length=10, null=True, blank=True)
   
    def __str__(self):
        return self.user.first_name

    class Meta:
        db_table = 'profiles'
