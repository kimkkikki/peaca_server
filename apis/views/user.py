from django.shortcuts import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from ..models import serialize_query_set, User
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
        uid = request.META['HTTP_ID']
        token = request.META['HTTP_TOKEN']

        user = User.objects.filter(id=uid, token=token)
        if len(user) != 0:
            return HttpResponse(json.dumps(serialize_query_set(user)), content_type='application/json')
        else:
            user = User.objects.filter(id=uid)
            user.token = uuid4()
            user.save()
            return HttpResponse(json.dumps(serialize_query_set(user)), content_type='application/json')
