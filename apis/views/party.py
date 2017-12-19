from django.shortcuts import HttpResponse, get_object_or_404
from ..models import Party, PartyMember, PushMessage
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
        _data = json.loads(request.body.decode('utf-8'))

        _user = request.user

        _party = Party()
        _party.title = _data['title']
        _party.contents = _data['contents']
        _party.writer = _user
        _party.persons = _data['persons']
        _party.date = pytz.timezone(_data['timezone']).localize(datetime.strptime(_data['date'].split('+')[0], '%Y-%m-%dT%H:%M:%S'))
        _party.timezone = _data['timezone']

        _party.destination_id = _data['destination']['placeId']

        if 'source' in _data:
            _party.source_id = _data['source']['placeId']

        if 'photo' in _data:
            _party.photo_id = _data['photo']

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

        _party_query = Party.objects

        _latitude = request.GET.get('latitude', 0)
        _longitude = request.GET.get('longitude', 0)

        if _latitude != 0 and _longitude != 0:
            _point = Point(float(_longitude), float(_latitude), srid=4326)
            _party_query = _party_query.annotate(distance=Distance('destination__point', _point))
        else:
            _party_query = _party_query.annotate(distance=Value(0, IntegerField()))

        _order = request.GET.get('order', 0)

        if _order != 0:
            if _order == 'distance':
                _party_query = _party_query.order_by('distance')
            elif _order == 'time':
                _party_query = _party_query.order_by('-created')
        else:
            _party_query = _party_query.order_by('-created')

        _city = request.GET.get('city', 0)
        if _city != 0:
            _party_query = _party_query.filter(destination_address__icontains=_city)

        _search_keyword = request.GET.get('keyword', 0)
        if _search_keyword != 0:
            _party_query = _party_query.filter(contents__icontains=_search_keyword)

        _page = request.GET.get('page', 1)
        _paginator = Paginator(_party_query, 10)

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


@csrf_exempt
def party_member(request, party_id):
    _party = get_object_or_404(Party, pk=party_id)

    if request.method == 'POST':
        _user = request.user

        _already_joined_party_members = PartyMember.objects.filter(party=_party)
        logger.info(_already_joined_party_members)

        for _joined_member in _already_joined_party_members:
            if _joined_member.user_id == _user.id:
                logger.info('already joined')

                _result = _joined_member.serialize
                _result['success'] = True
                return HttpResponse(json.dumps(_result), content_type='application/json')

        _joined_count = len(_already_joined_party_members)
        _party_count = _party.persons

        if _joined_count < _party_count:
            _party_member = PartyMember()
            _party_member.user = _user
            _party_member.party = _party
            _party_member.status = 'member'
            _party_member.save()

            _result = _party_member.serialize
            _result['success'] = True

            return HttpResponse(json.dumps(_result), content_type='application/json')
        else:
            logger.error('chat rom is full')
            _result = {'success': False}
            return HttpResponse(json.dumps(_result), content_type='application/json')

    # TODO: 모임 탈퇴 기능 추가해야댐
    elif request.method == 'DELETE':
        return HttpResponse(status=200, content_type='application/json')

    else:
        party_members = PartyMember.objects.filter(party=party_id)
        return HttpResponse(json.dumps([i.serialize for i in party_members]), content_type='application/json')


@csrf_exempt
def send_push_to_party_member(request, party_id):
    _party = get_object_or_404(Party, pk=party_id)

    if request.method == 'POST':
        _user = request.user
        data = json.loads(request.body.decode('utf-8'))

        _tokens = []
        _members = []
        _sender = None

        party_members = PartyMember.objects.filter(party=_party)
        for member in party_members:
            if member.user.push_token is not None:
                if member.user.id == _user.id:
                    _sender = member.user
                    if _sender.nickname is not None:
                        data['sender_name'] = _sender.nickname
                    else:
                        data['sender_name'] = _sender.name
                else:
                    _tokens.append(member.user.push_token)
                    _members.append(member.user)

        if len(_tokens) > 0:
            logger.info('data : ' + json.dumps(data))

            push_service = FCMNotification(api_key="AAAAo99UVFY:APA91bELR3C2GNdVF_PiuIXUKsM8S_0cgJa1PLbE1qsfuMS89gHI-pCPmE03EymlwqN7D-ewfXO76unh7tyx6mlMPzJKVDZnqfHuq6A9PdSh3oKvijDU9pQM1dfraNfDWQ3aae0SupcR")
            message_title = data['sender_name']
            message_body = data['message']

            result = push_service.notify_multiple_devices(registration_ids=_tokens, message_title=message_title, message_body=message_body)
            logger.info(result)

            for _member in _members:
                _push_message = PushMessage()
                _push_message.sender = _sender
                _push_message.receiver = _member
                _push_message.message = message_body
                _push_message.save()

            return HttpResponse(json.dumps({'status': 'success'}), content_type='application/json')

        else:
            logger.info('no have receiver : ' + json.dumps(data))
            return HttpResponse(json.dumps({'status': 'success'}), content_type='application/json')

    elif request.method == 'DELETE':
        _user = request.user
        _push_messages = PushMessage.objects.filter(receiver=_user)
        _push_messages.delete()

        return HttpResponse(json.dumps({'status': 'success'}), content_type='application/json')

    elif request.method == 'GET':
        _user = request.user
        _message_count = PushMessage.objects.filter(receiver=_user).count()

        return HttpResponse(json.dumps({'count': _message_count}), content_type='application/json')

    return HttpResponse(status=404)
