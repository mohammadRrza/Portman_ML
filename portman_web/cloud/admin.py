from django.contrib import admin
from .models import ConfigRequest, ConfigRequestLog, Device

# Register your models here.


admin.site.register(ConfigRequest)
admin.site.register(ConfigRequestLog)
admin.site.register(Device)
