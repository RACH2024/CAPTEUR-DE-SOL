from django.contrib import admin
from django.conf.locale.es import formats as es_formats
from .models import *
from .models import SensorData

admin.site.register(Makerfabs)
admin.site.register(vann)
admin.site.register(CapSol)
admin.site.register(CapSol2)
admin.site.register(CapSolGraviometrie)
admin.site.register(Ws)
admin.site.register(Data)
admin.site.register(Data2)
# admin.site.register(ET0)
admin.site.register(DataFwiO)
admin.site.register(Ray)
admin.site.register(Ray2)
# admin.site.register(ET0o)
admin.site.register(Envdata)
admin.site.register(wsd)
# admin.site.register(ET0DR)
# admin.site.register(ET0DRv)
admin.site.register(debitcap)
admin.site.register(ev_batt)
admin.site.register(ev_batt2)
admin.site.register(ev_batt3)
admin.site.register(rs_temp)
admin.site.register(rs_sol)
admin.site.register(DeviceData)
admin.site.register(greenHouse)
admin.site.register(WeatherData)
# admin.site.register(ETODR_FAO56)
# admin.site.register(ETOSensCap_FAO56)
# admin.site.register(ETODRV_FAO56)

@admin.register(SensorData)
class SensorDataAdmin(admin.ModelAdmin):
    list_display  = ('temperature', 'humidity', 'timestamp')
    ordering      = ('-timestamp',)


class BaseET0Admin(admin.ModelAdmin):
    ordering = ("-Time_Stamp",)      # ✅ tri par date
    date_hierarchy = "Time_Stamp"    # ✅ navigation calendrier
    list_per_page = 50
    list_filter = ("Time_Stamp",)
    search_fields = ("Time_Stamp",)

@admin.register(ET0o)
class ET0oAdmin(BaseET0Admin):
    list_display = ("Time_Stamp", "value", "Tavg", "Tmax", "Tmin", "WSavg", "Raym")

@admin.register(ET0DR)
class ET0DRAdmin(BaseET0Admin):
    list_display = ("Time_Stamp", "value", "Tavg", "Tmax", "Tmin", "WSavg", "Raym")

@admin.register(ET0DRv)
class ET0DRvAdmin(BaseET0Admin):
    list_display = ("Time_Stamp", "value", "Tavg", "Tmax", "Tmin", "WSavg", "Raym")

@admin.register(ETODR_FAO56)
class ETODRFAO56Admin(BaseET0Admin):
    list_display = ("Time_Stamp", "value", "Tavg", "Tmax", "Tmin", "WSavg", "Raym")

@admin.register(ETOSensCap_FAO56)
class ETOSSensCapFAO56Admin(BaseET0Admin):
    list_display = ("Time_Stamp", "value", "Tavg", "Tmax", "Tmin", "WSavg", "Raym")

@admin.register(ETODRV_FAO56)
class ETODRVFAO56Admin(BaseET0Admin):
    list_display = ("Time_Stamp", "value", "Tavg", "Tmax", "Tmin", "WSavg", "Raym")