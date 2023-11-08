from django.db import models

# Create your models here.
class staff(models.Model):
    staffId = models.AutoField(primary_key=True)
    name = models.CharField(max_length=24)
    email = models.EmailField()
    phone = models.CharField(max_length=11)
    pwd = models.CharField(max_length=20)
    types = (
        ('S', 'service'),
        ('F', 'finance')
    )
    staffType = models.CharField(choices=types, max_length=20)
    status = (
        ('A', 'active'),
        ('D', 'depart'),
        ('S', 'stop')
    )
    staffStatus = models.CharField(choices=status, max_length=20)
    deleted = models.BooleanField(default = 0)


class manager(models.Model):
    mId = models.AutoField(primary_key=True)
    pwd = models.CharField(max_length=20)

class notice(models.Model):
    nId = models.AutoField(primary_key=True)
    noticeName = models.CharField(max_length=50)
    noticeContent = models.TextField()
    noticeFile = models.BinaryField()
    noticeDate = models.DateTimeField()
    public = models.BooleanField(default=True)
    deleted = models.BooleanField(default = 0)