from django.shortcuts import HttpResponse
from ..models import Place, PlacePhoto
from django.contrib.gis.geos import Point
from django.core.exceptions import ObjectDoesNotExist
import requests
import io
import json
from mimetypes import guess_extension
import asyncio
import logging
from requests import Response


logger = logging.getLogger(__name__)


async def get_photo(photo, loop) -> (str, Response):
    _photo_params = {'key': 'AIzaSyB3fOxMsaexXMRCkw7gItbC61PV_o45w4c',
                     'maxheight': 400,
                     'photoreference': photo['photo_reference']}

    def do_req():
        return requests.get(url='https://maps.googleapis.com/maps/api/place/photo', params=_photo_params)
    _photo_response = await loop.run_in_executor(None, do_req)

    _attributions = photo['html_attributions']

    _place_photo = PlacePhoto()
    _place_photo.id = photo['photo_reference']

    for _item in _attributions:
        try:
            _place_photo.attribution_url = _item.split('<a href="')[1].split('">')[0]
            _place_photo.attribution = _item.split('<a href="')[1].split('">')[1].split('</a>')[0]
        except IndexError:
            logger.warning('attribution string unknown format : ' + str(_item))

    return _place_photo, _photo_response


def place(request, place_id):
    if request.method == 'GET':
        _params = {'key': 'AIzaSyB3fOxMsaexXMRCkw7gItbC61PV_o45w4c',
                   'placeid': place_id}

        if place_id is not None:
            _response = None

            try:
                _place = Place.objects.get(id=place_id)

            except ObjectDoesNotExist:
                _response = requests.get('https://maps.googleapis.com/maps/api/place/details/json', params=_params)
                _json = _response.json()

                _status = _json['status']

                if _status == 'OK':
                    _result = _json['result']

                    _place = Place()
                    _place.id = _result['place_id']
                    _place.name = _result['name']
                    _place.utc_offset = _result['utc_offset']

                    _address = ''
                    for _item in _result['address_components']:
                        _address = _address + _item['long_name'] + ','

                    _place.address = _address
                    _place.point = Point(_result['geometry']['location']['lng'], _result['geometry']['location']['lat'], srid=4326)
                    _place.save()

                else:
                    return HttpResponse(status=400)

            _place_photos = PlacePhoto.objects.filter(place=_place)

            if len(_place_photos) == 0:
                if _response is None:
                    _response = requests.get('https://maps.googleapis.com/maps/api/place/details/json', params=_params)

                _json = _response.json()
                _status = _json['status']

                if _status == 'OK':
                    if 'photos' in _json['result']:
                        _photos = _json['result']['photos']
                        _photo_result = []

                        asyncio.set_event_loop(asyncio.new_event_loop())
                        _loop = asyncio.get_event_loop()
                        _futures = [asyncio.ensure_future(get_photo(_photo, _loop)) for _photo in _photos]
                        _loop.run_until_complete(asyncio.wait(_futures))
                        _loop.close()

                        for _future in _futures:
                            _place_photo, _image = _future.result()
                            _image_extension = guess_extension(_image.headers['Content-Type'].split()[0].rstrip(";"))

                            _place_photo.place = _place
                            _place_photo.image.save(_place_photo.id + '.' + _image_extension, io.BytesIO(_image.content), save=False)
                            _place_photo.save()

                            _photo_result.append(_place_photo)

                        return HttpResponse(json.dumps([i.serialize for i in _photo_result]), content_type='application/json')

                    else:
                        return HttpResponse(json.dumps([]), content_type='application/json')

                else:
                    return HttpResponse(status=400)

            else:
                return HttpResponse(json.dumps([i.serialize for i in _place_photos]), content_type='application/json')

        else:
            return HttpResponse(status=400)

    else:
        return HttpResponse(status=400)
#
#
# def place_photo(request, photo_reference):
#     _params = {'key': 'AIzaSyB3fOxMsaexXMRCkw7gItbC61PV_o45w4c',
#                'maxheight': 400,
#                'photoreference': photo_reference}
#
#     _response = requests.get('https://maps.googleapis.com/maps/api/place/photo', params=_params)
#     print(_response.content)
#     print(_response.headers)
#
#     return HttpResponse(_response, content_type=_response.headers['Content-Type'])
