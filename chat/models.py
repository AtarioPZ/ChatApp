from django.contrib.postgres.fields import ArrayField
from django.db import models

class CreatedUser(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(max_length=254, unique=True)
    password = models.CharField(max_length=128)
    name = models.CharField(max_length=255)
    date_of_birth = models.DateField()
    about = models.TextField()
    last_seen = models.DateTimeField()
    block_user = models.BooleanField(default=False)
    contacts = ArrayField(models.IntegerField())
    online_status = models.BooleanField(default=False)
    registration_date = models.DateTimeField(auto_now_add=True)
    gender = models.CharField(max_length=50)
    location = models.CharField(max_length=255)
    social_media_links = models.TextField()
    phone_number = models.CharField(max_length=20)
    notification_preferences = models.CharField(max_length=50)
    privacy_settings = models.CharField(max_length=50)
    account_status = models.CharField(max_length=50)
    two_factor_authentication = models.BooleanField(default=False)
    colour_theme = models.CharField(max_length=50)
