from django.shortcuts import HttpResponse
from ..models import User, Party, PartyMember
from django.contrib.gis.geos import Point
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime
import pytz
import logging
from pyfcm import FCMNotification
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib.gis.db.models.functions import Distance, Value, IntegerField


logger = logging.getLogger(__name__)


@csrf_exempt
def party(request):
    if request.method == 'POST':
        _uid = request.META['HTTP_ID']
        _data = json.loads(request.body.decode('utf-8'))

        _user = User.objects.get(id=_uid)

        _party = Party()
        _party.title = _data['title']
        _party.contents = _data['contents']
        _party.writer = _user
        _party.persons = _data['persons']
        _party.date = pytz.timezone(_data['timezone']).localize(datetime.strptime(_data['date'].split('+')[0], '%Y-%m-%dT%H:%M:%S'))
        _party.timezone = _data['timezone']

        _party.destination_id = _data['destination']['placeId']
        _party.destination_name = _data['destination']['name']
        _party.destination_point = Point(_data['destination']['coordinate']['longitude'], _data['destination']['coordinate']['latitude'], srid=4326)
        _party.destination_address = _data['destination']['address']

        if 'source' in _data:
            source = _data['source']
            _party.source_id = source['placeId']
            _party.source_name = source['name']
            _party.source_point = Point(source['coordinate']['longitude'], source['coordinate']['latitude'], srid=4326)
            _party.source_address = source['address']

        _party.save()

        # Save Party Member
        _party_member = PartyMember()
        _party_member.party = _party
        _party_member.user = _user
        _party_member.status = 'master'
        _party_member.save()

        return HttpResponse(json.dumps(_party.serialize), content_type='application/json')

    else:
        # partys = Party.objects.filter(date__gte=datetime.utcnow().replace(tzinfo=pytz.utc))

        _page = request.GET.get('page', 1)

        _latitude = request.GET.get('latitude', 0)
        _longitude = request.GET.get('longitude', 0)

        if _latitude != 0 and _longitude != 0:
            _point = Point(float(_longitude), float(_latitude), srid=4326)
            partys = Party.objects.all().order_by('-created').annotate(distance=Distance('destination_point', _point))
        else:
            partys = Party.objects.all().order_by('-created').annotate(distance=Value(0, IntegerField()))

        _paginator = Paginator(partys, 10)

        try:
            partys = _paginator.page(_page)
        except PageNotAnInteger:
            partys = _paginator.page(1)
        except EmptyPage:
            partys = []

        results = []

        for p in partys:
            _members_count = PartyMember.objects.filter(party=p).count()

            party_dict = p.serialize

            if p.distance != 0:
                party_dict['distance'] = p.distance.km
            else:
                party_dict['distance'] = p.distance

            party_dict['count'] = _members_count

            if datetime.strptime(party_dict['date'], '%Y-%m-%dT%H:%M:%S') > datetime.utcnow():
                party_dict['status'] = 'I'
            else:
                party_dict['status'] = 'E'

            results.append(party_dict)

        logger.debug(results)

        return HttpResponse(json.dumps(results), content_type='application/json')


# TODO: 모임참가 기능 추가해야댐
@csrf_exempt
def party_member(request, party_id):
    if request.method == 'POST':
        uid = request.META['HTTP_ID']

        _already_joined_party_members = PartyMember.objects.filter(party_id=party_id)
        logger.info(_already_joined_party_members)

        for _joined_member in _already_joined_party_members:
            if _joined_member.user_id == uid:
                logger.info('already joined')

                _result = _joined_member.serialize
                _result['success'] = True
                return HttpResponse(json.dumps(_result), content_type='application/json')

        _party = Party.objects.get(id=party_id)

        _joined_count = len(_already_joined_party_members)
        _party_count = _party.persons

        if _joined_count < _party_count:
            _party_member = PartyMember()
            _party_member.user = User.objects.get(id=uid)
            _party_member.party = Party.objects.get(id=party_id)
            _party_member.status = 'member'
            _party_member.save()

            _result = _party_member.serialize
            _result['success'] = True

            return HttpResponse(json.dumps(_result), content_type='application/json')
        else:
            logger.error('chat rom is full')
            _result = {'success': False}
            return HttpResponse(json.dumps(_result), content_type='application/json')

    else:
        party_members = PartyMember.objects.filter(party=party_id)
        return HttpResponse(json.dumps([i.serialize for i in party_members]), content_type='application/json')


@csrf_exempt
def send_push_to_party_member(request, party_id):
    if request.method == 'POST':
        uid = request.META['HTTP_ID']
        data = json.loads(request.body.decode('utf-8'))

        tokens = []

        party_members = PartyMember.objects.filter(party_id=party_id)
        for member in party_members:
            if member.user.push_token is not None:
                if member.user.id == uid:
                    if member.user.nickname is not None:
                        data['sender_name'] = member.user.nickname
                    else:
                        data['sender_name'] = member.user.name
                else:
                    tokens.append(member.user.push_token)

        logger.info('data : ' + json.dumps(data))

        push_service = FCMNotification(api_key="AAAAo99UVFY:APA91bELR3C2GNdVF_PiuIXUKsM8S_0cgJa1PLbE1qsfuMS89gHI-pCPmE03EymlwqN7D-ewfXO76unh7tyx6mlMPzJKVDZnqfHuq6A9PdSh3oKvijDU9pQM1dfraNfDWQ3aae0SupcR")
        message_title = data['sender_name']
        message_body = data['message']

        result = push_service.notify_multiple_devices(registration_ids=tokens, message_title=message_title, message_body=message_body)
        logger.info(result)

        return HttpResponse(json.dumps(result), content_type='application/json')

    return HttpResponse(status=404)
