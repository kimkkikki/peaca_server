from django.shortcuts import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from ..models import serialize_query_set, User, PartyMember
import json
from datetime import datetime
from uuid import uuid4


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


@csrf_exempt
def user(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        id = data['id']

        is_exist = User.objects.filter(id=id)

        if len(is_exist) == 0:
            user = User()
            user.id = id
            user.gender = 'M' if data['gender'] == 'male' else 'W'
            user.name = data['name']
            user.email = data['email']
            user.picture_url = data['picture_url']
            user.birthday = datetime.strptime(data['birthday'], '%m/%d/%Y')

            user.save()
            return HttpResponse(json.dumps(user.serialize), content_type='application/json')
        else:
            return HttpResponse(json.dumps(serialize_query_set(is_exist)), content_type='application/json')
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
