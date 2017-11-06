from django.shortcuts import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from ..models import User, PartyMember
import json
from datetime import datetime
from uuid import uuid4


@csrf_exempt
def user(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        _id = data['id']

        try:
            _user = User.objects.get(id=_id)
            _user.push_token = data['push_token']
            _user.save()
            return HttpResponse(json.dumps(_user.serialize), content_type='application/json')
        except ObjectDoesNotExist:
            _user = User()
            _user.id = _id
            _user.gender = 'M' if data['gender'] == 'male' else 'W'
            _user.name = data['name']
            _user.email = data['email']
            _user.picture_url = data['picture_url']
            _user.birthday = datetime.strptime(data['birthday'], '%m/%d/%Y')

            if 'push_token' in data:
                _user.push_token = data['push_token']

            _user.save()

            return HttpResponse(json.dumps(_user.serialize), content_type='application/json')
    else:
        try:
            uid = request.META['HTTP_ID']
            token = request.META['HTTP_TOKEN']
        except:
            return HttpResponse(status=400)

        try:
            _user = User.objects.get(id=uid, token=token)
            return HttpResponse(json.dumps(_user.serialize), content_type='application/json')
        except:
            _user = User.objects.get(id=uid)
            _user.token = uuid4()
            _user.save()
            return HttpResponse(json.dumps(_user.serialize), content_type='application/json')


@csrf_exempt
def my_party(request):
    if request.method == 'GET':
        uid = request.META['HTTP_ID']
        party_members = PartyMember.objects.filter(user=uid)
        return HttpResponse(json.dumps([i.expend_serialize for i in party_members]), content_type='application/json')
    else:
        return HttpResponse(status=404)
