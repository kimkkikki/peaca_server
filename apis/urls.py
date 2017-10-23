from django.conf.urls import url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from .views import user, party

urlpatterns = [
    url(r'^$', user.index, name='index'),
    url(r'^user$', user.user, name='user'),
    url(r'^party$', party.party, name='party'),
    url(r'^party/(?P<party_id>\w+)$', party.party_member, name='party_member'),
    url(r'^user/party$', user.my_party, name='my_party'),
]

urlpatterns += staticfiles_urlpatterns()
