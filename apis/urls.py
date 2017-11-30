from django.conf.urls import url
from .views import user, party, place

urlpatterns = [
    url(r'^user$', user.user, name='user'),
    url(r'^party$', party.party, name='party'),
    url(r'^party/(?P<party_id>\d+)$', party.party_member, name='party_member'),
    url(r'^party/(?P<party_id>\d+)/push$', party.send_push_to_party_member, name='send_push_to_party_member'),
    url(r'^user/party$', user.my_party, name='my_party'),
    url(r'^place/(?P<place_id>[\w-]+)$', place.place, name='place'),
]
