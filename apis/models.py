from django.contrib.gis.db import models
from django.contrib.gis import admin
from uuid import uuid4
from datetime import datetime
import pytz


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
    secret = models.UUIDField(default=uuid4, editable=False, unique=True)
    email = models.CharField(max_length=50)
    name = models.CharField(max_length=20)
    nickname = models.CharField(max_length=20, null=True)
    birthday = models.DateField()
    os = models.CharField(max_length=1, choices=(('I', 'iOS'), ('A', 'Android')), default='I')
    push_token = models.CharField(max_length=200, null=True)
    picture_url = models.CharField(max_length=300, default="")
    created = models.DateTimeField(auto_now_add=True)

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
                'created': self.created.strftime('%Y%m%dT%H:%M:%S')}


class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'email', 'name', 'nickname', 'birthday', 'created']
    list_filter = ['created']
    search_fields = ['name', 'nickname', 'email']


class Party(models.Model):
    class Meta:
        db_table = 'party'
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=50)
    contents = models.TextField()
    writer = models.ForeignKey(User, null=True)
    persons = models.IntegerField()
    date = models.DateTimeField(db_index=True)
    destination_id = models.CharField(max_length=100)
    destination_name = models.CharField(max_length=100, default='place_name')
    destination_point = models.PointField(db_index=True)
    destination_address = models.CharField(max_length=100, null=True, blank=True)
    timezone = models.CharField(max_length=30, default='Asia/Seoul')
    source_id = models.CharField(max_length=100, null=True, blank=True)
    source_name = models.CharField(max_length=100, default='place_name')
    source_point = models.PointField(db_index=True, null=True, blank=True)
    source_address = models.CharField(max_length=100, null=True, blank=True)
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
                'destination_id': self.destination_id,
                'destination_name': self.destination_name,
                'destination_point': '%f,%f' % (self.destination_point.x, self.destination_point.y),
                'destination_address': self.destination_address,
                'source_id': self.source_id,
                'source_point': '%f,%f' % (self.source_point.x, self.source_point.y) if self.source_point is not None else None,
                'source_name': self.source_name,
                'source_address': self.source_address,
                'created': (datetime.now() if self.created is None else self.created).strftime('%Y-%m-%dT%H:%M:%S%z')}


class PartyAdmin(admin.GeoModelAdmin):
    list_display = ['id', 'title', 'destination_id', 'destination_point', 'source_id', 'date', 'created']
    list_filter = ['created']
    search_fields = ['title', 'contents']


class PartyPoint(models.Model):
    class Meta:
        db_table = 'party_point'
    id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100)
    point = models.PointField(db_index=True)


class PartyMember(models.Model):
    class Meta:
        db_table = 'party_member'
    id = models.AutoField(primary_key=True)
    party = models.ForeignKey(Party, db_index=True)
    user = models.ForeignKey(User)
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


class PartyMemberAdmin(admin.GeoModelAdmin):
    list_display = ['id', 'party', 'user', 'status', 'created']
    list_filter = ['created']


class PushMessage(models.Model):
    class Meta:
        db_table = 'push_message'
    id = models.AutoField(primary_key=True)
    sender = models.ForeignKey(User, related_name='sender')
    receiver = models.ForeignKey(User, related_name='receiver', db_index=True)
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


class PushMessageAdmin(admin.GeoModelAdmin):
    list_display = ['id', 'sender', 'receiver', 'message', 'created']
    list_filter = ['created']
