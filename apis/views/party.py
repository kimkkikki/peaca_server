from django.shortcuts import HttpResponse
from ..models import User, Party, PartyMember
from django.contrib.gis.geos import Point
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime
import pytz


@csrf_exempt
def party(request):
    if request.method == 'POST':
        uid = request.META['HTTP_ID']
        data = json.loads(request.body.decode('utf-8'))

        user = User.objects.get(id=uid)

        print(data)

        party = Party()
        party.title = data['title']
        party.contents = data['contents']
        party.writer = user
        party.persons = data['persons']
        party.date = pytz.timezone(data['timezone']).localize(datetime.strptime(data['date'].split('+')[0], '%Y-%m-%dT%H:%M:%S'))
        party.timezone = data['timezone']
        party.gender = data['gender']

        party.destination_id = data['destination']['placeId']
        party.destination_name = data['destination']['name']
        party.destination_point = Point(data['destination']['coordinate']['longitude'], data['destination']['coordinate']['latitude'])
        party.destination_address = data['destination']['address']

        if 'source' in data:
            source = data['source']
            print('source : ' + str(source))
            party.source_id = data['source']['placeId']
            party.source_name = data['source']['name']
            party.source_point = Point(data['source']['coordinate']['longitude'], data['destination']['coordinate']['latitude'])
            party.source_address = data['source']['address']

        party.save()

        # Save Party Member
        party_member = PartyMember()
        party_member.party = party
        party_member.user = user
        party_member.status = 'master'
        party_member.save()

        return HttpResponse(json.dumps(party.serialize), content_type='application/json')
    else:
        # partys = Party.objects.filter(date__gte=datetime.utcnow().replace(tzinfo=pytz.utc))
        partys = Party.objects.all()

        results = []

        for p in partys:
            party_members = PartyMember.objects.filter(party=p)

            party_dict = p.serialize
            party_dict['count'] = len(party_members)
            results.append(party_dict)

        return HttpResponse(json.dumps(results), content_type='application/json')


# TODO: 모임참가 기능 추가해야댐
@csrf_exempt
def party_member(request, party_id):
    if request.method == 'POST':
        uid = request.META['HTTP_ID']

        party_member = PartyMember()
        party_member.user = User.objects.get(id=uid)
        party_member.party = Party.objects.get(id=party_id)
        party_member.status = 'member'

        party_member.save()
        return HttpResponse(json.dumps(party_member.serialize), content_type='application/json')

    else:
        party_members = PartyMember.objects.filter(party=party_id)
        return HttpResponse(json.dumps([i.serialize for i in party_members]), content_type='application/json')
