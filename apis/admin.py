from django.contrib.gis import admin
from . import models


admin.site.register(models.Party, models.PartyAdmin)
admin.site.register(models.User, models.UserAdmin)
admin.site.register(models.PartyMember, models.PartyMemberAdmin)
