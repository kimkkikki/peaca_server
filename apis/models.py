from django.contrib.gis.db import models
from django.contrib.gis import admin
from django.contrib.postgres.fields import ArrayField
from mapwidgets.widgets import GooglePointFieldWidget
from uuid import uuid4
from datetime import datetime
import pytz
from django.conf import settings


def serialize_query_set(queryset):
    if len(queryset) > 1:
        result = [i.serialize for i in queryset]
    elif len(queryset) == 1:
        result = queryset[0].serialize
    else:
        result = {}
    return result


class User(models.Model):
    class Meta:
        db_table = 'user'
    id = models.CharField(primary_key=True, max_length=30)
    token = models.UUIDField(default=uuid4, unique=True)
    secret = models.UUIDField(default=uuid4, editable=False)
    email = models.CharField(max_length=50)
    name = models.CharField(max_length=20)
    nickname = models.CharField(max_length=20, null=True)
    birthday = models.DateField()
    os = models.CharField(max_length=1, choices=(('I', 'iOS'), ('A', 'Android')), default='I')
    push_token = models.CharField(max_length=200, null=True)
    picture_url = models.CharField(max_length=300, default="")
    photos = ArrayField(models.CharField(max_length=300), blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '%s' % self.id

    @property
    def serialize(self):
        return {'id': self.id,
                'token': str(self.token),
                'secret': str(self.secret),
                'email': self.email,
                'name': self.name,
                'os': self.os,
                'push_token': self.push_token,
                'photos': self.photos,
                'nickname': self.nickname,
                'birthday': self.birthday.strftime('%Y%m%d'),
                'picture_url': self.picture_url,
                'created': self.created.strftime('%Y%m%dT%H:%M:%S')}

    @property
    def serialize_public(self):
        return {'id': self.id,
                'name': self.name,
                'nickname': self.nickname,
                'picture_url': self.picture_url,
                'photos': self.photos,
                'created': self.created.strftime('%Y%m%dT%H:%M:%S')}


class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'email', 'name', 'nickname', 'birthday', 'created', 'updated']
    list_filter = ['created', 'updated']
    search_fields = ['name', 'nickname', 'email']


class Place(models.Model):
    class Meta:
        db_table = 'place'
    id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=200)
    point = models.PointField(db_index=True)
    utc_offset = models.IntegerField(default=0)
    address = models.CharField(max_length=200, default='')
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '%s' % self.name

    @property
    def serialize(self):
        return {'id': self.id,
                'name': self.name,
                'point': '%f,%f' % (self.point.x, self.point.y) if self.point is not None else None,
                'utc_offset': self.utc_offset,
                'address': self.address,
                'created': (datetime.now() if self.created is None else self.created).strftime('%Y-%m-%dT%H:%M:%S%z')}


class PlaceAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.PointField: {"widget": GooglePointFieldWidget}
    }
    list_display = ['id', 'name', 'point', 'created']
    list_filter = ['created']


def place_photo_directory_path(instance, filename):
    return 'place/{0}/{1}'.format(instance.place.id, filename)


class PlacePhoto(models.Model):
    class Meta:
        db_table = 'place_photo'
    id = models.CharField(max_length=200, primary_key=True)
    place = models.ForeignKey(Place, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=place_photo_directory_path)
    attribution = models.CharField(max_length=100, null=True, blank=True)
    attribution_url = models.CharField(max_length=200, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '%s' % self.id

    @property
    def serialize(self):
        return {'id': self.id,
                'place': self.place.id,
                'attribution': self.attribution,
                'attribution_url': self.attribution_url,
                'image': settings.MEDIA_URL + str(self.image),
                'created': (datetime.now() if self.created is None else self.created).strftime('%Y-%m-%dT%H:%M:%S%z')}


class PlacePhotoAdmin(admin.ModelAdmin):
    list_display = ['place', 'image', 'created']
    list_filter = ['created']


class Party(models.Model):
    class Meta:
        db_table = 'party'
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=50)
    contents = models.TextField()
    writer = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    persons = models.IntegerField()
    date = models.DateTimeField(db_index=True)
    destination = models.ForeignKey(Place, related_name='destination', on_delete=models.CASCADE)
    photo = models.ForeignKey(PlacePhoto, null=True, on_delete=models.SET_NULL)
    timezone = models.CharField(max_length=30, default='Asia/Seoul')
    source = models.ForeignKey(Place, related_name='source', null=True, blank=True, on_delete=models.SET_NULL)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '%s' % self.id

    @property
    def serialize(self):
        return {'id': self.id,
                'title': self.title,
                'contents': self.contents,
                'writer': self.writer.serialize_public,
                'persons': self.persons,
                'date': self.date.astimezone(pytz.timezone(self.timezone)).strftime('%Y-%m-%dT%H:%M:%S'),
                'destination': self.destination.serialize,
                'photo': self.photo.serialize if self.photo is not None else None,
                'source': self.source.serialize if self.source is not None else None,
                'created': (datetime.now() if self.created is None else self.created).strftime('%Y-%m-%dT%H:%M:%S%z')}


class PartyAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.PointField: {"widget": GooglePointFieldWidget}
    }
    list_display = ['id', 'title', 'destination', 'source', 'date', 'created']
    list_filter = ['created']
    search_fields = ['title', 'contents']


class PartyMember(models.Model):
    class Meta:
        db_table = 'party_member'
    id = models.AutoField(primary_key=True)
    party = models.ForeignKey(Party, db_index=True, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=6, choices=(('master', '방장'), ('member', '멤버'), ('ban', '강퇴'), ('exit', '나감')))
    created = models.DateTimeField(auto_now_add=True)

    @property
    def serialize(self):
        return {'id': self.id,
                'party': self.party.id,
                'user': self.user.serialize_public,
                'user_picture_url': self.user.picture_url,
                'status': self.status,
                'created': (datetime.now() if self.created is None else self.created).strftime('%Y-%m-%dT%H:%M:%S%z')}

    @property
    def expend_serialize(self):
        return {'id': self.id,
                'party': self.party.serialize,
                'user': self.user.serialize_public,
                'user_picture_url': self.user.picture_url,
                'status': self.status,
                'created': (datetime.now() if self.created is None else self.created).strftime('%Y-%m-%dT%H:%M:%S%z')}


class PartyMemberAdmin(admin.ModelAdmin):
    list_display = ['id', 'party', 'user', 'status', 'created']
    list_filter = ['created']


class PushMessage(models.Model):
    class Meta:
        db_table = 'push_message'
    id = models.AutoField(primary_key=True)
    sender = models.ForeignKey(User, related_name='sender', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='receiver', db_index=True, on_delete=models.CASCADE)
    message = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '%s' % self.id

    @property
    def serialize(self):
        return {'id': self.id,
                'sender': self.sender.id,
                'receiver': self.receiver.id,
                'message': self.message,
                'created': (datetime.now() if self.created is None else self.created).strftime('%Y-%m-%dT%H:%M:%S%z')}


class PushMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'sender', 'receiver', 'message', 'created']
    list_filter = ['created']
