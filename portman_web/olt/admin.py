from django.contrib import admin
from .models import OLTType, OLT, OLTCommand, OLTTypeCommand
# Register your models here.


class OLTypeCommandInline(admin.TabularInline):
    model = OLTTypeCommand
    extra = 1


class CommandAdmin(admin.ModelAdmin):
    inlines = [OLTypeCommandInline, ]


admin.site.register(OLTType)
admin.site.register(OLT)
admin.site.register(OLTCommand, CommandAdmin)
