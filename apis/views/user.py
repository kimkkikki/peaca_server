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
        id = data['id']

        try:
            user = User.objects.get(id=id)
            user.push_token = data['push_token']
            user.save()
            return HttpResponse(json.dumps(user.serialize), content_type='application/json')
        except ObjectDoesNotExist:
            user = User()
            user.id = id
            user.gender = 'M' if data['gender'] == 'male' else 'W'
            user.name = data['name']
            user.email = data['email']
            user.picture_url = data['picture_url']
            user.birthday = datetime.strptime(data['birthday'], '%m/%d/%Y')

            if 'push_token' in data:
                user.push_token = data['push_token']

            user.save()
            return HttpResponse(json.dumps(user.serialize), content_type='application/json')
    else:
        try:
            uid = request.META['HTTP_ID']
            token = request.META['HTTP_TOKEN']
        except:
            return HttpResponse(status=400)

        try:
            user = User.objects.get(id=uid, token=token)
            return HttpResponse(json.dumps(user.serialize), content_type='application/json')
        except:
            user = User.objects.get(id=uid)
            user.token = uuid4()
            user.save()
            return HttpResponse(json.dumps(user.serialize), content_type='application/json')


@csrf_exempt
def my_party(request):
    if request.method == 'GET':
        uid = request.META['HTTP_ID']
        party_members = PartyMember.objects.filter(user=uid)
        return HttpResponse(json.dumps([i.expend_serialize for i in party_members]), content_type='application/json')
    else:
        return HttpResponse(status=404)
