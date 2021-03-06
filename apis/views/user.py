from django.shortcuts import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from ..models import User, PartyMember
from datetime import datetime
from uuid import uuid4
import json
import logging


logger = logging.getLogger(__name__)


@csrf_exempt
def user(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        _id = data['id']

        try:
            _user = User.objects.get(id=_id)

        except ObjectDoesNotExist:
            _user = User()
            _user.id = _id
            _user.name = data['name']
            _user.email = data['email']

        _user.picture_url = data['picture_url']

        if 'photos' in data:
            _photos = []
            for photo in data['photos']:
                _photos.append(photo['source'])

            _user.photos = _photos

        if 'push_token' in data:
            _user.push_token = data['push_token']

        _user.birthday = datetime.strptime(data['birthday'], '%m/%d/%Y')

        _user.save()

        return HttpResponse(json.dumps(_user.serialize), content_type='application/json')

    elif request.method == 'PUT':
        _data = json.loads(request.body.decode('utf-8'))
        _id = _data['id']
        _secret = _data['secret']

        try:
            _user = User.objects.get(id=_id, secret=_secret)
            _user.token = uuid4()
            _user.save()

            return HttpResponse(json.dumps(_user.serialize), content_type='application/json')

        except ObjectDoesNotExist:
            return HttpResponse(status=401)

    else:
        try:
            uid = request.META['HTTP_ID']
            token = request.META['HTTP_TOKEN']
        except KeyError:
            return HttpResponse(status=400)

        try:
            _user = User.objects.get(id=uid, token=token)
            return HttpResponse(json.dumps(_user.serialize), content_type='application/json')
        except ObjectDoesNotExist:

            try:
                _user = User.objects.get(id=uid)
                _user.token = uuid4()
                _user.save()
                return HttpResponse(json.dumps(_user.serialize), content_type='application/json')

            except ObjectDoesNotExist:
                logger.error('bad request : %s' % str(request.META))
                return HttpResponse(status=400)


@csrf_exempt
def my_party(request):
    if request.method == 'GET':
        _user = request.user
        party_members = PartyMember.objects.filter(user=_user).order_by('-created')

        _my_list = [i.expend_serialize for i in party_members]

        for _party_member in _my_list:
            _members_count = PartyMember.objects.filter(party=_party_member['party']['id']).count()
            _party_member['party']['count'] = _members_count

            if datetime.strptime(_party_member['party']['date'], '%Y-%m-%dT%H:%M:%S') > datetime.utcnow():
                _party_member['party']['status'] = 'I'
            else:
                _party_member['party']['status'] = 'E'

        return HttpResponse(json.dumps(_my_list), content_type='application/json')
    else:
        return HttpResponse(status=404)
