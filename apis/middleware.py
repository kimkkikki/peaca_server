from django.shortcuts import HttpResponse
from django.core.exceptions import ObjectDoesNotExist, ValidationError
import logging
# import re
from .models import User


logger = logging.getLogger(__name__)


def pre_handle_request(get_response):
    # One-time configuration and initialization.

    def middleware(request):
        _dont_check_token = [
            '/apis/user',
        ]

        _meta = request.META
        _path = _meta['PATH_INFO']

        if _path not in _dont_check_token:
            try:
                _uid = _meta['HTTP_ID']
                _token = _meta['HTTP_TOKEN']

                try:
                    _user = User.objects.get(id=_uid, token=_token)
                    request.user = _user
                except ObjectDoesNotExist:
                    return HttpResponse(status=401)
                except ValidationError:
                    return HttpResponse(status=401)

            except KeyError:
                return HttpResponse(status=401)

        response = get_response(request)

        return response

    return middleware
