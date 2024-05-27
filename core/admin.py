from django.contrib import admin
from core.models.signal_user import SignalUser
from core.models.signal_group import SignalGroup
from core.models.signal_message import SignalMessage


class SignalUserAdmin(admin.ModelAdmin):
    pass


class SignalGroupAdmin(admin.ModelAdmin):
    pass


class SignalMessageAdmin(admin.ModelAdmin):
    pass


admin.site.register(SignalMessage, SignalMessageAdmin)
admin.site.register(SignalGroup, SignalGroupAdmin)
admin.site.register(SignalUser, SignalUserAdmin)
