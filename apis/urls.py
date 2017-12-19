from django.urls import path
from .views import user, party, place

urlpatterns = [
    path('user', user.user, name='user'),
    path('party', party.party, name='party'),
    path('party/<int:party_id>', party.party_member, name='party_member'),
    path('party/<int:party_id>/push', party.send_push_to_party_member, name='send_push_to_party_member'),
    path('user/party', user.my_party, name='my_party'),
    path('place/<slug:place_id>', place.place, name='place'),
]
