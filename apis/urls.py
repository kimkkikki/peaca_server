from django.conf.urls import url
from .views import user, party

urlpatterns = [
    url(r'^user$', user.user, name='user'),
    url(r'^party$', party.party, name='party'),
    url(r'^party/(?P<party_id>\w+)$', party.party_member, name='party_member'),
    url(r'^user/party$', user.my_party, name='my_party'),
]
