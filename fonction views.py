# Create your views here.
import datetime
import math
from django.utils.timezone import localtime
import numpy as np
import pandas as pd
from django.utils import timezone
from django.db.models import Max, Min, Sum, Avg
from django.http import HttpResponseRedirect
from django.shortcuts import render,HttpResponse
from django.views.generic import TemplateView
import paho.mqtt.client as mqtt
from collections import defaultdict
from django.utils.timezone import make_aware
from .models import *
import requests
import json
from .models import SenseCAPT1000



from collections import Counter
from django.http import JsonResponse
# import penmon as pm
#programmation chirpstack
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import logging

logger = logging.getLogger(__name__)

WS_DEVEUI_OPENSNZ = '57c32e0eb4160806'
valve_eui= '2ee5270e481778ff'
black_device_eui= '13e08e2951742243'
red_device_eui= '6f8e5550f7ec89e9'
npk_device_eui= 'fe86cac7b467a956'
pyranometre = '71ca6b16b8e4ac42'
pyranometre_jaune = '18362e0eb4160834'
WsSENSECAP_WeatherStation = '2cf7f1c04430038d'
module_drajino = 'a84041834189a939'
pyraGV = 'a84041fc4188657b'

Capteurdesol ='a84041d10858e027'
#fin progra

def aqi(request):
    context={}
    return render(request,"tab.html",context)

""" calcul et
"""
import datetime
from datetime import timedelta

from django.shortcuts import render
from django.utils import timezone
from django.db import transaction
from django.db.models import Avg, Min, Max

##########################################

def calculate_duration_and_volume(current_record):
    if current_record.valve != 1:
        return
    previous_records = Makerfabs.objects.filter(
        Time_Stamp__lt=current_record.Time_Stamp
    ).order_by('-Time_Stamp')
    open_start = None
    for record in previous_records:
        if record.valve == 0:
            open_start = record.Time_Stamp
        elif record.valve == 1:
            break
    if open_start is None:
        return
    duration_seconds = (current_record.Time_Stamp - open_start).total_seconds()
    flow_pulse = current_record.debit * 450 / 60
    volume = (flow_pulse * duration_seconds) / 450
    current_record.durée = duration_seconds
    current_record.Volume = round(volume, 3)
    current_record.save()
###########################################
def day_range(target_date):
    """
    Retourne [start, end) pour la date cible en timezone courante.
    """
    tz = timezone.get_current_timezone()
    start = tz.localize(datetime.datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0))
    end = start + timedelta(days=1)
    return start, end


def fetch_data_for_eto(target_date=None):
    if target_date is None:
        target_date = timezone.localtime(timezone.now()).date() - timedelta(days=1)

    start_day, end_day = day_range(target_date)

    qs_data2 = Data2.objects.filter(Time_Stamp__range=(start_day, end_day))
    if not qs_data2.exists():
        return None

    weather_data = qs_data2.aggregate(
        temp_avg=Avg('Temp'),
        hum_avg=Avg('Hum'),
        wind_avg=Avg('Wind_Speed'),
        pressure_avg=Avg('Pr'),
        temp_min=Min('Temp'),
        temp_max=Max('Temp'),
        hum_min=Min('Hum'),
        hum_max=Max('Hum'),
    )

    if weather_data["pressure_avg"] is None:
        return None

    wind_speed_avg = (
        round(weather_data['wind_avg'] / 3.6, 2)
        if weather_data['wind_avg'] is not None
        else None
    )

    hourly_ray = []
    for hour in range(24):
        interval_start = start_day + timedelta(hours=hour)
        interval_end = interval_start + timedelta(hours=1)
        avg_ray = Ray2.objects.filter(DateRay__range=(interval_start, interval_end)).aggregate(avg=Avg('Ray'))['avg']
        if avg_ray is not None:
            hourly_ray.append(avg_ray)

    if not hourly_ray:
        return None

    radiation_sum = sum(hourly_ray)
    day_of_year = start_day.timetuple().tm_yday

    return {
        'altitude': 532,
        'latitude': 33.51,
        'day_of_year': day_of_year,
        'pressure': weather_data['pressure_avg'],
        'humidity_max': weather_data['hum_max'],
        'humidity_min': weather_data['hum_min'],
        'temp_avg': weather_data['temp_avg'],
        'temp_max': weather_data['temp_max'],
        'temp_min': weather_data['temp_min'],
        'radiation_sum': radiation_sum,
        'wind_speed_avg': wind_speed_avg
    }

def fetch_data_for_etoDR(target_date=None):
    if target_date is None:
        target_date = timezone.localtime(timezone.now()).date() - timedelta(days=1)

    start_day, end_day = day_range(target_date)

    qs_wsd = wsd.objects.filter(Time_Stamp__range=(start_day, end_day))
    if not qs_wsd.exists():
        return None

    weather_data = qs_wsd.aggregate(
        temp_avg=Avg('TEM'),
        temp_min=Min('TEM'),
        temp_max=Max('TEM'),
        humidity_min=Min('HUM'),
        humidity_max=Max('HUM'),
        wind_avg=Avg('wind_speed'),
    )

    pressure = Data2.objects.filter(Time_Stamp__range=(start_day, end_day)).aggregate(pressure=Avg('Pr'))['pressure']
    if pressure is None:
        return None

    hourly_illum = []
    for hour in range(24):
        interval_start = start_day + timedelta(hours=hour)
        interval_end = interval_start + timedelta(hours=1)

        val = qs_wsd.filter(Time_Stamp__range=(interval_start, interval_end)).aggregate(avg=Avg('illumination'))['avg']
        if val is not None:
            hourly_illum.append(val)

    if not hourly_illum:
        return None

    radiation_sum = sum(hourly_illum)

    wind_speed_avg = (
        round(weather_data['wind_avg'] / 3.6, 2)
        if weather_data['wind_avg'] is not None
        else None
    )

    day_of_year = start_day.timetuple().tm_yday

    return {
        'altitude': 532,
        'latitude': 33.51,
        'day_of_year': day_of_year,
        'pressure': pressure,
        'humidity_max': weather_data['humidity_max'],
        'humidity_min': weather_data['humidity_min'],
        'temp_avg': weather_data['temp_avg'],
        'temp_max': weather_data['temp_max'],
        'temp_min': weather_data['temp_min'],
        'radiation_sum': radiation_sum,
        'wind_speed_avg': wind_speed_avg,
    }

def fetch_data_for_etoDRv(target_date=None):
    if target_date is None:
        target_date = timezone.localtime(timezone.now()).date() - timedelta(days=1)

    start_day, end_day = day_range(target_date)

    qs_wsd = wsd.objects.filter(Time_Stamp__range=(start_day, end_day))
    if not qs_wsd.exists():
        return None

    weather_data = qs_wsd.aggregate(
        tem_avg=Avg('TEM'),
        tem_min=Min('TEM'),
        tem_max=Max('TEM'),
        hum_min=Min('HUM'),
        hum_max=Max('HUM'),
        wind_avg=Avg('wind_speed'),
    )

    pressure = Data2.objects.filter(Time_Stamp__range=(start_day, end_day)).aggregate(pr=Avg('Pr'))['pr']
    if pressure is None:
        return None

    hourly_ray = []
    for hour in range(24):
        interval_start = start_day + timedelta(hours=hour)
        interval_end = interval_start + timedelta(hours=1)
        avg_ray = Ray2.objects.filter(DateRay__range=(interval_start, interval_end)).aggregate(avg=Avg('Ray'))['avg']
        if avg_ray is not None:
            hourly_ray.append(avg_ray)

    if not hourly_ray:
        return None

    radiation_sum = sum(hourly_ray)

    wind_speed_avg = (
        round(weather_data['wind_avg'] / 3.6, 2)
        if weather_data['wind_avg'] is not None
        else None
    )

    required = [
        weather_data["tem_avg"], weather_data["tem_min"], weather_data["tem_max"],
        weather_data["hum_min"], weather_data["hum_max"], wind_speed_avg, pressure
    ]
    if any(v is None for v in required):
        return None

    day_of_year = start_day.timetuple().tm_yday

    return {
        'altitude': 532,
        'latitude': 33.51,
        'day_of_year': day_of_year,
        'pressure': pressure,
        'humidity_max': weather_data['hum_max'],
        'humidity_min': weather_data['hum_min'],
        'temp_avg': weather_data['tem_avg'],
        'temp_max': weather_data['tem_max'],
        'temp_min': weather_data['tem_min'],
        'radiation_sum': radiation_sum,
        'wind_speed_avg': wind_speed_avg
    }

def ts_0101(target_date):
    naive = datetime.datetime.combine(target_date, datetime.time(1, 1))
    return timezone.make_aware(naive, timezone.get_current_timezone())


def backfill_et0(request):
    """
    URL: /backfill-et0/?days=30
    - calcule les jours manquants
    - ignore si données None
    - enregistre à 01:01 sur la date du jour concerné
    """

    # nb de jours (par défaut 7)
    try:
        days_back = int(request.GET.get("days", "3"))
    except ValueError:
        days_back = 3
    days_back = max(1, min(days_back, 365))

    today = timezone.localtime(timezone.now()).date()

    logs = []

    # Backfill du plus ancien vers le plus récent
    for i in range(days_back, -1, -1):
        target_date = today - timedelta(days=i)
        logs.append(f"📅 Backfill {target_date}")

        # -------- ET0o ----------
        if not ET0o.objects.filter(Time_Stamp__date=target_date).exists():
            data = fetch_data_for_eto(target_date=target_date)
            if data is None:
                logs.append("⛔ ET0 ignoré (données None)")
            else:
                try:
                    ETO(target_date=target_date)  # ✅ calcule sur la date cible
                    logs.append("✅ ET0 calculé")
                except Exception as e:
                    logs.append(f"⛔ ET0 erreur: {e}")
        else:
            logs.append("✅ ET0 déjà présent")

        # -------- ET0DR ----------
        if not ET0DR.objects.filter(Time_Stamp__date=target_date).exists():
            data = fetch_data_for_etoDR(target_date=target_date)
            if data is None:
                logs.append("⛔ ET0 Dragino ignoré (données None)")
            else:
                try:
                    ETODR(target_date=target_date)
                    logs.append("✅ ET0 Dragino calculé")
                except Exception as e:
                    logs.append(f"⛔ ET0 Dragino erreur: {e}")
        else:
            logs.append("✅ ET0 Dragino déjà présent")

        # -------- ET0DRv ----------
        if not ET0DRv.objects.filter(Time_Stamp__date=target_date).exists():
            data = fetch_data_for_etoDRv(target_date=target_date)
            if data is None:
                logs.append("⛔ ET0 Visiogreen ignoré (données None)")
            else:
                try:
                    ETODRv(target_date=target_date)
                    logs.append("✅ ET0 Visiogreen calculé")
                except Exception as e:
                    logs.append(f"⛔ ET0 Visiogreen erreur: {e}")
        else:
            logs.append("✅ ET0 Visiogreen déjà présent")

        # -------- ETODR_FAO56 ----------
        if not ETODR_FAO56.objects.filter(Time_Stamp__date=target_date).exists():
            data = fetch_data_for_etoDR(target_date=target_date)
            if data is None:
                logs.append("⛔ ET0 DR FAO56 ignoré (données None)")
            else:
                try:
                    ETODR_FAO56_DR(target_date=target_date)
                    logs.append("✅ ET0 DR FAO56 calculé")
                except Exception as e:
                    logs.append(f"⛔ ET0 DR FAO56 erreur: {e}")
        else:
            logs.append("✅ ET0 DR FAO56 déjà présent")

        # -------- ETOSensCap_FAO56 ----------
        if not ETOSensCap_FAO56.objects.filter(Time_Stamp__date=target_date).exists():
            data = fetch_data_for_eto(target_date=target_date)
            if data is None:
                logs.append("⛔ ET0 S FAO56 ignoré (données None)")
            else:
                try:
                    ETOS_FAO56_S(target_date=target_date)
                    logs.append("✅ ET0 S FAO56 calculé")
                except Exception as e:
                    logs.append(f"⛔ ET0 S FAO56 erreur: {e}")
        else:
            logs.append("✅ ET0 S FAO56 déjà présent")

        # -------- ETODRV_FAO56 ----------
        if not ETODRV_FAO56.objects.filter(Time_Stamp__date=target_date).exists():
            data = fetch_data_for_etoDRv(target_date=target_date)
            if data is None:
                logs.append("⛔ ET0 DRV FAO56 ignoré (données None)")
            else:
                try:
                    ETODRV_FAO56_DRV(target_date=target_date)
                    logs.append("✅ ET0 DRV FAO56 calculé")
                except Exception as e:
                    logs.append(f"⛔ ET0 DRV FAO56 erreur: {e}")
        else:
            logs.append("✅ ET0 DRV FAO56 déjà présent")

    return render(request, "jobles.html", {
        "message": f"Backfill terminé ✅ (jours: {days_back})",
        "logs": logs,
        "days_back": days_back,
    })


""" fin bat"""
#batterie
def bat11(request):
    one_day_ago = (datetime.datetime.today()).replace(hour=0,minute=0,second=0,microsecond=0)
    print("oui ......",one_day_ago)
    labels = []
    dataa = []
    all = Ray2.objects.filter(DateRay__gte=one_day_ago)
    # print("all", all)
    for i in all:
        labels.append((i.DateRay).strftime("%Y-%m-%d %H:%M:%S"))
        # print("labels", labels)
        dataa.append(i.Bat)
    lst = Data.objects.last()
    context = {'all': all, 'lst': lst, 'labels': labels, 'dataa': dataa}
    return render(request, "batt/bat1.html", context)

def bat31(request):
    one_day_ago = (datetime.datetime.now() - datetime.timedelta(days=3)).replace(hour=0,minute=0,second=0,microsecond=0)
    labels = []
    dataa = []
    all = Ray2.objects.filter(DateRay__gte=one_day_ago)
    print("all", all)
    for i in all:
        labels.append((i.DateRay).strftime("%Y-%m-%d %H:%M:%S"))
        # print("labels", labels)
        dataa.append(i.Bat)
    lst = Data.objects.last()
    context = {'all': all, 'lst': lst, 'labels': labels, 'dataa': dataa}
    return render(request, "batt/bat3.html", context)

def bat71(request):
    one_day_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).replace(hour=0,minute=0,second=0,microsecond=0)
    labels = []
    dataa = []
    all = Ray2.objects.filter(DateRay__gte=one_day_ago)
    print("all", all)
    for i in all:
        labels.append((i.DateRay).strftime("%Y-%m-%d %H:%M:%S"))
        # print("labels", labels)
        dataa.append(i.Bat)
    lst = Data.objects.last()
    context = {'all': all, 'lst': lst, 'labels': labels, 'dataa': dataa}
    return render(request, "batt/bat7.html", context)

def bat151(request):
    one_day_ago = (datetime.datetime.now() - datetime.timedelta(days=15)).replace(hour=0,minute=0,second=0,microsecond=0)
    labels = []
    dataa = []
    all = Ray2.objects.filter(DateRay__gte=one_day_ago)
    # print("all", all)
    for i in all:
        labels.append((i.DateRay).strftime("%Y-%m-%d %H:%M:%S"))
        # print("labels", labels)
        dataa.append(i.Bat)
    lst = Data.objects.last()
    context = {'all': all, 'lst': lst, 'labels': labels, 'dataa': dataa}
    return render(request, "batt/bat15.html", context)
""" fin bat"""


def fwi0(request):
    one_day_ago = (datetime.datetime.now() - datetime.timedelta(days=15)).replace(hour=0,minute=0,second=0,microsecond=0)
    labels = []
    dataa = []
    all = DataFwiO.objects.filter(Time_Stamp__gte=one_day_ago)
    for i in all:
        labels.append((i.Time_Stamp).strftime("%Y-%m-%d "))
        dataa.append(i.fwi)

    context = {'all': all, 'labels': labels, 'dataa': dataa}
    return render(request, "fwi/fwi.html", context)

"""
def chartsal(request):
    tab=CapSol.objects.all()
    labels = []
    dataa = []
    for data in tab:
        labels.append((data.dt).strftime("%Y-%m-%d %H:%M:%S"))
        dataa.append(data.Sal)
        print("labels0", type(labels))
    if (request.method == "POST"):
        labels.clear()
        dataa.clear()

        fromdate = request.POST.get('startdate')
        # print(type(datetime.datetime.now()))
        print("fromdate")
        print(fromdate)
        todate = request.POST.get('enddate')
        print("todate")
        print(todate)
        first = CapSol.objects.first()
        print("first date", str(first.dt))
        lastdate = CapSol.objects.last()
        print("last date", str(lastdate.dt))
        if fromdate != "" and todate != "":
            # to = datetime.datetime.strptime(todate, '%Y-%m-%d')+datetime.timedelta(days=1)
            to = datetime.datetime.strptime(todate, '%Y-%m-%d') + datetime.timedelta(days=1)
            print("to", to)
            # fromdate = datetime.datetime("07-07")
            created_documents5 = CapSol.objects.filter(dt__range=[fromdate, to]).order_by('dt')
            print("created_documents5", created_documents5)
            for data in created_documents5:
                labels.append((data.dt).strftime("%d %b %Y %H:%M:%S"))
                dataa.append(data.Sal)

                print("labelfiltter", labels)
                # return HttpResponseRedirect('/')
            # print("labelfiltter",labels)
        if fromdate == "":
            fromdate = first.dt

        if todate == "":
            to = (lastdate.dt) + datetime.timedelta(days=1)
            todate = to + datetime.timedelta(days=1)
            labels.clear()
            dataa.clear()

            created_documents6 = CapSol.objects.filter(dt__range=[fromdate, todate]).order_by('id')
            print("created_documents6", created_documents6)

            for data in created_documents6:
                labels.append((data.dt).strftime("%d %b %Y %H:%M:%S"))
                dataa.append(data.Sal)

                print("lab", labels)
                return HttpResponseRedirect('/Chartsal')

            print("todate", type(todate))

    context={'tab':tab,'labels':labels,'dataa':dataa}
    return render(request,"chartssal.html",context)
"""
# def chartN(request):
#     tab=CapSol.objects.all()
#     labels = []
#     dataa = []
#     for data in tab:
#         labels.append((data.dt).strftime("%Y-%m-%d %H:%M:%S"))
#         dataa.append(data.N)
#         print("labels0", type(labels))
#     if (request.method == "POST"):
#         labels.clear()
#         dataa.clear()

#         fromdate = request.POST.get('startdate')
#         # print(type(datetime.datetime.now()))
#         print("fromdate")
#         print(fromdate)
#         todate = request.POST.get('enddate')
#         print("todate")
#         print(todate)
#         first = CapSol.objects.first()
#         print("first date", str(first.dt))
#         lastdate = CapSol.objects.last()
#         print("last date", str(lastdate.dt))
#         if fromdate != "" and todate != "":
#             # to = datetime.datetime.strptime(todate, '%Y-%m-%d')+datetime.timedelta(days=1)
#             to = datetime.datetime.strptime(todate, '%Y-%m-%d') + datetime.timedelta(days=1)
#             print("to", to)
#             # fromdate = datetime.datetime("07-07")
#             created_documents5 = CapSol.objects.filter(dt__range=[fromdate, to]).order_by('dt')
#             print("created_documents5", created_documents5)
#             for data in created_documents5:
#                 labels.append((data.dt).strftime("%d %b %Y %H:%M:%S"))
#                 dataa.append(data.N)

#                 print("labelfiltter", labels)
#                 # return HttpResponseRedirect('/')
#             # print("labelfiltter",labels)
#         if fromdate == "":
#             fromdate = first.dt

#         if todate == "":
#             to = (lastdate.dt) + datetime.timedelta(days=1)
#             todate = to + datetime.timedelta(days=1)
#             labels.clear()
#             dataa.clear()

#             created_documents6 = CapSol.objects.filter(dt__range=[fromdate, todate]).order_by('id')
#             print("created_documents6", created_documents6)

#             for data in created_documents6:
#                 labels.append((data.dt).strftime("%d %b %Y %H:%M:%S"))
#                 dataa.append(data.N)

#                 print("lab", labels)
#                 return HttpResponseRedirect('/ChartN')

#             print("todate", type(todate))

#     context={'tab':tab,'labels':labels,'dataa':dataa}
#     return render(request,"chartsN.html",context)

# def chartP(request):
#     tab=CapSol.objects.all()
#     labels = []
#     dataa = []
#     for data in tab:
#         labels.append((data.dt).strftime("%Y-%m-%d %H:%M:%S"))
#         dataa.append(data.P)
#         print("labels0", type(labels))
#     if (request.method == "POST"):
#         labels.clear()
#         dataa.clear()

#         fromdate = request.POST.get('startdate')
#         # print(type(datetime.datetime.now()))
#         print("fromdate")
#         print(fromdate)
#         todate = request.POST.get('enddate')
#         print("todate")
#         print(todate)
#         first = CapSol.objects.first()
#         print("first date", str(first.dt))
#         lastdate = CapSol.objects.last()
#         print("last date", str(lastdate.dt))
#         if fromdate != "" and todate != "":
#             # to = datetime.datetime.strptime(todate, '%Y-%m-%d')+datetime.timedelta(days=1)
#             to = datetime.datetime.strptime(todate, '%Y-%m-%d') + datetime.timedelta(days=1)
#             print("to", to)
#             # fromdate = datetime.datetime("07-07")
#             created_documents5 = CapSol.objects.filter(dt__range=[fromdate, to]).order_by('dt')
#             print("created_documents5", created_documents5)
#             for data in created_documents5:
#                 labels.append((data.dt).strftime("%d %b %Y %H:%M:%S"))
#                 dataa.append(data.P)

#                 print("labelfiltter", labels)
#                 # return HttpResponseRedirect('/')
#             # print("labelfiltter",labels)
#         if fromdate == "":
#             fromdate = first.dt

#         if todate == "":
#             to = (lastdate.dt) + datetime.timedelta(days=1)
#             todate = to + datetime.timedelta(days=1)
#             labels.clear()
#             dataa.clear()

#             created_documents6 = CapSol.objects.filter(dt__range=[fromdate, todate]).order_by('id')
#             print("created_documents6", created_documents6)

#             for data in created_documents6:
#                 labels.append((data.dt).strftime("%d %b %Y %H:%M:%S"))
#                 dataa.append(data.P)

#                 print("lab", labels)
#                 return HttpResponseRedirect('/ChartP')

#             print("todate", type(todate))

#     context={'tab':tab,'labels':labels,'dataa':dataa}
#     return render(request,"chartsP.html",context)

# def chartK(request):
#     tab=CapSol.objects.all()
#     labels = []
#     dataa = []
#     for data in tab:
#         labels.append((data.dt).strftime("%Y-%m-%d %H:%M:%S"))
#         dataa.append(data.K)
#         print("labels0", type(labels))
#     if (request.method == "POST"):
#         labels.clear()
#         dataa.clear()

#         fromdate = request.POST.get('startdate')
#         # print(type(datetime.datetime.now()))
#         print("fromdate")
#         print(fromdate)
#         todate = request.POST.get('enddate')
#         print("todate")
#         print(todate)
#         first = CapSol.objects.first()
#         print("first date", str(first.dt))
#         lastdate = CapSol.objects.last()
#         print("last date", str(lastdate.dt))
#         if fromdate != "" and todate != "":
#             # to = datetime.datetime.strptime(todate, '%Y-%m-%d')+datetime.timedelta(days=1)
#             to = datetime.datetime.strptime(todate, '%Y-%m-%d') + datetime.timedelta(days=1)
#             print("to", to)
#             # fromdate = datetime.datetime("07-07")
#             created_documents5 = CapSol.objects.filter(dt__range=[fromdate, to]).order_by('dt')
#             print("created_documents5", created_documents5)
#             for data in created_documents5:
#                 labels.append((data.dt).strftime("%d %b %Y %H:%M:%S"))
#                 dataa.append(data.K)

#                 print("labelfiltter", labels)
#                 # return HttpResponseRedirect('/')
#             # print("labelfiltter",labels)
#         if fromdate == "":
#             fromdate = first.dt

#         if todate == "":
#             to = (lastdate.dt) + datetime.timedelta(days=1)
#             todate = to + datetime.timedelta(days=1)
#             labels.clear()
#             dataa.clear()

#             created_documents6 = CapSol.objects.filter(dt__range=[fromdate, todate]).order_by('id')
#             print("created_documents6", created_documents6)

#             for data in created_documents6:
#                 labels.append((data.dt).strftime("%d %b %Y %H:%M:%S"))
#                 dataa.append(data.K)

#                 print("lab", labels)
#                 return HttpResponseRedirect('/ChartK')

#             print("todate", type(todate))

#     context={'tab':tab,'labels':labels,'dataa':dataa}
#     return render(request,"chartsK.html",context)

# def chartbat(request):
#     tab=CapSol.objects.all()
#     labels = []
#     dataa = []
#     for data in tab:
#         labels.append((data.dt).strftime("%Y-%m-%d %H:%M:%S"))
#         dataa.append(data.Bat)
#         print("labels0", type(labels))
#     if (request.method == "POST"):
#         labels.clear()
#         dataa.clear()

#         fromdate = request.POST.get('startdate')
#         # print(type(datetime.datetime.now()))
#         print("fromdate")
#         print(fromdate)
#         todate = request.POST.get('enddate')
#         print("todate")
#         print(todate)
#         first = CapSol.objects.first()
#         print("first date", str(first.dt))
#         lastdate = CapSol.objects.last()
#         print("last date", str(lastdate.dt))
#         if fromdate != "" and todate != "":
#             # to = datetime.datetime.strptime(todate, '%Y-%m-%d')+datetime.timedelta(days=1)
#             to = datetime.datetime.strptime(todate, '%Y-%m-%d') + datetime.timedelta(days=1)
#             print("to", to)
#             # fromdate = datetime.datetime("07-07")
#             created_documents5 = CapSol.objects.filter(dt__range=[fromdate, to]).order_by('dt')
#             print("created_documents5", created_documents5)
#             for data in created_documents5:
#                 labels.append((data.dt).strftime("%d %b %Y %H:%M:%S"))
#                 dataa.append(data.Bat)

#                 print("labelfiltter", labels)
#                 # return HttpResponseRedirect('/')
#             # print("labelfiltter",labels)
#         if fromdate == "":
#             fromdate = first.dt

#         if todate == "":
#             to = (lastdate.dt) + datetime.timedelta(days=1)
#             todate = to + datetime.timedelta(days=1)
#             labels.clear()
#             dataa.clear()

#             created_documents6 = CapSol.objects.filter(dt__range=[fromdate, todate]).order_by('id')
#             print("created_documents6", created_documents6)

#             for data in created_documents6:
#                 labels.append((data.dt).strftime("%d %b %Y %H:%M:%S"))
#                 dataa.append(data.Bat)

#                 print("lab", labels)
#                 return HttpResponseRedirect('/Chartec')

#             print("todate", type(todate))

#     context={'tab':tab,'labels':labels,'dataa':dataa}
#     return render(request,"chartsbat.html",context)

from datetime import datetime, timezone as dt_timezone


def download_temp_ray_2025(request):

    data_temp = Data2.objects.filter(
        Time_Stamp__year=2025
    ).values_list("Time_Stamp", "Temp")

    data_ray = Ray2.objects.filter(
        DateRay__year=2025
    ).values_list("DateRay", "Ray")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="temperature_rayonnement_2025.csv"'

    writer = csv.writer(response)
    writer.writerow(["Date_Temp", "Temperature", "Date_Ray", "Rayonnement"])

    temp_list = list(data_temp)
    ray_list = list(data_ray)

    max_len = max(len(temp_list), len(ray_list))

    for i in range(max_len):
        t = temp_list[i] if i < len(temp_list) else ("", "")
        r = ray_list[i] if i < len(ray_list) else ("", "")
        writer.writerow([t[0], t[1], r[0], r[1]])

    return response

def fwi():
    global temp, rhum, prcp, wind, ffmc0, dc0, dmc0, ffmc, dmc, isi, bui, fwi, i, jprcp
    global DataFWI

    class FWICLASS:
        def __init__(self, temp, rhum, wind, prcp):
            self.h = rhum
            self.t = temp
            self.w = wind
            self.p = prcp

        def FFMCcalc(self, ffmc0):
            mo = (147.2 * (101.0 - ffmc0)) / (59.5 + ffmc0)  # *Eq. 1*#
            if (self.p > 0.5):
                rf = self.p - 0.5  # *Eq. 2*#
                if (mo > 150.0):
                    mo = (mo + 42.5 * rf * math.exp(-100.0 / (251.0 - mo)) * (1.0 - math.exp(-6.93 / rf))) + (
                            .0015 * (mo - 150.0) ** 2) * math.sqrt(rf)  # *Eq. 3b*#
                elif mo <= 150.0:
                    mo = mo + 42.5 * rf * math.exp(-100.0 / (251.0 - mo)) * (1.0 - math.exp(-6.93 / rf))  # *Eq. 3a*#
                if (mo > 250.0):
                    mo = 250.0
            ed = .942 * (self.h ** .679) + (11.0 * math.exp((self.h - 100.0) / 10.0)) + 0.18 * (21.1 - self.t) * (
                    1.0 - 1.0 / math.exp(.1150 * self.h))  # *Eq. 4*#
            if (mo < ed):
                ew = .618 * (self.h ** .753) + (10.0 * math.exp((self.h - 100.0) / 10.0)) + .18 * (21.1 - self.t) * (
                        1.0 - 1.0 / math.exp(.115 * self.h))
                if (mo <= ew):
                    kl = .424 * (1.0 - ((100.0 - self.h) / 100.0) ** 1.7) + (.0694 * math.sqrt(self.w)) * (
                            1.0 - ((100.0 - self.h) / 100.0) ** 8)  # *Eq. 7a*#
                    kw = kl * (.581 * math.exp(.0365 * self.t))  # *Eq. 7b*#
                    m = ew - (ew - mo) / 10.0 ** kw  # *Eq. 9*#
                elif mo > ew:
                    m = mo
            elif (mo == ed):
                m = mo
            elif mo > ed:
                kl = .424 * (1.0 - (self.h / 100.0) ** 1.7) + (.0694 * math.sqrt(self.w)) * (
                        1.0 - (self.h / 100.0) ** 8)  # *Eq. 6a*#
                kw = kl * (.581 * math.exp(.0365 * self.t))  # *Eq. 6b*#
                m = ed + (mo - ed) / 10.0 ** kw  # *Eq. 8*#
            ffmc = (59.5 * (250.0 - m)) / (147.2 + m)
            if (ffmc > 101.0):
                ffmc = 101.0
            if (ffmc <= 0.0):
                ffmc = 0.0
            return ffmc

        def DMCcalc(self, dmc0, mth):
            el = [6.5, 7.5, 9.0, 12.8, 13.9, 13.9, 12.4, 10.9, 9.4, 8.0, 7.0, 6.0]
            t = self.t
            if (t < -1.1):
                t = -1.1
            rk = 1.894 * (t + 1.1) * (100.0 - self.h) * (el[mth - 1] * 0.0001)
            if self.p > 1.5:
                ra = self.p
                rw = 0.92 * ra - 1.27
                wmi = 20.0 + 280.0 / math.exp(0.023 * dmc0)
                if dmc0 <= 33.0:
                    b = 100.0 / (0.5 + 0.3 * dmc0)
                elif dmc0 > 33.0:
                    if dmc0 <= 65.0:
                        b = 14.0 - 1.3 * math.log(dmc0)
                    elif dmc0 > 65.0:
                        b = 6.2 * math.log(dmc0) - 17.2
                wmr = wmi + (1000 * rw) / (48.77 + b * rw)
                pr = 43.43 * (5.6348 - math.log(wmr - 20.0))
            elif self.p <= 1.5:
                pr = dmc0
            if (pr < 0.0):
                pr = 0.0
            dmc = pr + rk
            if (dmc <= 1.0):
                dmc = 1.0
            return dmc

        def DCcalc(self, dc0, mth):
            fl = [-1.6, -1.6, -1.6, 0.9, 3.8, 5.8, 6.4, 5.0, 2.4, 0.4, -1.6, -1.6]
            t = self.t
            if (t < -2.8):
                t = -2.8
            pe = (0.36 * (t + 2.8) + fl[mth - 1]) / 2
            if pe <= 0.0:
                pe = 0.0
            # *Eq. 22*#
            if (self.p > 2.8):
                ra = self.p
                rw = 0.83 * ra - 1.27
                smi = 800.0 * math.exp(-dc0 / 400.0)  # *Eq. 19*#
                dr = dc0 - 400.0 * math.log(1.0 + ((3.937 * rw) / smi))  # *Eqs. 20 and 21*#
                if (dr > 0.0):
                    dc = dr + pe
            elif self.p <= 2.8:
                dc = dc0 + pe
            return dc

        def ISIcalc(self, ffmc):
            mo = 147.2 * (101.0 - ffmc) / (59.5 + ffmc)
            ff = 19.115 * math.exp(mo * -0.1386) * (1.0 + (mo ** 5.31) / 49300000.0)
            isi = ff * math.exp(0.05039 * self.w)
            return isi

        def BUIcalc(self, dmc, dc):
            if dmc <= 0.4 * dc:
                bui = (0.8 * dc * dmc) / (dmc + 0.4 * dc)
            else:
                bui = dmc - (1.0 - 0.8 * dc / (dmc + 0.4 * dc)) * (0.92 + (0.0114 * dmc) ** 1.7)
            if bui < 0.0:
                bui = 0.0
            return bui

        def FWIcalc(self, isi, bui):
            if bui <= 80.0:
                bb = 0.1 * isi * (0.626 * bui ** 0.809 + 2.0)

            else:
                bb = 0.1 * isi * (1000.0 / (25. + 108.64 / math.exp(0.023 * bui)))
            if (bb <= 1.0):
                fwi = bb
            else:
                fwi = math.exp(2.72 * (0.434 * math.log(bb)) ** 0.647)
            return fwi


    from django.utils import timezone

    def main():
        # ✅ On utilise timezone.now() pour éviter les problèmes UTC/local
        now = timezone.now()
        one_day_ago = now - datetime.timedelta(days=1)

        print("Date de référence :", one_day_ago.date())

        # ✅ Récupération des mesures météo de la veille
        posts = Data2.objects.filter(Time_Stamp__date=one_day_ago.date())
        print("Mesures récupérées :", posts.count())

        if not posts.exists():
            print("Aucune donnée météo pour la journée précédente.")
            return

        # ✅ Moyennes calculées
        wind = round(posts.aggregate(Avg('Wind_Speed'))['Wind_Speed__avg'] or 0.0, 2)
        temp = round(posts.aggregate(Avg('Temp'))['Temp__avg'] or 0.0, 2)
        rhum = round(min(posts.aggregate(Avg('Hum'))['Hum__avg'] or 0.0, 100.0), 2)
        prcp = round(posts.aggregate(Avg('Rain'))['Rain__avg'] or 0.0, 2)

        print("Température :", temp, "Humidité :", rhum, "Vent :", wind, "Pluie :", prcp)

        # ✅ Recherche des indices FWI existants pour la veille
        initfw = DataFwi.objects.filter(Time_Stamp__date=one_day_ago.date()).last()

        if initfw:
            ffmc0 = initfw.ffmc
            dmc0 = initfw.dmc
            dc0 = initfw.dc
            print("FWI initial récupéré :", ffmc0, dmc0, dc0)
        else:
            print("Pas de données FWI initiales pour la journée précédente. Valeurs par défaut appliquées.")
            ffmc0 = 85.0
            dmc0 = 6.0
            dc0 = 15.0

        # ✅ Calcul des indices
        mth = now.month
        fwisystem = FWICLASS(temp, rhum, wind, prcp)

        ffmc = fwisystem.FFMCcalc(ffmc0)
        dmc = fwisystem.DMCcalc(dmc0, mth)
        dc = fwisystem.DCcalc(dc0, mth)
        isi = fwisystem.ISIcalc(ffmc)
        bui = fwisystem.BUIcalc(dmc, dc)
        fwi = fwisystem.FWIcalc(isi, bui)

        # ✅ Enregistrement avec timezone.now()
        DataFwi.objects.create(
            ffmc=round(ffmc, 1),
            dmc=round(dmc, 1),
            dc=round(dc, 1),
            isi=round(isi, 1),
            bui=round(bui, 1),
            fwi=round(fwi, 2),
            Time_Stamp=now
        )
        print("Nouveaux indices FWI enregistrés :", ffmc, dmc, dc, isi, bui, fwi)


    main()

def weatherS(request):
    lst=Ws.objects.last()
    t = round(lst.Temperature,1)
    h = round(lst.Humidity)
    v = round(lst.Vent,1)
    r = round(lst.Rafale,1)
    p = round(lst.Pluv,1)

    lstR=Ray.objects.last()
    ray = round(lstR.Ray, 1)
    print(ray)
    lstet = ET0.objects.last()
    lstfwi= DataFwi.objects.last()

    # exemple()
    # FWI
    one_day_ago = datetime.datetime.now() - datetime.timedelta(days=1)
    posts = Ws.objects.filter(date__gte=one_day_ago)
    print("................................. weeather station visio green .................................")

    context={'lst':lst,'t':t,'h':h,'v':v,'r':r,'p':p,"lstet":lstet,'lstfwi':lstfwi,'ray':ray,'lstR':lstR}
    return render(request,"stationvisio.html",context)


from django.shortcuts import render, redirect
from .models import CapSol2

def home(request):
    cap1_last_data = CapSol2.objects.filter(devId="1").latest('dt')
    cap2_last_data = CapSol2.objects.filter(devId="2").latest('dt')
    cap3_last_data = CapSol2.objects.filter(devId="3").latest('dt')
    cap4_last_data = CapSol2.objects.filter(devId="4").latest('dt')
    cap5_last_data = CapSol2.objects.filter(devId="5").latest('dt')
    cap6_last_data = CapSol2.objects.filter(devId="6").latest('dt')
    cap7_last_data = CapSol2.objects.filter(devId="7").latest('dt')
    cap8_last_data = CapSol2.objects.filter(devId="8").latest('dt') ############## ajouter capteur nouveau de hum et temp
    cap9_last_data = CapSol2.objects.filter(devId="9").latest('dt') ############## ajouter capteur nouveau de hum et temp
    cap2 = CapSol2.objects.last()

    irrigation_time = None
    milliseconds = None
    hex_milliseconds = None

    if request.method == "POST":
        action = request.POST.get('action')

        if action == "set_time":
            irrigation_time = request.POST.get('irrigation_time')
            # Ici tu peux envoyer l'heure au device ou stocker

        elif action == "send_time":
            milliseconds = request.POST.get('milliseconds')
            if milliseconds and milliseconds.isdigit():
                hex_milliseconds = hex(int(milliseconds))[2:].upper()
                # Ici tu peux envoyer le temps converti en hexa au device

    context = {
        'cap2': cap2,
        'cap1_last_data': cap1_last_data,
        'cap2_last_data': cap2_last_data,
        'cap3_last_data': cap3_last_data,
        'cap4_last_data': cap4_last_data,
        'cap5_last_data': cap5_last_data,
        'cap6_last_data': cap6_last_data,
        'cap7_last_data': cap7_last_data,
        'cap8_last_data': cap8_last_data,  ############## ajouter capteur nouveau de hum et temp
        'cap9_last_data': cap9_last_data,  ############## ajouter capteur nouveau de hum et temp
        'irrigation_time': irrigation_time,
        'milliseconds': milliseconds,
        'hex_milliseconds': hex_milliseconds,
    }
    return render(request, "index.html", context)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import DeviceData

@csrf_exempt
def gprs_receive(request):
    if request.method == "GET":
        try:
            device_name  = request.GET.get('device', 'GPRS-MODULE')
            temp_ds      = float(request.GET.get('temp_ds', 0))
            hum_sht      = float(request.GET.get('hum_sht', 0))
            temp_sht     = float(request.GET.get('temp_sht', 0))
            battery      = float(request.GET.get('battery', 0))

            DeviceData.objects.create(
                device_name     = device_name,
                temp_ds         = temp_ds,
                hum_sht         = hum_sht,
                temp_sht        = temp_sht,
                battery_voltage = battery,
            )
            return JsonResponse({'status': 'ok'}, status=200)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'method not allowed'}, status=405)

#def home(request):
    # IDs des capteurs que tu veux afficher (1..9)
    #sensor_ids = range(1, 10)  # 1 → 9

    # Dictionnaire {id_capteur: dernière_donnée}
    #capteurs = {}

    #for sid in sensor_ids:
        #capteurs[sid] = (
            #CapSol2.objects
            #.filter(devId=sid)
            #.order_by('-dt')
            #.first()
        #)

    #context = {
        #"capteurs": capteurs
    #}

 #   return render(request, "index.html", context)
#******* Capteur des sol ***********
def capsol_filter(request):
    # Champs disponibles pour la sélection
    available_fields = ['Temp', 'Hum', 'ec', 'N', 'P', 'K', 'Sal', 'Bat']

    # Récupération des paramètres GET
    selected_field = request.GET.get('field', 'Temp')  # Temp par défaut
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Traitement des dates
    if start_date and end_date:
        start_date = make_aware(datetime.datetime.strptime(start_date, "%Y-%m-%d"))
        end_date = make_aware(datetime.datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59))
    else:
        one_day_ago = (datetime.datetime.now() - datetime.timedelta(days=1)).replace(hour=0, minute=0)
        start_date = make_aware(one_day_ago)
        end_date = make_aware(datetime.datetime.now().replace(hour=23, minute=59, second=59))

    # Filtrage des données CapSol2 pour les capteurs 1, 2 et 3
    data_by_sensor = {}
    for dev_id in [1, 2, 3, 4, 7, 8, 9]:  ##### j'ai modofie "for dev_id in [1, 2, 3, 4]:" en ajourant cap 8 et 9
        data = CapSol2.objects.filter(devId=dev_id, dt__range=(start_date, end_date)).order_by('dt')
        labels = [d.dt.strftime("%Y-%m-%d %H:%M:%S") for d in data]
        values = [getattr(d, selected_field, 0) if getattr(d, selected_field, None) is not None else 0 for d in data]
        data_by_sensor[dev_id] = list(zip(labels, values))
    # data_by_sensor = {}
    # for dev_id in [1, 2, 3, 4]:
    #     data = CapSol2.objects.filter(devId=dev_id, dt__range=(start_date, end_date)).order_by('dt')

    #     filtered_data = []
    #     for d in data:
    #         value = getattr(d, selected_field, None)
    #         if value is not None and value <= 500:
    #             timestamp = d.dt.strftime("%Y-%m-%d %H:%M:%S")
    #             filtered_data.append((timestamp, value))

    #     data_by_sensor[dev_id] = filtered_data
    # data_by_sensor = {}
    # for dev_id in [1, 2, 3, 4]:
    #     data = CapSol2.objects.filter(devId=dev_id, dt__range=(start_date, end_date)).order_by('dt')

    #     filtered_data = []
    #     for d in data:
    #         value = getattr(d, selected_field, None)

    #         # Si le champ sélectionné est "Temp" et que la température est supérieure à 100, ignorer l'enregistrement
    #         if selected_field == "Temp" and value is not None and value > 100:
    #             continue

    #         if value is not None:
    #             timestamp = d.dt.strftime("%Y-%m-%d %H:%M:%S")
    #             filtered_data.append((timestamp, value))

    #     data_by_sensor[dev_id] = filtered_data

    context = {
        'available_fields': available_fields,
        'selected_field': selected_field,
        'start_date': start_date.strftime("%Y-%m-%d"),
        'end_date': end_date.strftime("%Y-%m-%d"),
        'data_by_sensor': data_by_sensor
    }

    return render(request, "enviro/tvoc7.html", context)

#***********************************


################################capteur sol calibré par graviométrie#################################
from .models import CapSolGraviometrie

def capteursol(request):
    capteur1_last_data = CapSolGraviometrie.objects.filter(devId="1").latest('dt')
    capteur2_last_data = CapSolGraviometrie.objects.filter(devId="2").latest('dt')
    capteur3_last_data = CapSolGraviometrie.objects.filter(devId="3").latest('dt')
    capteur4_last_data = CapSolGraviometrie.objects.filter(devId="4").latest('dt')
    cap2 = CapSolGraviometrie.objects.last()

    irrigation_time = None
    milliseconds = None
    hex_milliseconds = None

    if request.method == "POST":
        action = request.POST.get('action')

        if action == "set_time":
            irrigation_time = request.POST.get('irrigation_time')
            # Ici tu peux envoyer l'heure au device ou stocker

        elif action == "send_time":
            milliseconds = request.POST.get('milliseconds')
            if milliseconds and milliseconds.isdigit():
                hex_milliseconds = hex(int(milliseconds))[2:].upper()
                # Ici tu peux envoyer le temps converti en hexa au device

    context = {
        'cap2': cap2,
        'capteur1_last_data': capteur1_last_data,
        'capteur2_last_data': capteur2_last_data,
        'capteur3_last_data': capteur3_last_data,
        'capteur4_last_data': capteur4_last_data,
        'irrigation_time': irrigation_time,
        'milliseconds': milliseconds,
        'hex_milliseconds': hex_milliseconds,
    }
    return render(request, "calibration_sol.html", context)
#******* Capteur des sol ***********
def capteursol_filter(request):
    # Champs disponibles pour la sélection
    available_fields = ['TempGraviometrie', 'HumGraviometrie', 'ecGraviometrie', 'NGraviometrie', 'PGraviometrie', 'KGraviometrie', 'SalGraviometrie', 'BatGraviometrie']

    # Récupération des paramètres GET
    selected_field = request.GET.get('field', 'TempGraviometrie')  # Temp par défaut
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Traitement des dates
    if start_date and end_date:
        start_date = make_aware(datetime.datetime.strptime(start_date, "%Y-%m-%d"))
        end_date = make_aware(datetime.datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59))
    else:
        one_day_ago = (datetime.datetime.now() - datetime.timedelta(days=1)).replace(hour=0, minute=0)
        start_date = make_aware(one_day_ago)
        end_date = make_aware(datetime.datetime.now().replace(hour=23, minute=59, second=59))

    # Filtrage des données CapSol2 pour les capteurs 1, 2 et 3
    data_by_sensor = {}
    for dev_id in [1, 2, 3, 4]:
        data = CapSolGraviometrie.objects.filter(devId=dev_id, dt__range=(start_date, end_date)).order_by('dt')
        labels = [d.dt.strftime("%Y-%m-%d %H:%M:%S") for d in data]
        values = [getattr(d, selected_field, 0) if getattr(d, selected_field, None) is not None else 0 for d in data]
        data_by_sensor[dev_id] = list(zip(labels, values))

    context = {
        'available_fields': available_fields,
        'selected_field': selected_field,
        'start_date': start_date.strftime("%Y-%m-%d"),
        'end_date': end_date.strftime("%Y-%m-%d"),
        'data_by_sensor': data_by_sensor
    }

    return render(request, "enviro/tvoc7.html", context)


####################################################################################################
    # completed = request.POST('checks')
    # print(completed)
    # if 'checks' in request.GET:

    # toSave = vanne.objects.all()
    # geek_object = vanne.objects.create(onoff=True)
    # geek_object.save()
    # toSave.save()
    # print(toSave)
# def fetch_data_for_eto():
#     # Période de données : hier de 00:00 à aujourd’hui 00:00
#     start_of_yesterday = (timezone.now() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
#     start_of_today = start_of_yesterday + timedelta(days=1)

#     # Moyennes des autres paramètres (hors Ray)
#     weather_data = Data2.objects.filter(Time_Stamp__range=(start_of_yesterday, start_of_today)).aggregate(
#         Avg('Temp'),
#         Avg('Hum'),
#         Avg('Wind_Speed'),
#         Avg('Pr')
#     )

#     # Min/max température et humidité
#     temp_max = Data2.objects.filter(Time_Stamp__range=(start_of_yesterday, start_of_today)).order_by('-Temp').first().Temp
#     temp_min = Data2.objects.filter(Time_Stamp__range=(start_of_yesterday, start_of_today)).order_by('Temp').first().Temp
#     hum_max = Data2.objects.filter(Time_Stamp__range=(start_of_yesterday, start_of_today)).order_by('-Hum').first().Hum
#     hum_min = Data2.objects.filter(Time_Stamp__range=(start_of_yesterday, start_of_today)).order_by('Hum').first().Hum

#     temp_avg = weather_data['Temp__avg']
#     wind_speed_avg = round(weather_data['Wind_Speed__avg'] / 3.6, 2) if weather_data['Wind_Speed__avg'] else 0

#     # Moyenne horaire de Ray (24 intervalles horaires)
#     hourly_ray_averages = []
#     for hour in range(24):
#         interval_start = start_of_yesterday + timedelta(hours=hour)
#         interval_end = interval_start + timedelta(hours=1)
#         avg_ray = Ray2.objects.filter(DateRay__range=(interval_start, interval_end)).aggregate(avg=Avg('Ray'))['avg']
#         if avg_ray is not None:
#             hourly_ray_averages.append(avg_ray)

#     # Moyenne journalière sur les 24 heures
#     if hourly_ray_averages:
#         daily_ray_avg = sum(hourly_ray_averages)
#     else:
#         daily_ray_avg = 0

#     # Conversion en MJ/m²
#     radiation_sum = daily_ray_avg

#     # Numéro du jour dans l’année (pour hier)
#     day_of_year = start_of_yesterday.timetuple().tm_yday

#     return {
#         'altitude': 532,
#         'latitude': 33.51,
#         'day_of_year': day_of_year,
#         'pressure': weather_data['Pr__avg'],
#         'humidity_max': hum_max,
#         'humidity_min': hum_min,
#         'temp_avg': temp_avg,
#         'temp_max': temp_max,
#         'temp_min': temp_min,
#         'radiation_sum': radiation_sum,
#         'wind_speed_avg': wind_speed_avg
#     }
# def fetch_data_for_etoDR():
#     # Début et fin de la journée d'hier
#     start_of_yesterday = (timezone.now() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
#     start_of_today = start_of_yesterday + timedelta(days=1)

#     # Moyennes globales (hors illumination)
#     weather_data = wsd.objects.filter(Time_Stamp__range=(start_of_yesterday, start_of_today)).aggregate(
#         Avg('TEM'),
#         Avg('HUM'),
#         Avg('wind_speed'),
#         Min('TEM'),
#         Max('TEM'),
#         Min('HUM'),
#         Max('HUM'),
#     )
#     weather_data1 = Data2.objects.filter(Time_Stamp__range=(start_of_yesterday, start_of_today)).aggregate(
#         Avg('Pr')
#     )
#     # Récupération depuis rs_temp
#     rs_temp_data = rs_temp.objects.filter(Time_Stamp__range=(start_of_yesterday, start_of_today)).aggregate(
#         Avg('temp1'),
#         Min('temp1'),
#         Max('temp1'),
#         Avg('hum1'),
#         Min('hum1'),
#         Max('hum1'),
#     )
#     # Température et humidité min/max
#     temp_max = wsd.objects.filter(Time_Stamp__range=(start_of_yesterday, start_of_today)).order_by('-TEM').first().TEM
#     temp_min = wsd.objects.filter(Time_Stamp__range=(start_of_yesterday, start_of_today)).order_by('TEM').first().TEM
#     hum_max = wsd.objects.filter(Time_Stamp__range=(start_of_yesterday, start_of_today)).order_by('-HUM').first().HUM
#     hum_min = wsd.objects.filter(Time_Stamp__range=(start_of_yesterday, start_of_today)).order_by('HUM').first().HUM

#     # Calcul des 24 moyennes horaires d'illumination
#     hourly_illum_averages = []
#     for hour in range(24):
#         interval_start = start_of_yesterday + timedelta(hours=hour)
#         interval_end = interval_start + timedelta(hours=1)
#         avg_illum = wsd.objects.filter(Time_Stamp__range=(interval_start, interval_end)).aggregate(avg=Avg('illumination'))['avg']
#         if avg_illum is not None:
#             hourly_illum_averages.append(avg_illum)

#     # Moyenne des 24 moyennes horaires
#     if hourly_illum_averages:
#         daily_illum_avg = sum(hourly_illum_averages)
#     else:
#         daily_illum_avg = 0

#     # Conversion en MJ/m²
#     radiation_sum = daily_illum_avg

#     wind_speed_avg = round(weather_data['wind_speed__avg'] / 3.6, 2) if weather_data['wind_speed__avg'] else 0

#     # Numéro du jour dans l’année pour hier
#     day_of_year = start_of_yesterday.timetuple().tm_yday

#     return {
#         'altitude': 532,
#         'latitude': 33.51,
#         'day_of_year': day_of_year,
#         'pressure': weather_data1['Pr__avg'],
#         'humidity_max': weather_data['HUM__max'],
#         'humidity_min': weather_data['HUM__min'],
#         'temp_avg': weather_data['TEM__avg'],
#         'temp_max': weather_data['TEM__max'],
#         'temp_min': weather_data['TEM__min'],
#         'radiation_sum': radiation_sum,
#         'wind_speed_avg': wind_speed_avg
#     }

# def fetch_data_for_etoDR():
#     start_of_yesterday = (timezone.now() - timedelta(days=1)).replace(
#         hour=0, minute=0, second=0, microsecond=0
#     )
#     start_of_today = start_of_yesterday + timedelta(days=1)

#     qs_wsd = wsd.objects.filter(Time_Stamp__range=(start_of_yesterday, start_of_today))

#     if not qs_wsd.exists():
#         logger.warning("Aucune donnée WSD pour la journée → ET0 impossible")
#         return None

#     weather_data = qs_wsd.aggregate(
#         temp_avg=Avg('TEM'),
#         temp_min=Min('TEM'),
#         temp_max=Max('TEM'),
#         humidity_min=Min('HUM'),
#         humidity_max=Max('HUM'),
#         wind_avg=Avg('wind_speed'),
#     )

#     weather_data1 = Data2.objects.filter(
#         Time_Stamp__range=(start_of_yesterday, start_of_today)
#     ).aggregate(pressure=Avg('Pr'))

#     if weather_data1['pressure'] is None:
#         logger.warning("Pression manquante → ET0 impossible")
#         return None

#     # Illumination horaire
#     hourly_illum = []
#     for hour in range(24):
#         interval_start = start_of_yesterday + timedelta(hours=hour)
#         interval_end = interval_start + timedelta(hours=1)

#         val = qs_wsd.filter(
#             Time_Stamp__range=(interval_start, interval_end)
#         ).aggregate(avg=Avg('illumination'))['avg']

#         if val is not None:
#             hourly_illum.append(val)

#     if not hourly_illum:
#         logger.warning("Radiation manquante → ET0 impossible")
#         return None

#     radiation_sum = sum(hourly_illum)

#     wind_speed_avg = (
#         round(weather_data['wind_avg'] / 3.6, 2)
#         if weather_data['wind_avg'] is not None
#         else None
#     )

#     day_of_year = start_of_yesterday.timetuple().tm_yday

#     return {
#         'altitude': 532,
#         'latitude': 33.51,
#         'day_of_year': day_of_year,
#         'pressure': weather_data1['pressure'],
#         'humidity_max': weather_data['humidity_max'],
#         'humidity_min': weather_data['humidity_min'],
#         'temp_avg': weather_data['temp_avg'],
#         'temp_max': weather_data['temp_max'],
#         'temp_min': weather_data['temp_min'],
#         'radiation_sum': radiation_sum,
#         'wind_speed_avg': wind_speed_avg,
#     }


# def fetch_data_for_etoDRv():
#     # Début et fin de la journée d'hier
#     start_of_yesterday = (timezone.now() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
#     start_of_today = start_of_yesterday + timedelta(days=1)

#     # Moyennes globales (hors illumination)
#     weather_data = wsd.objects.filter(Time_Stamp__range=(start_of_yesterday, start_of_today)).aggregate(
#         Avg('TEM'),
#         Avg('HUM'),
#         Avg('wind_speed'),
#         Min('TEM'),
#         Max('TEM'),
#         Min('HUM'),
#         Max('HUM'),
#     )
#     weather_data1 = Data2.objects.filter(Time_Stamp__range=(start_of_yesterday, start_of_today)).aggregate(
#         Avg('Pr')
#     )
#     # Récupération depuis rs_temp
#     rs_temp_data = rs_temp.objects.filter(Time_Stamp__range=(start_of_yesterday, start_of_today)).aggregate(
#         Avg('temp1'),
#         Min('temp1'),
#         Max('temp1'),
#         Avg('hum1'),
#         Min('hum1'),
#         Max('hum1'),
#     )
#     # Température et humidité min/max
#     temp_max = wsd.objects.filter(Time_Stamp__range=(start_of_yesterday, start_of_today)).order_by('-TEM').first().TEM
#     temp_min = wsd.objects.filter(Time_Stamp__range=(start_of_yesterday, start_of_today)).order_by('TEM').first().TEM
#     hum_max = wsd.objects.filter(Time_Stamp__range=(start_of_yesterday, start_of_today)).order_by('-HUM').first().HUM
#     hum_min = wsd.objects.filter(Time_Stamp__range=(start_of_yesterday, start_of_today)).order_by('HUM').first().HUM

#     # Moyenne horaire de Ray (24 intervalles horaires)
#     hourly_ray_averages = []
#     for hour in range(24):
#         interval_start = start_of_yesterday + timedelta(hours=hour)
#         interval_end = interval_start + timedelta(hours=1)
#         avg_ray = Ray2.objects.filter(DateRay__range=(interval_start, interval_end)).aggregate(avg=Avg('Ray'))['avg']
#         if avg_ray is not None:
#             hourly_ray_averages.append(avg_ray)

#     # Moyenne journalière sur les 24 heures
#     if hourly_ray_averages:
#         daily_ray_avg = sum(hourly_ray_averages)
#     else:
#         daily_ray_avg = 0

#     # Conversion en MJ/m²
#     radiation_sum = daily_ray_avg

#     wind_speed_avg = round(weather_data['wind_speed__avg'] / 3.6, 2) if weather_data['wind_speed__avg'] else 0

#     # Numéro du jour dans l’année pour hier
#     day_of_year = start_of_yesterday.timetuple().tm_yday

#     return {
#         'altitude': 532,
#         'latitude': 33.51,
#         'day_of_year': day_of_year,
#         'pressure': weather_data1['Pr__avg'],
#         'humidity_max': weather_data['HUM__max'],
#         'humidity_min': weather_data['HUM__min'],
#         'temp_avg': weather_data['TEM__avg'],
#         'temp_max': weather_data['TEM__max'],
#         'temp_min': weather_data['TEM__min'],
#         'radiation_sum': radiation_sum,
#         'wind_speed_avg': wind_speed_avg
#     }

def ETODR(target_date=None):

    if target_date is None:
        target_date = timezone.localtime(timezone.now()).date()

    # ✅ données de la journée précédente
    data_date = target_date - timedelta(days=1)

    # ✅ on fetch la veille
    data = fetch_data_for_etoDR(target_date=data_date)
    if data is None:
        print(f"⛔ ETO ignoré: données manquantes pour {data_date}")
        return None
    # data = fetch_data_for_etoDR()
    # if not validate_eto_data(data):
    #     return None
    A6 = data['altitude']  # Altitude (m)
    B6 = data['latitude']  # Latitude (degrés)
    C6 = 11  # Hauteur de l'anémomètre (m)
    D11 = data['day_of_year']  # Jour de l'année
    E6 = data['pressure']  # Pression moyenne (hPa)
    F11 = data['humidity_max']  # Humidité max (%)
    G11 = data['humidity_min']  # Humidité min (%)
    H11 = data['temp_avg']  # Température moyenne (°C)
    I11 = data['temp_max']  # Température max (°C)
    J11 = data['temp_min']  # Température min (°C)
    K11 = data['radiation_sum']  # Radiation solaire (MJ/m²)
    L11 = data['wind_speed_avg']  # Vitesse moyenne du vent (m/s)
    print("K11 : somme irradiation ", K11)
    # Remplacement des None par une valeur par défaut (ex: 0 ou une moyenne raisonnable)
    # I11 = I11 if I11 is not None else 0
    # J11 = J11 if J11 is not None else 0
    # H11 = H11 if H11 is not None else (I11 + J11) / 2
    # F11 = F11 if F11 is not None else 0
    # G11 = G11 if G11 is not None else 0
    # E6 = E6 if E6 is not None else 1013  # Pression atmosphérique standard
    print("===== Données Météorologiques =====")
    print(f"Altitude (A6)                : {data['altitude']} m")
    print(f"Latitude (B6)                : {data['latitude']} °")
    print(f"Hauteur de l'anémomètre (C6): 9.5 m")
    print(f"Jour de l'année (D11)        : {data['day_of_year']}")
    print(f"Pression moyenne (E6)        : {data['pressure']} hPa")
    print(f"Humidité max (F11)           : {data['humidity_max']} %")
    print(f"Humidité min (G11)           : {data['humidity_min']} %")
    print(f"Température moyenne (H11)    : {data['temp_avg']} °C")
    print(f"Température max (I11)        : {data['temp_max']} °C")
    print(f"Température min (J11)        : {data['temp_min']} °C")
    print(f"Radiation solaire (K11)      : {data['radiation_sum']} MJ/m²")
    print(f"Vitesse moyenne du vent (L11): {data['wind_speed_avg']} m/s")
    # Calculs
    P = 1013 * ((293 - 0.0065 * A6) / 293) ** 5.256
    λ = 694.5 * (1 - 0.000946 * H11)
    print("λ  : somme irradiation ",λ )
    γ = 0.2805555 * E6 / (0.622 * λ)
    U2 = 4.868 * L11 / np.log(67.75 * C6 - 5.42)
    γ_prime = γ * (1 + 0.34 * U2)

    if np.isnan(H11):
        ea_Tmoy = 6.108 * np.exp((17.27 * (I11 + J11) / 2) / ((I11 + J11) / 2 + 237.3))
    else:
        ea_Tmoy = 6.108 * np.exp((17.27 * H11) / (H11 + 237.3))

    if pd.isna(F11) or pd.isna(I11):
        ed = ea_Tmoy * E6 / 100
    else:
        ed = (6.108 * np.exp((17.27 * J11) / (J11 + 237.3)) * F11 +
              6.108 * np.exp((17.27 * I11) / (I11 + 237.3)) * G11) / 200

    Δ = 4098.171 * ea_Tmoy / (ea_Tmoy + 237.3) ** 2
    dr = 1 + 0.033 * np.cos(2 * np.pi * D11 / 365)
    δ = 0.4093 * np.sin(2 * np.pi * (284 + D11) / 365)
    ωs = np.arccos(-np.tan(np.radians(B6)) * np.tan(δ))
    Rsmm = K11 / λ
    print("Rsmm  : somme irradiation ",Rsmm )
    Ra = (24 / np.pi) * 1367 * dr * (ωs * np.sin(np.radians(B6)) * np.sin(δ) +
                                     np.cos(np.radians(B6)) * np.cos(δ) * np.sin(ωs))
    Ramm = Ra / λ
    Rso = (0.75 + 2 * (10 ** -5) * A6) * Ramm

    if pd.isna(F11) or pd.isna(I11):
        Rn = 0.77 * Rsmm - (1.35 * (Rsmm / Rso) - 0.35) * (0.34 - 0.14 * np.sqrt(ed)) * (1360.8 * (10 ** -9) / λ) * (H11 + 273.16) ** 4
    else:
        Rn = (0.77 * Rsmm - (1.35 * (Rsmm / Rso) - 0.35) * (0.34 - 0.14 * np.sqrt(ed)) * (1360.8 * (10 ** -9) / λ) *
              ((I11 + 273.16) ** 4 + (J11 + 273.16) ** 4) / 2)

    ETrad = (Δ * Rn) / (Δ + γ_prime)

    if np.isnan(H11):
        ETaero = (γ * (90 / ((I11 + J11) / 2 + 273.16)) * U2 * (ea_Tmoy - ed)) / (Δ + γ_prime)
    else:
        ETaero = (γ * (90 / (H11 + 273.16)) * U2 * (ea_Tmoy - ed)) / (Δ + γ_prime)

    ETo = ETrad + ETaero

    # Résultats
    # Output results
    print(f"P: {P} mb")
    print(f"λ: {λ} W/m²/mm")
    print(f"γ: {γ} mb/°C")
    print(f"U2: {U2} m/s")
    print(f"γ': {γ_prime} mb/°C")
    print(f"ea(Tmoy): {ea_Tmoy} mb")
    print(f"ed: {ed} mb")
    print(f"Δ: {Δ} mb/°C")
    print(f"dr: {dr}")
    print(f"δ: {δ} radian")
    print(f"ωs: {ωs} radian")
    print(f"Rsmm: {Rsmm} mm/jour")
    print(f"Ra: {Ra} W/m²")
    print(f"Ramm: {Ramm} mm/jour")
    print(f"Rso: {Rso} mm/jour")
    print(f"Rn: {Rn} mm/jour")
    print(f"ETrad: {ETrad} mm/jour")
    print(f"ETaero: {ETaero} mm/jour")
    print(f"ETo: {ETo} mm/jour")

    # Enregistrement dans la base de données
    ET0DR.objects.create(
        Time_Stamp=ts_0101(target_date),
        value=round(ETo, 2),
        WSavg=L11,
        Tmax=I11,
        Tmin=J11,
        Tavg=H11,
        Hmax=F11,
        Hmin=G11,
        Raym=round(K11, 2),
        U2=U2,
        Delta=D11
    )

###################################################

def ETODR_FAO56_DR(target_date=None):

    if target_date is None:
        target_date = timezone.localtime(timezone.now()).date()

    # ✅ données de la journée précédente
    data_date = target_date - timedelta(days=1)

    # ✅ on fetch la veille
    data = fetch_data_for_etoDR(target_date=data_date)
    if data is None:
        print(f"⛔ ETO ignoré: données manquantes pour {data_date}")
        return None
    # ========= 1) LECTURE DES DONNÉES BRUTES =========
    A6_alt_m   = float(data['altitude'])          # Altitude (m)
    B6_lat_deg = float(data['latitude'])          # Latitude (degrés)
    C6_z_m     = 11.0                             # Hauteur de l'anémomètre (m)
    D11_doy    = int(data['day_of_year'])         # Jour de l'année (1–365)
    E6_hPa     = data.get('pressure')             # Pression moyenne (hPa) ou None

    Tmax_C = float(data['temp_max'])
    Tmin_C = float(data['temp_min'])
    Tmoy_C = float(data['temp_avg'])

    RHmax_pct = float(data['humidity_max'])
    RHmin_pct = float(data['humidity_min'])

    # ⚠️ IMPORTANT : ici on suppose que radiation_sum = total journalier en Wh/m²
    # Si dans ta base c'est déjà en MJ/m²/j, enlève la conversion (voir commentaire plus bas)
    Ray_total_Whm2 = float(data['radiation_sum'])
    Ray_avg_Wm2 = Ray_total_Whm2 / 24.0 ###########
    uz_value = float(data['wind_speed_avg'])      # vent mesuré à z = 11 m
    wind_unit = "m/s"

    print("===== Données Météorologiques (ETODR_FAO56_V) =====")
    print(f"Alt       = {A6_alt_m} m | Lat = {B6_lat_deg} ° | DOY = {D11_doy}")
    print(f"Tmax/Tmin/Tmoy = {Tmax_C}/{Tmin_C}/{Tmoy_C} °C")
    print(f"RHmax/RHmin    = {RHmax_pct}/{RHmin_pct} %")
    print(f"Rayonnement total (brut) = {Ray_total_Whm2} Wh/m²")
    print(f"Rayonnement moyen        = {Ray_avg_Wm2:.2f} W/m²") ########
    print(f"Vent (mesuré)   = {uz_value} {wind_unit} à {C6_z_m} m")

    # ========= 2) OUTILS FAO-56 =========

    def pressure_kPa_from_alt(z_m: float) -> float:
        """Pression atmosphérique (kPa) en fonction de l'altitude (m)"""
        return 101.3 * ((293.0 - 0.0065 * z_m) / 293.0) ** 5.26

    def es_kPa(Tc: float) -> float:
        """Pression de vapeur saturante es (kPa)"""
        return 0.6108 * math.exp(17.27 * Tc / (Tc + 237.3))

    def slope_kPa_per_C(Tm: float) -> float:
        """Pente de la courbe de saturation Δ (kPa/°C)"""
        return 4098.0 * (0.6108 * math.exp(17.27 * Tm / (Tm + 237.3))) / (Tm + 237.3) ** 2

    def dr(J: int) -> float:
        """Distance relative Terre–Soleil"""
        return 1.0 + 0.033 * math.cos(2.0 * math.pi * J / 365.0)

    def decl(J: int) -> float:
        """Déclinaison solaire (rad)"""
        return 0.409 * math.sin(2.0 * math.pi * J / 365.0 - 1.39)

    def ws(phi: float, d: float) -> float:
        """Angle horaire au coucher du soleil (rad)"""
        return math.acos(-math.tan(phi) * math.tan(d))

    def Ra_MJ(J: int, lat_deg: float) -> float:
        """Rayonnement extraterrestre Ra (MJ/m²/j)"""
        phi = math.radians(lat_deg)
        Gsc = 0.0820  # MJ m^-2 min^-1
        d = decl(J)
        w = ws(phi, d)
        return (24.0 * 60.0 / math.pi) * Gsc * dr(J) * (
            w * math.sin(phi) * math.sin(d) +
            math.cos(phi) * math.cos(d) * math.sin(w)
        )

    def Rso_MJ(Ra: float, z_m: float) -> float:
        """Rayonnement ciel clair Rso (MJ/m²/j)"""
        return (0.75 + 2.0e-5 * z_m) * Ra

    def u2_from_uz(uz_value: float, z_m: float, unit: str = "m/s") -> float:
        """Vent mesuré à z_m -> vent standardisé à 2 m (u2)"""
        uz = float(uz_value)
        if unit.lower() in ["km/h", "kmh", "kph"]:
            uz /= 3.6  # km/h -> m/s
        return uz * (4.87 / math.log(67.8 * z_m - 5.42))

    def rs_to_MJ_per_m2_per_day(avg_Wm2=None, total_Whm2=None) -> float:
        """
        Convertit Rs vers MJ/m²/j :
        - soit à partir d'un total Wh/m²/j
        - soit à partir d'une moyenne W/m²
        """
        if total_Whm2 is not None:
            return float(total_Whm2) * 0.0036
        if avg_Wm2 is not None:
            return float(avg_Wm2) * 0.0864
        raise ValueError("Fournis Ray_total_Whm2 ou Ray_avg_Wm2")

    # ========= 3) PARAMÈTRES FAO-56 =========

    # Pression en kPa
    if E6_hPa is not None:
        P_kPa = float(E6_hPa) / 10.0
    else:
        P_kPa = pressure_kPa_from_alt(A6_alt_m)

    gamma = 0.000665 * P_kPa          # kPa/°C
    Delta = slope_kPa_per_C(Tmoy_C)   # kPa/°C

    # Pression de vapeur saturante (kPa)
    es_Tmax = es_kPa(Tmax_C)
    es_Tmin = es_kPa(Tmin_C)
    es_mean = (es_Tmax + es_Tmin) / 2.0

    # Pression de vapeur réelle e_a (kPa)
    ea = (es_Tmin * RHmax_pct / 100.0 + es_Tmax * RHmin_pct / 100.0) / 2.0
    vpd = max(es_mean - ea, 0.0)

    # Rayonnement global Rs (MJ/m²/j) – conversion depuis Wh/m²
    Rs_MJ = rs_to_MJ_per_m2_per_day(avg_Wm2=None, total_Whm2=Ray_total_Whm2)

    # Rayonnement extraterrestre & ciel clair
    Ra  = Ra_MJ(D11_doy, B6_lat_deg)
    Rso = Rso_MJ(Ra, A6_alt_m)

    # Rayonnement net
    albedo = 0.23
    sigma  = 4.903e-9  # MJ K^-4 m^-2 j^-1
    Rns = (1.0 - albedo) * Rs_MJ

    Tmax_K = Tmax_C + 273.16
    Tmin_K = Tmin_C + 273.16
    Rnl = sigma * ((Tmax_K**4 + Tmin_K**4) / 2.0) \
          * (0.34 - 0.14 * math.sqrt(max(ea, 0.0))) \
          * (1.35 * min(Rs_MJ / Rso, 1.0) - 0.35)

    Rn = Rns - Rnl
    G  = 0.0  # flux de chaleur du sol pour la journée

    # Vent à 2 m
    U2 = u2_from_uz(uz_value, C6_z_m, unit=wind_unit)

    # ========= 4) ET0 FAO-56 =========
    num = 0.408 * Delta * (Rn - G) + gamma * (900.0 / (Tmoy_C + 273.0)) * U2 * vpd
    den = Delta + gamma * (1.0 + 0.34 * U2)

    if den <= 0:
        ETo = 0.0
    else:
        ETo = max(0.0, num / den)

    print("\n===== Termes FAO-56 =====")
    print(f"P={P_kPa:.2f} kPa | γ={gamma:.4f} kPa/°C | Δ={Delta:.4f} kPa/°C")
    print(f"es_mean={es_mean:.3f} kPa | ea={ea:.3f} kPa | VPD={vpd:.3f} kPa")
    print(f"Ra={Ra:.2f} MJ/m²/j | Rso={Rso:.2f} MJ/m²/j")
    print(f"Rs={Rs_MJ:.3f} MJ/m²/j | Rn={Rn:.2f} MJ/m²/j")
    print(f"u2@2m={U2:.3f} m/s")
    print(f"\nET0 (FAO-56) = {ETo:.2f} mm/j\n")

    # ========= 5) SAUVEGARDE EN BASE =========
    ETODR_FAO56.objects.create(
        Time_Stamp=ts_0101(target_date),
        value=round(ETo, 2),
        WSavg=uz_value,
        Tmax=Tmax_C,
        Tmin=Tmin_C,
        Tavg=Tmoy_C,
        Hmax=RHmax_pct,
        Hmin=RHmin_pct,
        Raym=round(Ray_total_Whm2, 2),
        U2=U2,
        Delta=D11_doy
    )


def ETOS_FAO56_S(target_date=None):

    if target_date is None:
        target_date = timezone.localtime(timezone.now()).date()

    # ✅ données de la journée précédente
    data_date = target_date - timedelta(days=1)

    # ✅ on fetch la veille
    data = fetch_data_for_eto(target_date=data_date)
    if data is None:
        print(f"⛔ ETO ignoré: données manquantes pour {data_date}")
        return None
    # ========= 1) LECTURE DES DONNÉES BRUTES =========
    A6_alt_m   = float(data['altitude'])          # Altitude (m)
    B6_lat_deg = float(data['latitude'])          # Latitude (degrés)
    C6_z_m     = 9.5                              # Hauteur de l'anémomètre (m)
    D11_doy    = int(data['day_of_year'])         # Jour de l'année (1–365)
    E6_hPa     = data.get('pressure')             # Pression moyenne (hPa) ou None

    Tmax_C = float(data['temp_max'])
    Tmin_C = float(data['temp_min'])
    Tmoy_C = float(data['temp_avg'])

    RHmax_pct = float(data['humidity_max'])
    RHmin_pct = float(data['humidity_min'])

    # ⚠️ IMPORTANT : ici on suppose que radiation_sum = total journalier en Wh/m²
    # Si dans ta base c'est déjà en MJ/m²/j, enlève la conversion (voir commentaire plus bas)
    Ray_total_Whm2 = float(data['radiation_sum'])
    Ray_avg_Wm2 = Ray_total_Whm2 / 24.0 ###########
    uz_value = float(data['wind_speed_avg'])      # vent mesuré à z = 11 m
    wind_unit = "m/s"

    print("===== Données Météorologiques (ETODR_FAO56_V) =====")
    print(f"Alt       = {A6_alt_m} m | Lat = {B6_lat_deg} ° | DOY = {D11_doy}")
    print(f"Tmax/Tmin/Tmoy = {Tmax_C}/{Tmin_C}/{Tmoy_C} °C")
    print(f"RHmax/RHmin    = {RHmax_pct}/{RHmin_pct} %")
    print(f"Rayonnement total (brut) = {Ray_total_Whm2} Wh/m²")
    print(f"Vent (mesuré)   = {uz_value} {wind_unit} à {C6_z_m} m")

    # ========= 2) OUTILS FAO-56 =========

    def pressure_kPa_from_alt(z_m: float) -> float:
        """Pression atmosphérique (kPa) en fonction de l'altitude (m)"""
        return 101.3 * ((293.0 - 0.0065 * z_m) / 293.0) ** 5.26

    def es_kPa(Tc: float) -> float:
        """Pression de vapeur saturante es (kPa)"""
        return 0.6108 * math.exp(17.27 * Tc / (Tc + 237.3))

    def slope_kPa_per_C(Tm: float) -> float:
        """Pente de la courbe de saturation Δ (kPa/°C)"""
        return 4098.0 * (0.6108 * math.exp(17.27 * Tm / (Tm + 237.3))) / (Tm + 237.3) ** 2

    def dr(J: int) -> float:
        """Distance relative Terre–Soleil"""
        return 1.0 + 0.033 * math.cos(2.0 * math.pi * J / 365.0)

    def decl(J: int) -> float:
        """Déclinaison solaire (rad)"""
        return 0.409 * math.sin(2.0 * math.pi * J / 365.0 - 1.39)

    def ws(phi: float, d: float) -> float:
        """Angle horaire au coucher du soleil (rad)"""
        return math.acos(-math.tan(phi) * math.tan(d))

    def Ra_MJ(J: int, lat_deg: float) -> float:
        """Rayonnement extraterrestre Ra (MJ/m²/j)"""
        phi = math.radians(lat_deg)
        Gsc = 0.0820  # MJ m^-2 min^-1
        d = decl(J)
        w = ws(phi, d)
        return (24.0 * 60.0 / math.pi) * Gsc * dr(J) * (
            w * math.sin(phi) * math.sin(d) +
            math.cos(phi) * math.cos(d) * math.sin(w)
        )

    def Rso_MJ(Ra: float, z_m: float) -> float:
        """Rayonnement ciel clair Rso (MJ/m²/j)"""
        return (0.75 + 2.0e-5 * z_m) * Ra

    def u2_from_uz(uz_value: float, z_m: float, unit: str = "m/s") -> float:
        """Vent mesuré à z_m -> vent standardisé à 2 m (u2)"""
        uz = float(uz_value)
        if unit.lower() in ["km/h", "kmh", "kph"]:
            uz /= 3.6  # km/h -> m/s
        return uz * (4.87 / math.log(67.8 * z_m - 5.42))

    def rs_to_MJ_per_m2_per_day(avg_Wm2=None, total_Whm2=None) -> float:
        """
        Convertit Rs vers MJ/m²/j :
        - soit à partir d'un total Wh/m²/j
        - soit à partir d'une moyenne W/m²
        """
        if total_Whm2 is not None:
            return float(total_Whm2) * 0.0036
        if avg_Wm2 is not None:
            return float(avg_Wm2) * 0.0864
        raise ValueError("Fournis Ray_total_Whm2 ou Ray_avg_Wm2")

    # ========= 3) PARAMÈTRES FAO-56 =========

    # Pression en kPa
    if E6_hPa is not None:
        P_kPa = float(E6_hPa) / 10.0
    else:
        P_kPa = pressure_kPa_from_alt(A6_alt_m)

    gamma = 0.000665 * P_kPa          # kPa/°C
    Delta = slope_kPa_per_C(Tmoy_C)   # kPa/°C

    # Pression de vapeur saturante (kPa)
    es_Tmax = es_kPa(Tmax_C)
    es_Tmin = es_kPa(Tmin_C)
    es_mean = (es_Tmax + es_Tmin) / 2.0

    # Pression de vapeur réelle e_a (kPa)
    ea = (es_Tmin * RHmax_pct / 100.0 + es_Tmax * RHmin_pct / 100.0) / 2.0
    vpd = max(es_mean - ea, 0.0)

    # Rayonnement global Rs (MJ/m²/j) – conversion depuis Wh/m²
    Rs_MJ = rs_to_MJ_per_m2_per_day(avg_Wm2=None, total_Whm2=Ray_total_Whm2)

    # Rayonnement extraterrestre & ciel clair
    Ra  = Ra_MJ(D11_doy, B6_lat_deg)
    Rso = Rso_MJ(Ra, A6_alt_m)

    # Rayonnement net
    albedo = 0.23
    sigma  = 4.903e-9  # MJ K^-4 m^-2 j^-1
    Rns = (1.0 - albedo) * Rs_MJ

    Tmax_K = Tmax_C + 273.16
    Tmin_K = Tmin_C + 273.16
    Rnl = sigma * ((Tmax_K**4 + Tmin_K**4) / 2.0) \
          * (0.34 - 0.14 * math.sqrt(max(ea, 0.0))) \
          * (1.35 * min(Rs_MJ / Rso, 1.0) - 0.35)

    Rn = Rns - Rnl
    G  = 0.0  # flux de chaleur du sol pour la journée

    # Vent à 2 m
    U2 = u2_from_uz(uz_value, C6_z_m, unit=wind_unit)

    # ========= 4) ET0 FAO-56 =========
    num = 0.408 * Delta * (Rn - G) + gamma * (900.0 / (Tmoy_C + 273.0)) * U2 * vpd
    den = Delta + gamma * (1.0 + 0.34 * U2)

    if den <= 0:
        ETo = 0.0
    else:
        ETo = max(0.0, num / den)

    print("\n===== Termes FAO-56 =====")
    print(f"P={P_kPa:.2f} kPa | γ={gamma:.4f} kPa/°C | Δ={Delta:.4f} kPa/°C")
    print(f"es_mean={es_mean:.3f} kPa | ea={ea:.3f} kPa | VPD={vpd:.3f} kPa")
    print(f"Ra={Ra:.2f} MJ/m²/j | Rso={Rso:.2f} MJ/m²/j")
    print(f"Rs={Rs_MJ:.3f} MJ/m²/j | Rn={Rn:.2f} MJ/m²/j")
    print(f"u2@2m={U2:.3f} m/s")
    print(f"\nET0 (FAO-56) = {ETo:.2f} mm/j\n")

    # ========= 5) SAUVEGARDE EN BASE =========
    ETOSensCap_FAO56.objects.create(
        Time_Stamp=ts_0101(target_date),
        value=round(ETo, 2),
        WSavg=uz_value,
        Tmax=Tmax_C,
        Tmin=Tmin_C,
        Tavg=Tmoy_C,
        Hmax=RHmax_pct,
        Hmin=RHmin_pct,
        #Raym=round(Rs_MJ, 2),
        Raym=round(Ray_total_Whm2, 2),
        U2=U2,
        Delta=D11_doy
    )


def ETODRV_FAO56_DRV(target_date=None):

    if target_date is None:
        target_date = timezone.localtime(timezone.now()).date()

    # ✅ données de la journée précédente
    data_date = target_date - timedelta(days=1)

    # ✅ on fetch la veille
    data = fetch_data_for_etoDRv(target_date=data_date)
    if data is None:
        print(f"⛔ ETO ignoré: données manquantes pour {data_date}")
        return None
    # ========= 1) LECTURE DES DONNÉES BRUTES =========
    A6_alt_m   = float(data['altitude'])          # Altitude (m)
    B6_lat_deg = float(data['latitude'])          # Latitude (degrés)
    C6_z_m     = 11.0                             # Hauteur de l'anémomètre (m)
    D11_doy    = int(data['day_of_year'])         # Jour de l'année (1–365)
    E6_hPa     = data.get('pressure')             # Pression moyenne (hPa) ou None

    Tmax_C = float(data['temp_max'])
    Tmin_C = float(data['temp_min'])
    Tmoy_C = float(data['temp_avg'])

    RHmax_pct = float(data['humidity_max'])
    RHmin_pct = float(data['humidity_min'])

    # ⚠️ IMPORTANT : ici on suppose que radiation_sum = total journalier en Wh/m²
    # Si dans ta base c'est déjà en MJ/m²/j, enlève la conversion (voir commentaire plus bas)
    Ray_total_Whm2 = float(data['radiation_sum'])
    Ray_avg_Wm2 = Ray_total_Whm2 / 24.0 ###########
    uz_value = float(data['wind_speed_avg'])      # vent mesuré à z = 11 m
    wind_unit = "m/s"

    print("===== Données Météorologiques (ETODRV_FAO56_V) =====")
    print(f"Alt       = {A6_alt_m} m | Lat = {B6_lat_deg} ° | DOY = {D11_doy}")
    print(f"Tmax/Tmin/Tmoy = {Tmax_C}/{Tmin_C}/{Tmoy_C} °C")
    print(f"RHmax/RHmin    = {RHmax_pct}/{RHmin_pct} %")
    print(f"Rayonnement total (brut) = {Ray_total_Whm2} Wh/m²")
    print(f"Vent (mesuré)   = {uz_value} {wind_unit} à {C6_z_m} m")

    # ========= 2) OUTILS FAO-56 =========

    def pressure_kPa_from_alt(z_m: float) -> float:
        """Pression atmosphérique (kPa) en fonction de l'altitude (m)"""
        return 101.3 * ((293.0 - 0.0065 * z_m) / 293.0) ** 5.26

    def es_kPa(Tc: float) -> float:
        """Pression de vapeur saturante es (kPa)"""
        return 0.6108 * math.exp(17.27 * Tc / (Tc + 237.3))

    def slope_kPa_per_C(Tm: float) -> float:
        """Pente de la courbe de saturation Δ (kPa/°C)"""
        return 4098.0 * (0.6108 * math.exp(17.27 * Tm / (Tm + 237.3))) / (Tm + 237.3) ** 2

    def dr(J: int) -> float:
        """Distance relative Terre–Soleil"""
        return 1.0 + 0.033 * math.cos(2.0 * math.pi * J / 365.0)

    def decl(J: int) -> float:
        """Déclinaison solaire (rad)"""
        return 0.409 * math.sin(2.0 * math.pi * J / 365.0 - 1.39)

    def ws(phi: float, d: float) -> float:
        """Angle horaire au coucher du soleil (rad)"""
        return math.acos(-math.tan(phi) * math.tan(d))

    def Ra_MJ(J: int, lat_deg: float) -> float:
        """Rayonnement extraterrestre Ra (MJ/m²/j)"""
        phi = math.radians(lat_deg)
        Gsc = 0.0820  # MJ m^-2 min^-1
        d = decl(J)
        w = ws(phi, d)
        return (24.0 * 60.0 / math.pi) * Gsc * dr(J) * (
            w * math.sin(phi) * math.sin(d) +
            math.cos(phi) * math.cos(d) * math.sin(w)
        )

    def Rso_MJ(Ra: float, z_m: float) -> float:
        """Rayonnement ciel clair Rso (MJ/m²/j)"""
        return (0.75 + 2.0e-5 * z_m) * Ra

    def u2_from_uz(uz_value: float, z_m: float, unit: str = "m/s") -> float:
        """Vent mesuré à z_m -> vent standardisé à 2 m (u2)"""
        uz = float(uz_value)
        if unit.lower() in ["km/h", "kmh", "kph"]:
            uz /= 3.6  # km/h -> m/s
        return uz * (4.87 / math.log(67.8 * z_m - 5.42))

    def rs_to_MJ_per_m2_per_day(avg_Wm2=None, total_Whm2=None) -> float:
        """
        Convertit Rs vers MJ/m²/j :
        - soit à partir d'un total Wh/m²/j
        - soit à partir d'une moyenne W/m²
        """
        if total_Whm2 is not None:
            return float(total_Whm2) * 0.0036
        if avg_Wm2 is not None:
            return float(avg_Wm2) * 0.0864
        raise ValueError("Fournis Ray_total_Whm2 ou Ray_avg_Wm2")

    # ========= 3) PARAMÈTRES FAO-56 =========

    # Pression en kPa
    if E6_hPa is not None:
        P_kPa = float(E6_hPa) / 10.0
    else:
        P_kPa = pressure_kPa_from_alt(A6_alt_m)

    gamma = 0.000665 * P_kPa          # kPa/°C
    Delta = slope_kPa_per_C(Tmoy_C)   # kPa/°C

    # Pression de vapeur saturante (kPa)
    es_Tmax = es_kPa(Tmax_C)
    es_Tmin = es_kPa(Tmin_C)
    es_mean = (es_Tmax + es_Tmin) / 2.0

    # Pression de vapeur réelle e_a (kPa)
    ea = (es_Tmin * RHmax_pct / 100.0 + es_Tmax * RHmin_pct / 100.0) / 2.0
    vpd = max(es_mean - ea, 0.0)

    # Rayonnement global Rs (MJ/m²/j) – conversion depuis Wh/m²
    Rs_MJ = rs_to_MJ_per_m2_per_day(avg_Wm2=None, total_Whm2=Ray_total_Whm2)

    # Rayonnement extraterrestre & ciel clair
    Ra  = Ra_MJ(D11_doy, B6_lat_deg)
    Rso = Rso_MJ(Ra, A6_alt_m)

    # Rayonnement net
    albedo = 0.23
    sigma  = 4.903e-9  # MJ K^-4 m^-2 j^-1
    Rns = (1.0 - albedo) * Rs_MJ

    Tmax_K = Tmax_C + 273.16
    Tmin_K = Tmin_C + 273.16
    Rnl = sigma * ((Tmax_K**4 + Tmin_K**4) / 2.0) \
          * (0.34 - 0.14 * math.sqrt(max(ea, 0.0))) \
          * (1.35 * min(Rs_MJ / Rso, 1.0) - 0.35)

    Rn = Rns - Rnl
    G  = 0.0  # flux de chaleur du sol pour la journée

    # Vent à 2 m
    U2 = u2_from_uz(uz_value, C6_z_m, unit=wind_unit)

    # ========= 4) ET0 FAO-56 =========
    num = 0.408 * Delta * (Rn - G) + gamma * (900.0 / (Tmoy_C + 273.0)) * U2 * vpd
    den = Delta + gamma * (1.0 + 0.34 * U2)

    if den <= 0:
        ETo = 0.0
    else:
        ETo = max(0.0, num / den)

    print("\n===== Termes FAO-56 =====")
    print(f"P={P_kPa:.2f} kPa | γ={gamma:.4f} kPa/°C | Δ={Delta:.4f} kPa/°C")
    print(f"es_mean={es_mean:.3f} kPa | ea={ea:.3f} kPa | VPD={vpd:.3f} kPa")
    print(f"Ra={Ra:.2f} MJ/m²/j | Rso={Rso:.2f} MJ/m²/j")
    print(f"Rs={Rs_MJ:.3f} MJ/m²/j | Rn={Rn:.2f} MJ/m²/j")
    print(f"u2@2m={U2:.3f} m/s")
    print(f"\nET0 (FAO-56) = {ETo:.2f} mm/j\n")

    # ========= 5) SAUVEGARDE EN BASE =========
    ETODRV_FAO56.objects.create(
        Time_Stamp=ts_0101(target_date),
        value=round(ETo, 2),
        WSavg=uz_value,
        Tmax=Tmax_C,
        Tmin=Tmin_C,
        Tavg=Tmoy_C,
        Hmax=RHmax_pct,
        Hmin=RHmin_pct,
        #Raym=round(Rs_MJ, 2),
        Raym=round(Ray_total_Whm2, 2),
        U2=U2,
        Delta=D11_doy
    )
#######################################################
def ETODRv(target_date=None):

    if target_date is None:
        target_date = timezone.localtime(timezone.now()).date()

    # ✅ données de la journée précédente
    data_date = target_date - timedelta(days=1)

    # ✅ on fetch la veille
    data = fetch_data_for_etoDRv(target_date=data_date)
    if data is None:
        print(f"⛔ ETO ignoré: données manquantes pour {data_date}")
        return None
    # data = fetch_data_for_etoDRv()
    A6 = data['altitude']  # Altitude (m)
    B6 = data['latitude']  # Latitude (degrés)
    C6 = 11  # Hauteur de l'anémomètre (m)
    D11 = data['day_of_year']  # Jour de l'année
    E6 = data['pressure']  # Pression moyenne (hPa)
    F11 = data['humidity_max']  # Humidité max (%)
    G11 = data['humidity_min']  # Humidité min (%)
    H11 = data['temp_avg']  # Température moyenne (°C)
    I11 = data['temp_max']  # Température max (°C)
    J11 = data['temp_min']  # Température min (°C)
    K11 = data['radiation_sum']  # Radiation solaire (MJ/m²)
    L11 = data['wind_speed_avg']  # Vitesse moyenne du vent (m/s)
    print("===== Données Météorologiques =====")
    print(f"Altitude (A6)                : {data['altitude']} m")
    print(f"Latitude (B6)                : {data['latitude']} °")
    print(f"Hauteur de l'anémomètre (C6): 9.5 m")
    print(f"Jour de l'année (D11)        : {data['day_of_year']}")
    print(f"Pression moyenne (E6)        : {data['pressure']} hPa")
    print(f"Humidité max (F11)           : {data['humidity_max']} %")
    print(f"Humidité min (G11)           : {data['humidity_min']} %")
    print(f"Température moyenne (H11)    : {data['temp_avg']} °C")
    print(f"Température max (I11)        : {data['temp_max']} °C")
    print(f"Température min (J11)        : {data['temp_min']} °C")
    print(f"Radiation solaire (K11)      : {data['radiation_sum']} MJ/m²")
    print(f"Vitesse moyenne du vent (L11): {data['wind_speed_avg']} m/s")
    # Remplacement des None par une valeur par défaut (ex: 0 ou une moyenne raisonnable)
    # I11 = I11 if I11 is not None else 0
    # J11 = J11 if J11 is not None else 0
    # H11 = H11 if H11 is not None else (I11 + J11) / 2
    # F11 = F11 if F11 is not None else 0
    # G11 = G11 if G11 is not None else 0
    # E6 = E6 if E6 is not None else 1013  # Pression atmosphérique standard

    # Calculs
    P = 1013 * ((293 - 0.0065 * A6) / 293) ** 5.256
    λ = 694.5 * (1 - 0.000946 * H11)
    γ = 0.2805555 * E6 / (0.622 * λ)
    U2 = 4.868 * L11 / np.log(67.75 * C6 - 5.42)
    γ_prime = γ * (1 + 0.34 * U2)

    if np.isnan(H11):
        ea_Tmoy = 6.108 * np.exp((17.27 * (I11 + J11) / 2) / ((I11 + J11) / 2 + 237.3))
    else:
        ea_Tmoy = 6.108 * np.exp((17.27 * H11) / (H11 + 237.3))

    if pd.isna(F11) or pd.isna(I11):
        ed = ea_Tmoy * E6 / 100
    else:
        ed = (6.108 * np.exp((17.27 * J11) / (J11 + 237.3)) * F11 +
              6.108 * np.exp((17.27 * I11) / (I11 + 237.3)) * G11) / 200

    Δ = 4098.171 * ea_Tmoy / (ea_Tmoy + 237.3) ** 2
    dr = 1 + 0.033 * np.cos(2 * np.pi * D11 / 365)
    δ = 0.4093 * np.sin(2 * np.pi * (284 + D11) / 365)
    ωs = np.arccos(-np.tan(np.radians(B6)) * np.tan(δ))
    Rsmm = K11 / λ
    Ra = (24 / np.pi) * 1367 * dr * (ωs * np.sin(np.radians(B6)) * np.sin(δ) +
                                     np.cos(np.radians(B6)) * np.cos(δ) * np.sin(ωs))
    Ramm = Ra / λ
    Rso = (0.75 + 2 * (10 ** -5) * A6) * Ramm

    if pd.isna(F11) or pd.isna(I11):
        Rn = 0.77 * Rsmm - (1.35 * (Rsmm / Rso) - 0.35) * (0.34 - 0.14 * np.sqrt(ed)) * (1360.8 * (10 ** -9) / λ) * (H11 + 273.16) ** 4
    else:
        Rn = (0.77 * Rsmm - (1.35 * (Rsmm / Rso) - 0.35) * (0.34 - 0.14 * np.sqrt(ed)) * (1360.8 * (10 ** -9) / λ) *
              ((I11 + 273.16) ** 4 + (J11 + 273.16) ** 4) / 2)

    ETrad = (Δ * Rn) / (Δ + γ_prime)

    if np.isnan(H11):
        ETaero = (γ * (90 / ((I11 + J11) / 2 + 273.16)) * U2 * (ea_Tmoy - ed)) / (Δ + γ_prime)
    else:
        ETaero = (γ * (90 / (H11 + 273.16)) * U2 * (ea_Tmoy - ed)) / (Δ + γ_prime)

    ETo = ETrad + ETaero
    print("K11 : somme irradiation ", K11)
    print("λ  : somme irradiation ",λ )
    print("Rsmm  : somme irradiation ",Rsmm )
    # Résultats
    # Output results
    print(f"P: {P} mb")
    print(f"λ: {λ} W/m²/mm")
    print(f"γ: {γ} mb/°C")
    print(f"U2: {U2} m/s")
    print(f"γ': {γ_prime} mb/°C")
    print(f"ea(Tmoy): {ea_Tmoy} mb")
    print(f"ed: {ed} mb")
    print(f"Δ: {Δ} mb/°C")
    print(f"dr: {dr}")
    print(f"δ: {δ} radian")
    print(f"ωs: {ωs} radian")
    print(f"Rsmm: {Rsmm} mm/jour")
    print(f"Ra: {Ra} W/m²")
    print(f"Ramm: {Ramm} mm/jour")
    print(f"Rso: {Rso} mm/jour")
    print(f"Rn: {Rn} mm/jour")
    print(f"ETrad: {ETrad} mm/jour")
    print(f"ETaero: {ETaero} mm/jour")
    print(f"ETo: {ETo} mm/jour")

    # Enregistrement dans la base de données
    ET0DRv.objects.create(
        Time_Stamp=ts_0101(target_date),
        value=round(ETo, 2),
        WSavg=L11,
        Tmax=I11,
        Tmin=J11,
        Tavg=H11,
        Hmax=F11,
        Hmin=G11,
        Raym=round(K11, 2),
        U2=U2,
        Delta=D11
    )

def ETO(target_date=None):
    # data = fetch_data_for_eto()
    if target_date is None:
        target_date = timezone.localtime(timezone.now()).date()

    # ✅ données de la journée précédente
    data_date = target_date - timedelta(days=1)

    # ✅ on fetch la veille
    data = fetch_data_for_eto(target_date=data_date)
    if data is None:
        print(f"⛔ ETO ignoré: données manquantes pour {data_date}")
        return None
    ts_save = ts_0101(target_date)
    A6 = data['altitude']  # Altitude (m)
    B6 = data['latitude']  # Latitude (degrés)
    C6 = 9.5  # Hauteur de l'anémomètre (m)
    D11 = data['day_of_year']  # Jour de l'année
    E6 = data['pressure']  # Pression moyenne (hPa)
    F11 = data['humidity_max']  # Humidité max (%)
    G11 = data['humidity_min']  # Humidité min (%)
    H11 = data['temp_avg']  # Température moyenne (°C)
    I11 = data['temp_max']  # Température max (°C)
    J11 = data['temp_min']  # Température min (°C)
    K11 = data['radiation_sum']  # Radiation solaire (MJ/m²)
    L11 = data['wind_speed_avg']  # Vitesse moyenne du vent (m/s)
    print("===== Données Météorologiques =====")
    print(f"Altitude (A6)                : {data['altitude']} m")
    print(f"Latitude (B6)                : {data['latitude']} °")
    print(f"Hauteur de l'anémomètre (C6): 9.5 m")
    print(f"Jour de l'année (D11)        : {data['day_of_year']}")
    print(f"Pression moyenne (E6)        : {data['pressure']} hPa")
    print(f"Humidité max (F11)           : {data['humidity_max']} %")
    print(f"Humidité min (G11)           : {data['humidity_min']} %")
    print(f"Température moyenne (H11)    : {data['temp_avg']} °C")
    print(f"Température max (I11)        : {data['temp_max']} °C")
    print(f"Température min (J11)        : {data['temp_min']} °C")
    print(f"Radiation solaire (K11)      : {data['radiation_sum']} MJ/m²")
    print(f"Vitesse moyenne du vent (L11): {data['wind_speed_avg']} m/s")

    # Calculs
    P = 1013 * ((293 - 0.0065 * A6) / 293) ** 5.256
    λ = 694.5 * (1 - 0.000946 * H11)
    γ = 0.2805555 * E6 / (0.622 * λ)
    U2 = 4.868 * L11 / np.log(67.75 * C6 - 5.42)
    γ_prime = γ * (1 + 0.34 * U2)

    if np.isnan(H11):
        ea_Tmoy = 6.108 * np.exp((17.27 * (I11 + J11) / 2) / ((I11 + J11) / 2 + 237.3))
    else:
        ea_Tmoy = 6.108 * np.exp((17.27 * H11) / (H11 + 237.3))

    if pd.isna(F11) or pd.isna(I11):
        ed = ea_Tmoy * E6 / 100
    else:
        ed = (6.108 * np.exp((17.27 * J11) / (J11 + 237.3)) * F11 +
              6.108 * np.exp((17.27 * I11) / (I11 + 237.3)) * G11) / 200

    Δ = 4098.171 * ea_Tmoy / (ea_Tmoy + 237.3) ** 2
    dr = 1 + 0.033 * np.cos(2 * np.pi * D11 / 365)
    δ = 0.4093 * np.sin(2 * np.pi * (284 + D11) / 365)
    ωs = np.arccos(-np.tan(np.radians(B6)) * np.tan(δ))
    Rsmm = K11 / λ
    Ra = (24 / np.pi) * 1367 * dr * (ωs * np.sin(np.radians(B6)) * np.sin(δ) +
                                     np.cos(np.radians(B6)) * np.cos(δ) * np.sin(ωs))
    Ramm = Ra / λ
    Rso = (0.75 + 2 * (10 ** -5) * A6) * Ramm

    if pd.isna(F11) or pd.isna(I11):
        Rn = 0.77 * Rsmm - (1.35 * (Rsmm / Rso) - 0.35) * (0.34 - 0.14 * np.sqrt(ed)) * (1360.8 * (10 ** -9) / λ) * (H11 + 273.16) ** 4
    else:
        Rn = (0.77 * Rsmm - (1.35 * (Rsmm / Rso) - 0.35) * (0.34 - 0.14 * np.sqrt(ed)) * (1360.8 * (10 ** -9) / λ) *
              ((I11 + 273.16) ** 4 + (J11 + 273.16) ** 4) / 2)

    ETrad = (Δ * Rn) / (Δ + γ_prime)

    if np.isnan(H11):
        ETaero = (γ * (90 / ((I11 + J11) / 2 + 273.16)) * U2 * (ea_Tmoy - ed)) / (Δ + γ_prime)
    else:
        ETaero = (γ * (90 / (H11 + 273.16)) * U2 * (ea_Tmoy - ed)) / (Δ + γ_prime)

    ETo = ETrad + ETaero
    print("K11 : somme irradiation ", K11)
    print("λ  : somme irradiation ",λ )
    print("Rsmm  : somme irradiation ",Rsmm )
    # Résultats
    # Output results
    print(f"P: {P} mb")
    print(f"λ: {λ} W/m²/mm")
    print(f"γ: {γ} mb/°C")
    print(f"U2: {U2} m/s")
    print(f"γ': {γ_prime} mb/°C")
    print(f"ea(Tmoy): {ea_Tmoy} mb")
    print(f"ed: {ed} mb")
    print(f"Δ: {Δ} mb/°C")
    print(f"dr: {dr}")
    print(f"δ: {δ} radian")
    print(f"ωs: {ωs} radian")
    print(f"Rsmm: {Rsmm} mm/jour")
    print(f"Ra: {Ra} W/m²")
    print(f"Ramm: {Ramm} mm/jour")
    print(f"Rso: {Rso} mm/jour")
    print(f"Rn: {Rn} mm/jour")
    print(f"ETrad: {ETrad} mm/jour")
    print(f"ETaero: {ETaero} mm/jour")
    print(f"ETo: {ETo} mm/jour")

    # Enregistrement dans la base de données
    ET0o.objects.create(
        Time_Stamp=ts_save,
        value=round(ETo,2),
        WSavg=L11,
        Tmax=I11,
        Tmin=J11,
        Tavg=H11,
        Hmax=F11,
        Hmin=G11,
        Raym=round(K11, 2),
        U2=U2,
        Delta=D11
    )

from django.utils.timezone import now as dj_now

def fwijob(request):
    fwi()  # Assurez-vous que cette fonction est définie ailleurs
    print("les mesures fwi : ",fwi())
    return HttpResponse("Tâche exécutée avec succès.")

# def et0_job(request):
#     current_time = dj_now()  # Utilisation de la gestion des fuseaux horaires Django
#     current_date = current_time.date()

#     print(f"📅 Date actuelle : {current_date}")
#     print(f"⏳ Heure actuelle : {current_time.time()}")
#     fetch_data_for_eto()
#     fetch_data_for_etoDR()
#     fetch_data_for_etoDRv()
#     # Vérifier si ET0 a déjà été calculé aujourd'hui
#     last_eto_entry = ET0o.objects.filter(Time_Stamp__date=current_date).last()
#     last_eto_entry1 = ET0DR.objects.filter(Time_Stamp__date=current_date).last()
#     last_eto_entry2 = ET0DRv.objects.filter(Time_Stamp__date=current_date).last()
#     last_eto_entry3 = ETODR_FAO56.objects.filter(Time_Stamp__date=current_date).last()     # j'ai ajouter cette ligne
#     last_eto_entry4 = ETOSensCap_FAO56.objects.filter(Time_Stamp__date=current_date).last()     # j'ai ajouter cette ligne
#     last_eto_entry5 = ETODRV_FAO56.objects.filter(Time_Stamp__date=current_date).last()     # j'ai ajouter cette ligne

#     print(f"🔍 Dernière entrée ET0 : {last_eto_entry}")
#     print(f"🔍 Dernière entrée ET0 Dragino : {last_eto_entry1}")
#     print(f"🔍 Dernière entrée ET0 Dragino visiogreen : {last_eto_entry2}")
#     print(f"🔍 Dernière entrée ET0 DR PM FAO56 : {last_eto_entry3}")                         # j'ai ajouté cette ligne
#     print(f"🔍 Dernière entrée ET0 S PM FAO56 : {last_eto_entry4}")                          # j'ai ajouté cette ligne
#     print(f"🔍 Dernière entrée ET0 DRV PM FAO56 : {last_eto_entry5}")                          # j'ai ajouté cette ligne


#     # Vérifier si on est entre 1h et 2h du matin
#     if 0 <= current_time.hour < 2:
#         if not last_eto_entry and not last_eto_entry1:
#             print("🚀 Calcul simultané de ET0 et ET0 Dragino...")
#             ETO()
#             ETODR()
#             ETODRv()
#             ETODR_FAO56_DR()                                                              # j'ai ajouté cette ligne
#             ETOS_FAO56_S()                                                                # j'ai ajouté cette ligne
#             ETODRV_FAO56_DRV()                                                              # j'ai ajouté cette ligne

#             print(f"✅ ET0 et ET0 Dragino calculés et enregistrés à {current_time}")
#         else:
#             if last_eto_entry:
#                 print(f"⚠️ ET0 déjà calculé aujourd'hui à : {last_eto_entry.Time_Stamp}")
#             else:
#                 print("✅ Calcul de ET0...")
#                 ETO()

#             if last_eto_entry1:
#                 print(f"⚠️ ET0 Dragino déjà calculé aujourd'hui à : {last_eto_entry1.Time_Stamp}")
#             else:
#                 print("✅ Calcul de ET0 Dragino...")
#                 ETODR()

#             if last_eto_entry2:
#                 print(f"⚠️ ET0 Dragino - visiogreen déjà calculé aujourd'hui à : {last_eto_entry2.Time_Stamp}")
#             else:
#                 print("✅ Calcul de ET0 Dragino..-visiogreen.")
#                 ETODRv()

#             if last_eto_entry3:                                                                                            # j'ai ajouté cette ligne
#                 print(f"⚠️ ET0 PM FAO56 déjà calculé aujourd'hui à : {last_eto_entry3.Time_Stamp}")                       # j'ai ajouté cette ligne
#             else:                                                                                                         # j'ai ajouté cette ligne
#                 print("✅ Calcul de ET0 DPM FAO56.")                                                                     # j'ai ajouté cette ligne
#                 ETODR_FAO56_DR()                                                                                           # j'ai ajouté cette ligne

#             if last_eto_entry4:                                                                                            # j'ai ajouté cette ligne
#                 print(f"⚠️ ET0 PM FAO56 déjà calculé aujourd'hui à : {last_eto_entry4.Time_Stamp}")                       # j'ai ajouté cette ligne
#             else:                                                                                                         # j'ai ajouté cette ligne
#                 print("✅ Calcul de ET0 DPM FAO56.")                                                                     # j'ai ajouté cette ligne
#                 ETOS_FAO56_S()                                                                                           # j'ai ajouté cette ligne

#             if last_eto_entry5:                                                                                            # j'ai ajouté cette ligne
#                 print(f"⚠️ ET0 PM FAO56 déjà calculé aujourd'hui à : {last_eto_entry5.Time_Stamp}")                       # j'ai ajouté cette ligne
#             else:                                                                                                         # j'ai ajouté cette ligne
#                 print("✅ Calcul de ET0 DPM FAO56.")                                                                     # j'ai ajouté cette ligne
#                 ETODRV_FAO56_DRV()                                                                                           # j'ai ajouté cette ligne
#     else:
#         print("⏳ Il n'est pas encore temps de calculer ET0 (attendre entre 1h et 2h du matin).")

#     return render(request, "job.html", {})
# from django.shortcuts import render
# from django.utils.timezone import now as dj_now
# from datetime import timedelta

def et0_job(request):
    current_time = dj_now()
    current_date = current_time.date()

    print(f"📅 Date actuelle : {current_date}")
    print(f"⏳ Heure actuelle : {current_time.time()}")

    # ===============================
    # 🔹 Sécurisation des fetch (sans toucher aux fetch_* )
    # ===============================
    data_ok_eto = True
    data_ok_dr = True
    data_ok_drv = True

    try:
        fetch_data_for_eto()
    except Exception as e:
        print(f"⚠️ fetch_data_for_eto ignoré : {e}")
        data_ok_eto = False

    try:
        fetch_data_for_etoDR()
    except Exception as e:
        print(f"⚠️ fetch_data_for_etoDR ignoré : {e}")
        data_ok_dr = False

    try:
        fetch_data_for_etoDRv()
    except Exception as e:
        print(f"⚠️ fetch_data_for_etoDRv ignoré : {e}")
        data_ok_drv = False

    # ===============================
    # 🔹 Vérification des entrées du jour
    # ===============================
    last_eto_entry = ET0o.objects.filter(Time_Stamp__date=current_date).last()
    last_eto_entry1 = ET0DR.objects.filter(Time_Stamp__date=current_date).last()
    last_eto_entry2 = ET0DRv.objects.filter(Time_Stamp__date=current_date).last()
    # last_eto_entry3 = ETODR_FAO56.objects.filter(Time_Stamp__date=current_date).last()
    # last_eto_entry4 = ETOSensCap_FAO56.objects.filter(Time_Stamp__date=current_date).last()
    # last_eto_entry5 = ETODRV_FAO56.objects.filter(Time_Stamp__date=current_date).last()

    # print(f"🔍 Dernière entrée ET0 : {last_eto_entry}")
    # print(f"🔍 Dernière entrée ET0 Dragino : {last_eto_entry1}")
    # print(f"🔍 Dernière entrée ET0 Dragino visiogreen : {last_eto_entry2}")
    # print(f"🔍 Dernière entrée ET0 DR PM FAO56 : {last_eto_entry3}")
    # print(f"🔍 Dernière entrée ET0 S PM FAO56 : {last_eto_entry4}")
    # print(f"🔍 Dernière entrée ET0 DRV PM FAO56 : {last_eto_entry5}")

    # ===============================
    # 🔹 Fenêtre de calcul
    # ===============================
    if 0 <= current_time.hour < 2:
        print("🕒 Fenêtre de calcul active")

        # --- ET0 ---
        if data_ok_eto and not last_eto_entry:
            print("✅ Calcul ET0...")
            try:
                ETO()
            except Exception as e:
                print(f"⛔ ETO ignoré (erreur) : {e}")
        elif not data_ok_eto:
            print("⛔ ET0 ignoré (données nulles)")
        else:
            print(f"⚠️ ET0 déjà calculé à : {last_eto_entry.Time_Stamp}")

        # --- ET0 Dragino ---
        if data_ok_dr and not last_eto_entry1:
            print("✅ Calcul ET0 Dragino...")
            try:
                ETODR()
            except Exception as e:
                print(f"⛔ ETODR ignoré (erreur) : {e}")
        elif not data_ok_dr:
            print("⛔ ET0 Dragino ignoré (données nulles)")
        else:
            print(f"⚠️ ET0 Dragino déjà calculé à : {last_eto_entry1.Time_Stamp}")

        # --- ET0 Dragino Visiogreen ---
        if data_ok_drv and not last_eto_entry2:
            print("✅ Calcul ET0 Dragino - visiogreen...")
            try:
                ETODRv()
            except Exception as e:
                print(f"⛔ ETODRv ignoré (erreur) : {e}")
        elif not data_ok_drv:
            print("⛔ ET0 Dragino Visiogreen ignoré (données nulles)")
        else:
            print(f"⚠️ ET0 Dragino - visiogreen déjà calculé à : {last_eto_entry2.Time_Stamp}")

        # --- ET0 DR PM FAO56 ---
        # if data_ok_dr and not last_eto_entry3:
        #     print("✅ Calcul ET0 DR PM FAO56...")
        #     try:
        #         ETODR_FAO56_DR()
        #     except Exception as e:
        #         print(f"⛔ ETODR_FAO56_DR ignoré (erreur) : {e}")
        # elif not data_ok_dr:
        #     print("⛔ ET0 DR PM FAO56 ignoré (données nulles)")
        # else:
        #     print(f"⚠️ ET0 DR PM FAO56 déjà calculé à : {last_eto_entry3.Time_Stamp}")

        # # --- ET0 S PM FAO56 ---
        # if data_ok_eto and not last_eto_entry4:
        #     print("✅ Calcul ET0 S PM FAO56...")
        #     try:
        #         ETOS_FAO56_S()
        #     except Exception as e:
        #         print(f"⛔ ETOS_FAO56_S ignoré (erreur) : {e}")
        # elif not data_ok_eto:
        #     print("⛔ ET0 S PM FAO56 ignoré (données nulles)")
        # else:
        #     print(f"⚠️ ET0 S PM FAO56 déjà calculé à : {last_eto_entry4.Time_Stamp}")

        # # --- ET0 DRV PM FAO56 ---
        # if data_ok_drv and not last_eto_entry5:
        #     print("✅ Calcul ET0 DRV PM FAO56...")
        #     try:
        #         ETODRV_FAO56_DRV()
        #     except Exception as e:
        #         print(f"⛔ ETODRV_FAO56_DRV ignoré (erreur) : {e}")
        # elif not data_ok_drv:
        #     print("⛔ ET0 DRV PM FAO56 ignoré (données nulles)")
        # else:
        #     print(f"⚠️ ET0 DRV PM FAO56 déjà calculé à : {last_eto_entry5.Time_Stamp}")

    else:
        print("⏳ Il n'est pas encore temps de calculer ET0 (attendre entre 0h et 2h du matin).")

    return render(request, "job.html", {})
def et0_job1(request):
    current_time = dj_now()
    current_date = current_time.date()

    print(f"📅 Date actuelle : {current_date}")
    print(f"⏳ Heure actuelle : {current_time.time()}")

    # ===============================
    # 🔹 Sécurisation des fetch (sans toucher aux fetch_* )
    # ===============================
    data_ok_eto = True
    data_ok_dr = True
    data_ok_drv = True

    try:
        fetch_data_for_eto()
    except Exception as e:
        print(f"⚠️ fetch_data_for_eto ignoré : {e}")
        data_ok_eto = False

    try:
        fetch_data_for_etoDR()
    except Exception as e:
        print(f"⚠️ fetch_data_for_etoDR ignoré : {e}")
        data_ok_dr = False

    try:
        fetch_data_for_etoDRv()
    except Exception as e:
        print(f"⚠️ fetch_data_for_etoDRv ignoré : {e}")
        data_ok_drv = False

    # ===============================
    # 🔹 Vérification des entrées du jour
    # ===============================
    # last_eto_entry = ET0o.objects.filter(Time_Stamp__date=current_date).last()
    # last_eto_entry1 = ET0DR.objects.filter(Time_Stamp__date=current_date).last()
    # last_eto_entry2 = ET0DRv.objects.filter(Time_Stamp__date=current_date).last()
    last_eto_entry3 = ETODR_FAO56.objects.filter(Time_Stamp__date=current_date).last()
    last_eto_entry4 = ETOSensCap_FAO56.objects.filter(Time_Stamp__date=current_date).last()
    last_eto_entry5 = ETODRV_FAO56.objects.filter(Time_Stamp__date=current_date).last()

    # print(f"🔍 Dernière entrée ET0 : {last_eto_entry}")
    # print(f"🔍 Dernière entrée ET0 Dragino : {last_eto_entry1}")
    # print(f"🔍 Dernière entrée ET0 Dragino visiogreen : {last_eto_entry2}")
    # print(f"🔍 Dernière entrée ET0 DR PM FAO56 : {last_eto_entry3}")
    # print(f"🔍 Dernière entrée ET0 S PM FAO56 : {last_eto_entry4}")
    # print(f"🔍 Dernière entrée ET0 DRV PM FAO56 : {last_eto_entry5}")

    # ===============================
    # 🔹 Fenêtre de calcul
    # ===============================
    if 0 <= current_time.hour < 2:
        print("🕒 Fenêtre de calcul active")

        # # --- ET0 ---
        # if data_ok_eto and not last_eto_entry:
        #     print("✅ Calcul ET0...")
        #     try:
        #         ETO()
        #     except Exception as e:
        #         print(f"⛔ ETO ignoré (erreur) : {e}")
        # elif not data_ok_eto:
        #     print("⛔ ET0 ignoré (données nulles)")
        # else:
        #     print(f"⚠️ ET0 déjà calculé à : {last_eto_entry.Time_Stamp}")

        # # --- ET0 Dragino ---
        # if data_ok_dr and not last_eto_entry1:
        #     print("✅ Calcul ET0 Dragino...")
        #     try:
        #         ETODR()
        #     except Exception as e:
        #         print(f"⛔ ETODR ignoré (erreur) : {e}")
        # elif not data_ok_dr:
        #     print("⛔ ET0 Dragino ignoré (données nulles)")
        # else:
        #     print(f"⚠️ ET0 Dragino déjà calculé à : {last_eto_entry1.Time_Stamp}")

        # # --- ET0 Dragino Visiogreen ---
        # if data_ok_drv and not last_eto_entry2:
        #     print("✅ Calcul ET0 Dragino - visiogreen...")
        #     try:
        #         ETODRv()
        #     except Exception as e:
        #         print(f"⛔ ETODRv ignoré (erreur) : {e}")
        # elif not data_ok_drv:
        #     print("⛔ ET0 Dragino Visiogreen ignoré (données nulles)")
        # else:
        #     print(f"⚠️ ET0 Dragino - visiogreen déjà calculé à : {last_eto_entry2.Time_Stamp}")

        # --- ET0 DR PM FAO56 ---
        if data_ok_dr and not last_eto_entry3:
            print("✅ Calcul ET0 DR PM FAO56...")
            try:
                ETODR_FAO56_DR()
            except Exception as e:
                print(f"⛔ ETODR_FAO56_DR ignoré (erreur) : {e}")
        elif not data_ok_dr:
            print("⛔ ET0 DR PM FAO56 ignoré (données nulles)")
        else:
            print(f"⚠️ ET0 DR PM FAO56 déjà calculé à : {last_eto_entry3.Time_Stamp}")

        # --- ET0 S PM FAO56 ---
        if data_ok_eto and not last_eto_entry4:
            print("✅ Calcul ET0 S PM FAO56...")
            try:
                ETOS_FAO56_S()
            except Exception as e:
                print(f"⛔ ETOS_FAO56_S ignoré (erreur) : {e}")
        elif not data_ok_eto:
            print("⛔ ET0 S PM FAO56 ignoré (données nulles)")
        else:
            print(f"⚠️ ET0 S PM FAO56 déjà calculé à : {last_eto_entry4.Time_Stamp}")

        # --- ET0 DRV PM FAO56 ---
        if data_ok_drv and not last_eto_entry5:
            print("✅ Calcul ET0 DRV PM FAO56...")
            try:
                ETODRV_FAO56_DRV()
            except Exception as e:
                print(f"⛔ ETODRV_FAO56_DRV ignoré (erreur) : {e}")
        elif not data_ok_drv:
            print("⛔ ET0 DRV PM FAO56 ignoré (données nulles)")
        else:
            print(f"⚠️ ET0 DRV PM FAO56 déjà calculé à : {last_eto_entry5.Time_Stamp}")

    else:
        print("⏳ Il n'est pas encore temps de calculer ET0 (attendre entre 0h et 2h du matin).")

    return render(request, "job1.html", {})
from django.utils import timezone
import pytz

# def wsopen(request):
#     maroc_tz = pytz.timezone('Africa/Casablanca')
#     now = timezone.now().astimezone(maroc_tz).replace(hour=0, minute=0, second=0, microsecond=0)
#     print("La date aujourd'hui est ", now)

#     current_time = timezone.now().astimezone(maroc_tz)
#     current_date = current_time.date()  # Date actuelle sans l'heure
#     print("Le temps de comparaison : ", current_time)

#     # Récupération des données à partir de minuit
#     hm = Data2.objects.filter(Time_Stamp__gte=now)
#     hm1 = Ray2.objects.filter(DateRay__gte=now)
#     # send_simple_message()
#     # Calcul des valeurs max et min
#     light_max = hm.aggregate(Max('Light_Intensity'))['Light_Intensity__max'] or 0
#     light_min = hm.aggregate(Min('Light_Intensity'))['Light_Intensity__min'] or 0
#     light_avg = hm.aggregate(Avg('Light_Intensity'))['Light_Intensity__avg'] or 0
#     uv_max= hm.aggregate(Max('UV_Index'))['UV_Index__max'] or 0
#     uv_min= hm.aggregate(Min('UV_Index'))['UV_Index__min'] or 0
#     uv_avg= hm.aggregate(Avg('UV_Index'))['UV_Index__avg'] or 0
#     Tmmax = hm.aggregate(Max('Temp'))['Temp__max'] or 0
#     Tmmin = hm.aggregate(Min('Temp'))['Temp__min'] or 0
#     Hx = hm.aggregate(Max('Hum'))['Hum__max'] or 0
#     Hm = hm.aggregate(Min('Hum'))['Hum__min'] or 0
#     Sx = hm.aggregate(Max('Wind_Speed'))['Wind_Speed__max'] or 0
#     Sm = hm.aggregate(Min('Wind_Speed'))['Wind_Speed__min'] or 0
#     Rx = hm1.aggregate(Max('Ray'))['Ray__max'] or 0
#     Rm = hm1.aggregate(Min('Ray'))['Ray__min'] or 0
#     Tmavg = hm.aggregate(Avg('Temp'))['Temp__avg'] or 0
#     Havg = hm.aggregate(Avg('Hum'))['Hum__avg'] or 0
#     Savg = hm.aggregate(Avg('Wind_Speed'))['Wind_Speed__avg'] or 0
#     Ravg = hm1.aggregate(Avg('Ray'))['Ray__avg'] or 0

#     # Fonction pour récupérer les précipitations sur une période donnée
#     def get_rain_sum(start_time):
#         return Data2.objects.filter(Time_Stamp__gte=start_time, Time_Stamp__lte=current_time).aggregate(Sum('Rain'))['Rain__sum'] or 0
#     def get_rain_sum_(start_time):
#         return Data2.objects.filter(Time_Stamp__gte=start_time, Time_Stamp__lte=current_time).aggregate(Sum('Rain_act'))['Rain_act__sum'] or 0

#     one_hour_ago = current_time - timezone.timedelta(hours=1)
#     eight_hours_ago = current_time - timezone.timedelta(hours=8)
#     one_day_ago = current_time - timezone.timedelta(days=1)
#     one_week_ago = current_time - timezone.timedelta(days=7)

#     p1h = round(get_rain_sum(one_hour_ago), 2)
#     p8h = round(get_rain_sum(eight_hours_ago), 2)
#     p24h = round(get_rain_sum(one_day_ago), 2)
#     p1w = round(get_rain_sum(one_week_ago), 2)

#     # p1h_ = round(get_rain_sum_(one_hour_ago), 2)
#     # p8h_ = round(get_rain_sum_(eight_hours_ago), 2)
#     # p24h_ = round(get_rain_sum_(one_day_ago), 2)
#     # p1w_ = round(get_rain_sum_(one_week_ago), 2)
#     last_two_rain_acc_1 = Data2.objects.order_by('-Time_Stamp')[:2]
#     print("last_record databases :", last_two_rain_acc_1)
#     # Récupérer les enregistrements par ordre décroissant de date
#     all_rain = Data2.objects.order_by('-Time_Stamp')

#     # Initialiser une liste pour stocker les 2 enregistrements valides
#     last_two_rain_acc = []

#     for record in all_rain:
#         if not last_two_rain_acc:
#             # Premier enregistrement, on l'ajoute
#             last_two_rain_acc.append(record)
#         else:
#             # Comparer avec le précédent : au moins 5 minutes d’écart ?
#             time_diff = last_two_rain_acc[0].Time_Stamp - record.Time_Stamp
#             if time_diff >= timedelta(minutes=5):
#                 last_two_rain_acc.append(record)
#                 break  # On a trouvé les deux, on peut arrêter
#     one_hour = current_time - datetime.timedelta(hours=1)
#     huit_hour = current_time - datetime.timedelta(hours=8)
#     one_day = current_time - datetime.timedelta(days=1)
#     week = current_time - datetime.timedelta(days=7)
#     posts = Data2.objects.filter(Time_Stamp__gte=one_hour, Time_Stamp__lte=current_time)
#     post8 = Data2.objects.filter(Time_Stamp__gte=huit_hour, Time_Stamp__lte=current_time)
#     post24 = Data2.objects.filter(Time_Stamp__gte=one_day, Time_Stamp__lte=current_time)
#     postweek = Data2.objects.filter(Time_Stamp__gte=week, Time_Stamp__lte=current_time)

#     def get_rain_sum_(queryset):
#         rain_sum = queryset.aggregate(Sum('Rain'))['Rain__sum'] or 0
#         rain_sum = round(rain_sum,2)
#         return round(rain_sum, 2) if rain_sum is not None else 0
#     # fwi()
#     p1h = get_rain_sum_(posts)
#     p8h = get_rain_sum_(post8)
#     p24h = get_rain_sum_(post24)
#     p1w = get_rain_sum_(postweek)

#     # print("last_record.last_two_rain_acc : ", last_two_rain_acc.Rain_acc,type(last_two_rain_acc.Rain_acc))
#     tab = Data2.objects.last()
#     tab2 = Ray2.objects.last()
#     eto = ET0o.objects.order_by('-Time_Stamp').first()
#     lstfwi = DataFwiO.objects.last()
#     # derniers_enregistrements = wsd.objects.exclude(Rg=0).order_by('-Time_Stamp')[:2]
#     data = fetch_data_for_eto()
#     altitude = data['altitude']  # Altitude (m)
#     latitude = data['latitude']  # Latitude (degrés)
#     C6 = 2  # Hauteur de l'anémomètre (m)
#     day_of_year = data['day_of_year']  # Jour de l'année
#     pressure = data['pressure']  # Pression moyenne (hPa)
#     humidity_max = data['humidity_max']  # Humidité max (%)
#     humidity_min = data['humidity_min']  # Humidité min (%)
#     temp_avg = data['temp_avg']  # Température moyenne (°C)
#     temp_max = data['temp_max']  # Température max (°C)
#     temp_min = data['temp_min']  # Température min (°C)
#     radiation_sum = data['radiation_sum']/24 # Radiation solaire (MJ/m²)
#     wind_speed_avg = data['wind_speed_avg']  # Vitesse moyenne du vent (m/s)
#     context = {
#     'tab': tab, 'tab2': tab2, 'eto': eto, 'p1w': p1w, 'p24h': p24h, 'p8h': p8h, 'p1h': p1h,
#     'rg_data': last_two_rain_acc,'Rx': Rx, 'Rm': Rm, 'Sx': Sx, 'Sm': Sm, 'Hx': Hx, 'Hm': Hm, 'Tmmax': Tmmax, 'Tmmin': Tmmin,
#     'Tmavg': round(Tmavg, 2), 'Havg': round(Havg, 2), 'Savg': round(Savg, 2), 'Ravg': round(Ravg, 2),
#     'lstfwi': lstfwi,'wind_speed_avg':wind_speed_avg,
#     'radiation_sum':radiation_sum,'temp_min':temp_min,'temp_max':temp_max,'temp_avg':temp_avg,'humidity_min':humidity_min,'humidity_max':humidity_max,'altitude':altitude,'latitude':latitude,
#     'light_max':round(light_max,2),'light_min':round(light_min,2),'light_avg':round(light_avg,2),'uv_max':uv_max,'uv_min':uv_min,'uv_avg':round(uv_avg,2),
#     }
#     return render(request, "ws_open.html", context)
from django.db.models import Max, Min, Avg, Sum
from django.utils import timezone
import pytz
import datetime
from datetime import timedelta

def wsopen(request):
    maroc_tz = pytz.timezone('Africa/Casablanca')
    current_time = timezone.now().astimezone(maroc_tz)
    now0 = current_time.replace(hour=0, minute=0, second=0, microsecond=0)

    # =========================
    # 1) Querysets (sans exécuter)
    # =========================
    hm = Data2.objects.filter(Time_Stamp__gte=now0)
    hm1 = Ray2.objects.filter(DateRay__gte=now0)

    # =========================
    # 2) 1 seule requête aggregate Data2
    # =========================
    agg_data2 = hm.aggregate(
        light_max=Max('Light_Intensity'),
        light_min=Min('Light_Intensity'),
        light_avg=Avg('Light_Intensity'),

        uv_max=Max('UV_Index'),
        uv_min=Min('UV_Index'),
        uv_avg=Avg('UV_Index'),

        tmax=Max('Temp'),
        tmin=Min('Temp'),
        tavg=Avg('Temp'),

        hmax=Max('Hum'),
        hmin=Min('Hum'),
        havg=Avg('Hum'),

        smax=Max('Wind_Speed'),
        smin=Min('Wind_Speed'),
        savg=Avg('Wind_Speed'),
    )

    # Remplacer None par 0
    def nz(v):
        return v if v is not None else 0

    light_max = nz(agg_data2['light_max'])
    light_min = nz(agg_data2['light_min'])
    light_avg = nz(agg_data2['light_avg'])

    uv_max = nz(agg_data2['uv_max'])
    uv_min = nz(agg_data2['uv_min'])
    uv_avg = nz(agg_data2['uv_avg'])

    Tmmax = nz(agg_data2['tmax'])
    Tmmin = nz(agg_data2['tmin'])
    Tmavg = nz(agg_data2['tavg'])

    Hx = nz(agg_data2['hmax'])
    Hm_ = nz(agg_data2['hmin'])
    Havg = nz(agg_data2['havg'])

    Sx = nz(agg_data2['smax'])
    Sm = nz(agg_data2['smin'])
    Savg = nz(agg_data2['savg'])

    # =========================
    # 3) 1 seule requête aggregate Ray2
    # =========================
    agg_ray = hm1.aggregate(
        Rx=Max('Ray'),
        Rm=Min('Ray'),
        Ravg=Avg('Ray'),
    )
    Rx = nz(agg_ray['Rx'])
    Rm = nz(agg_ray['Rm'])
    Ravg = nz(agg_ray['Ravg'])

    # =========================
    # 4) Pluie (4 requêtes max)
    # =========================
    one_hour = current_time - timedelta(hours=1)
    eight_hours = current_time - timedelta(hours=8)
    one_day = current_time - timedelta(days=1)
    one_week = current_time - timedelta(days=7)

    def rain_sum(start):
        return Data2.objects.filter(Time_Stamp__gte=start, Time_Stamp__lte=current_time)\
            .aggregate(total=Sum('Rain'))['total'] or 0

    p1h = round(rain_sum(one_hour), 2)
    p8h = round(rain_sum(eight_hours), 2)
    p24h = round(rain_sum(one_day), 2)
    p1w = round(rain_sum(one_week), 2)

    # =========================
    # 5) last_two_rain_acc : éviter boucle sur toute la table
    # =========================
    recent = list(Data2.objects.order_by('-Time_Stamp')[:300])  # limite
    last_two_rain_acc = []
    for rec in recent:
        if not last_two_rain_acc:
            last_two_rain_acc.append(rec)
        else:
            if last_two_rain_acc[0].Time_Stamp - rec.Time_Stamp >= timedelta(minutes=5):
                last_two_rain_acc.append(rec)
                break

    # =========================
    # 6) derniers enregistrements (1 requête chacun)
    # =========================
    tab = Data2.objects.order_by('-Time_Stamp').first()
    tab2 = Ray2.objects.order_by('-DateRay').first()
    eto = ET0o.objects.order_by('-Time_Stamp').first()
    lstfwi = DataFwiO.objects.order_by('-id').first()

    # ⚠️ IMPORTANT : ne pas recalculer fetch_data_for_eto ici (très lourd)
    # => si tu veux quand même afficher des valeurs météo de ET0, utilise l'objet ET0 (déjà calculé)
    # sinon tu peux garder fetch_data_for_eto mais ça ralentira fortement.

    context = {
        'tab': tab, 'tab2': tab2, 'eto': eto, 'p1w': p1w, 'p24h': p24h, 'p8h': p8h, 'p1h': p1h,
        'rg_data': last_two_rain_acc,
        'Rx': Rx, 'Rm': Rm, 'Sx': Sx, 'Sm': Sm, 'Hx': Hx, 'Hm': Hm_, 'Tmmax': Tmmax, 'Tmmin': Tmmin,
        'Tmavg': round(Tmavg, 2), 'Havg': round(Havg, 2), 'Savg': round(Savg, 2), 'Ravg': round(Ravg, 2),
        'lstfwi': lstfwi,
        'light_max': round(light_max, 2), 'light_min': round(light_min, 2), 'light_avg': round(light_avg, 2),
        'uv_max': uv_max, 'uv_min': uv_min, 'uv_avg': round(uv_avg, 2),
    }

    return render(request, "ws_open.html", context)

REQUIRED_FIELDS = [
    'temp_avg',
    'temp_max',
    'temp_min',
    'radiation_sum',
    'humidity_max',
    'humidity_min',
    'wind_speed_avg',
    'pressure',
    'latitude',
    'altitude',
    'day_of_year'
]
def validate_eto_data(data):
    if not data:
        logger.warning("ET0 non calculé : aucune donnée récupérée")
        return False

    missing = [
        field for field in REQUIRED_FIELDS
        if data.get(field) is None
    ]

    if missing:
        logger.warning(
            "ET0 non calculé : données manquantes → %s",
            ", ".join(missing)
        )
        return False

    return True

# def wsopen1(request):
#     now = (datetime.datetime.now()).replace(hour=0, minute=0, second=0, microsecond=0)
#     print(now)
#     current_time = datetime.datetime.now()
#     current_date = current_time.date()
#     print(current_time)
#     #ETODR_FAO56_DR()
#     #ETOS_FAO56_S()
#     #ETODRV_FAO56_DRV()
#     # last_eto_entry = ET0o.objects.filter(Time_Stamp__date=current_date).last()

#     # if current_time.hour == 1 and not last_eto_entry:
#     #     ETO()
#     #     print("ET0 calculé et enregistré.")
#     # else:
#     #     print("ET0 a déjà été calculé aujourd'hui ou il n'est pas encore temps.")

#     hm = wsd.objects.filter(Time_Stamp__gte=now)
#     lstfwi = DataFwiO.objects.last()

# ###################################################################
#     th = rs_temp.objects.filter(Time_Stamp__gte=now)

#     """ Température1 """
#     Tmmax1 = th.aggregate(Max('temp1'))['temp1__max']
#     Tmmin1 = th.aggregate(Min('temp1'))['temp1__min']
#     Tmavg1 = th.aggregate(Avg('temp1'))['temp1__avg'] or 0

#     """ Température2 """
#     Tmmax2 = th.aggregate(Max('temp2'))['temp2__max']
#     Tmmin2 = th.aggregate(Min('temp2'))['temp2__min']
#     Tmavg2 = th.aggregate(Avg('temp2'))['temp2__avg'] or 0

#     """ Humidité 1"""
#     Hx1 = th.aggregate(Max('hum1'))['hum1__max']
#     Hm1 = th.aggregate(Min('hum1'))['hum1__min']
#     Havg1 = th.aggregate(Avg('hum1'))['hum1__avg'] or 0

#     """ Humidité2 """
#     Hx2 = th.aggregate(Max('hum2'))['hum2__max']
#     Hm2 = th.aggregate(Min('hum2'))['hum2__min']
#     Havg2 = th.aggregate(Avg('hum2'))['hum2__avg'] or 0

# ####################################################################

#     # ETODR()
#     """ Température """
#     Tmmax = hm.aggregate(Max('TEM'))['TEM__max']
#     Tmmin = hm.aggregate(Min('TEM'))['TEM__min']
#     Tmavg = hm.aggregate(Avg('TEM'))['TEM__avg'] or 0

#     """ Humidité """
#     Hx = hm.aggregate(Max('HUM'))['HUM__max']
#     Hm = hm.aggregate(Min('HUM'))['HUM__min']
#     Havg = hm.aggregate(Avg('HUM'))['HUM__avg'] or 0

#     """ Vitesse du vent """
#     Sx = hm.aggregate(Max('wind_speed'))['wind_speed__max']
#     print("sppped max :",Sx)
#     Sm = hm.aggregate(Min('wind_speed'))['wind_speed__min']
#     Savg = hm.aggregate(Avg('wind_speed'))['wind_speed__avg'] or 0

#     """ Illumination """
#     Rx = hm.aggregate(Max('illumination'))['illumination__max']
#     Rm = hm.aggregate(Min('illumination'))['illumination__min']
#     Ravg = hm.aggregate(Avg('illumination'))['illumination__avg'] or 0

#     """ Pluie """
#     one_hour = current_time - datetime.timedelta(hours=1)
#     huit_hour = current_time - datetime.timedelta(hours=8)
#     one_day = current_time - datetime.timedelta(days=1)
#     week = current_time - datetime.timedelta(days=7)

#     posts = wsd.objects.filter(Time_Stamp__gte=one_hour, Time_Stamp__lte=current_time)
#     post8 = wsd.objects.filter(Time_Stamp__gte=huit_hour, Time_Stamp__lte=current_time)
#     post24 = wsd.objects.filter(Time_Stamp__gte=one_day, Time_Stamp__lte=current_time)
#     postweek = wsd.objects.filter(Time_Stamp__gte=week, Time_Stamp__lte=current_time)

#     def get_rain_sum(queryset):
#         rain_sum = queryset.aggregate(Sum('rain_gauge'))['rain_gauge__sum'] or 0
#         rain_sum = round(rain_sum,2)
#         return round(rain_sum, 2) if rain_sum is not None else 0

#     p1h = get_rain_sum(posts)
#     p8h = get_rain_sum(post8)
#     p24h = get_rain_sum(post24)
#     p1w = get_rain_sum(postweek)
#     derniers_enregistrements = wsd.objects.exclude(Rg=0).order_by('-Time_Stamp')[:2]
#     tab = wsd.objects.last()
#     eto = ET0o.objects.last()
#     last_et0dr = ET0DR.objects.last()
#     lasted = rs_temp.objects.last()
#     data = fetch_data_for_etoDR()
#     eto_data_valid = validate_eto_data(data)
#     altitude = latitude = day_of_year = pressure = None
#     humidity_max = humidity_min = None
#     temp_avg = temp_max = temp_min = None
#     radiation_sum = radiation_sum1 = None
#     wind_speed_avg = None
#     if eto_data_valid:
#         altitude = data['altitude']  # Altitude (m)
#         latitude = data['latitude']  # Latitude (degrés)
#         C6 = 2  # Hauteur de l'anémomètre (m)
#         day_of_year = data['day_of_year']  # Jour de l'année
#         pressure = data['pressure']  # Pression moyenne (hPa)
#         humidity_max = data['humidity_max']  # Humidité max (%)
#         humidity_min = data['humidity_min']  # Humidité min (%)
#         temp_avg = data['temp_avg']  # Température moyenne (°C)
#         temp_max = data['temp_max']  # Température max (°C)
#         temp_min = data['temp_min']  # Température min (°C)
#         radiation_sum = data['radiation_sum'] /24 # Radiation solaire (MJ/m²)
#         radiation_sum1 = data['radiation_sum'] # Radiation solaire (MJ/m²)
#         wind_speed_avg = data['wind_speed_avg']  # Vitesse moyenne du vent (m/s)
#     context = {
#     'tab': tab, 'eto': eto, 'p1w': p1w, 'p24h': p24h, 'p8h': p8h, 'p1h': p1h,
#     'Rx': Rx, 'Rm': Rm, 'Ravg': round(Ravg, 2),
#     'Sx': Sx, 'Sm': Sm, 'Savg': round(Savg, 2),
#     'Hx': Hx, 'Hm': Hm, 'Havg': round(Havg, 2),
#     'Tmmax': Tmmax, 'Tmmin': Tmmin, 'Tmavg': round(Tmavg, 2),'rg_data': derniers_enregistrements,
#     'lstfwi': lstfwi, 'last_et0dr': last_et0dr,'Hx1': round(Hx1, 2)if Hx1 is not None else None, 'Hm1': Hm1, 'Havg1': round(Havg1, 2),
#     'Tmmax1': Tmmax1, 'Tmmin1': Tmmin1, 'Tmavg1': round(Tmavg1, 2),'Hx2': round(Hx2, 2)if Hx2 is not None else None, 'Hm2': Hm2, 'Havg2': round(Havg2, 2),
#     'Tmmax2': Tmmax2, 'Tmmin2': Tmmin2, 'Tmavg2': round(Tmavg2, 2),'lasted':lasted,'wind_speed_avg':wind_speed_avg,
#     'radiation_sum':radiation_sum,'temp_min':temp_min,'temp_max':temp_max,'temp_avg':temp_avg,'humidity_min':humidity_min,'humidity_max':humidity_max,'altitude':altitude,'latitude':latitude,
#     'eto_available': eto_data_valid,
#     }

#     return render(request, "ws_open1.html", context)

import datetime
from datetime import timedelta
from django.db.models import Max, Min, Avg, Sum
from django.utils import timezone

def wsopen1(request):
    # ⚠️ si tu peux, remplace datetime.now() par timezone.now() (timezone-aware)
    current_time = timezone.localtime(timezone.now())
    current_date = current_time.date()
    now0 = current_time.replace(hour=0, minute=0, second=0, microsecond=0)

    hm = wsd.objects.filter(Time_Stamp__gte=now0)
    th = rs_temp.objects.filter(Time_Stamp__gte=now0)

    lstfwi = DataFwiO.objects.order_by("-id").first()

    # ============================
    # 1) rs_temp : 1 seule requête aggregate
    # ============================
    agg_rs = th.aggregate(
        Tmmax1=Max('temp1'), Tmmin1=Min('temp1'), Tmavg1=Avg('temp1'),
        Tmmax2=Max('temp2'), Tmmin2=Min('temp2'), Tmavg2=Avg('temp2'),
        Hx1=Max('hum1'),     Hm1=Min('hum1'),     Havg1=Avg('hum1'),
        Hx2=Max('hum2'),     Hm2=Min('hum2'),     Havg2=Avg('hum2'),
    )

    Tmmax1, Tmmin1, Tmavg1 = agg_rs["Tmmax1"], agg_rs["Tmmin1"], agg_rs["Tmavg1"] or 0
    Tmmax2, Tmmin2, Tmavg2 = agg_rs["Tmmax2"], agg_rs["Tmmin2"], agg_rs["Tmavg2"] or 0
    Hx1, Hm1, Havg1        = agg_rs["Hx1"], agg_rs["Hm1"],       agg_rs["Havg1"] or 0
    Hx2, Hm2, Havg2        = agg_rs["Hx2"], agg_rs["Hm2"],       agg_rs["Havg2"] or 0

    # ============================
    # 2) wsd : 1 seule requête aggregate
    # ============================
    agg_wsd = hm.aggregate(
        Tmmax=Max('TEM'), Tmmin=Min('TEM'), Tmavg=Avg('TEM'),
        Hx=Max('HUM'),    Hm=Min('HUM'),    Havg=Avg('HUM'),
        Sx=Max('wind_speed'), Sm=Min('wind_speed'), Savg=Avg('wind_speed'),
        Rx=Max('illumination'), Rm=Min('illumination'), Ravg=Avg('illumination'),
    )

    Tmmax = agg_wsd["Tmmax"]
    Tmmin = agg_wsd["Tmmin"]
    Tmavg = agg_wsd["Tmavg"] or 0

    Hx = agg_wsd["Hx"]
    Hm = agg_wsd["Hm"]
    Havg = agg_wsd["Havg"] or 0

    Sx = agg_wsd["Sx"]
    Sm = agg_wsd["Sm"]
    Savg = agg_wsd["Savg"] or 0

    Rx = agg_wsd["Rx"]
    Rm = agg_wsd["Rm"]
    Ravg = agg_wsd["Ravg"] or 0

    # ============================
    # 3) Pluie : 4 requêtes (OK) mais propres
    # ============================
    def rain_sum(start):
        return wsd.objects.filter(Time_Stamp__gte=start, Time_Stamp__lte=current_time) \
            .aggregate(total=Sum('rain_gauge'))['total'] or 0

    p1h  = round(rain_sum(current_time - timedelta(hours=1)), 2)
    p8h  = round(rain_sum(current_time - timedelta(hours=8)), 2)
    p24h = round(rain_sum(current_time - timedelta(days=1)), 2)
    p1w  = round(rain_sum(current_time - timedelta(days=7)), 2)

    # ============================
    # 4) Derniers enregistrements pluie non nuls (2 lignes)
    # ============================
    # Si Rg est un champ numérique: filtre direct > 0 (plus rapide que exclude)
    derniers_enregistrements = wsd.objects.filter(Rg__gt=0).order_by('-Time_Stamp')[:2]

    # ============================
    # 5) Last records : mieux que .last()
    # ============================
    tab = wsd.objects.order_by("-Time_Stamp").first()
    eto = ET0o.objects.order_by("-Time_Stamp").first()
    last_et0dr = ET0DR.objects.order_by("-Time_Stamp").first()
    lasted = rs_temp.objects.order_by("-Time_Stamp").first()

    # ============================
    # 6) fetch_data_for_etoDR() (lourd) — on le garde pour toi
    # ============================
    data = fetch_data_for_etoDR()
    eto_data_valid = validate_eto_data(data)

    altitude = latitude = day_of_year = pressure = None
    humidity_max = humidity_min = None
    temp_avg = temp_max = temp_min = None
    radiation_sum = radiation_sum1 = None
    wind_speed_avg = None

    if eto_data_valid:
        altitude = data['altitude']
        latitude = data['latitude']
        day_of_year = data['day_of_year']
        pressure = data['pressure']
        humidity_max = data['humidity_max']
        humidity_min = data['humidity_min']
        temp_avg = data['temp_avg']
        temp_max = data['temp_max']
        temp_min = data['temp_min']
        radiation_sum = data['radiation_sum'] / 24
        radiation_sum1 = data['radiation_sum']
        wind_speed_avg = data['wind_speed_avg']

    context = {
        'tab': tab, 'eto': eto, 'p1w': p1w, 'p24h': p24h, 'p8h': p8h, 'p1h': p1h,
        'Rx': Rx, 'Rm': Rm, 'Ravg': round(Ravg, 2),
        'Sx': Sx, 'Sm': Sm, 'Savg': round(Savg, 2),
        'Hx': Hx, 'Hm': Hm, 'Havg': round(Havg, 2),
        'Tmmax': Tmmax, 'Tmmin': Tmmin, 'Tmavg': round(Tmavg, 2),
        'rg_data': derniers_enregistrements,
        'lstfwi': lstfwi,
        'last_et0dr': last_et0dr,

        'Hx1': round(Hx1, 2) if Hx1 is not None else None, 'Hm1': Hm1, 'Havg1': round(Havg1, 2),
        'Tmmax1': Tmmax1, 'Tmmin1': Tmmin1, 'Tmavg1': round(Tmavg1, 2),

        'Hx2': round(Hx2, 2) if Hx2 is not None else None, 'Hm2': Hm2, 'Havg2': round(Havg2, 2),
        'Tmmax2': Tmmax2, 'Tmmin2': Tmmin2, 'Tmavg2': round(Tmavg2, 2),

        'lasted': lasted,
        'wind_speed_avg': wind_speed_avg,
        'radiation_sum': radiation_sum,
        'temp_min': temp_min, 'temp_max': temp_max, 'temp_avg': temp_avg,
        'humidity_min': humidity_min, 'humidity_max': humidity_max,
        'altitude': altitude, 'latitude': latitude,
        'eto_available': eto_data_valid,
    }

    return render(request, "ws_open1.html", context)
# def test0(request):
#     one_day_ago = datetime.datetime.now() - datetime.timedelta(days=1)
#     labels = []
#     dataa = []
#     all = Ws.objects.all()
#     # print("all", all)
#     for i in all:
#         labels.append((i.date).strftime("%Y-%m-%d %H:%M:%S"))
#         # print("labels", labels)
#         dataa.append(i.Temperature)
#     lst = Ws.objects.last()
#     context={'all':all,'lst':lst,'labels':labels,'dataa':dataa}
#     return render(request,"test.html",context)

# def test0(request):
#     return render(request,"test.html")
def cwsi_data(request):
    # Retrieve all records from the cwsi model
    cwsi_records = cwsi.objects.all()
    cw = cwsiO.objects.all()
    # Pass the data to the template
    context = {
        'cwsi_records': cwsi_records,
        'cw' : cw
    }
    return render(request, 'cwsi/cwsi01.html', context)



""" pm10"""
from django.db.models.functions import TruncHour
import pytz

def export_hourly_averages_since_25june_csv(request):
    tz = timezone.get_current_timezone()

    start_date = datetime.datetime(2025, 6, 25, 0, 0, 0)
    start_date = timezone.make_aware(start_date, timezone=tz)
    end_date = timezone.make_aware(datetime.datetime.now(), timezone=tz)

    # Data2
    data2_hourly = (
        Data2.objects
        .filter(Time_Stamp__gte=start_date, Time_Stamp__lte=end_date)
        .annotate(hour=TruncHour('Time_Stamp'))
        .values('hour')
        .annotate(
            Temp_avg=Avg('Temp'),
            Hum_avg=Avg('Hum'),
            Wind_Speed_avg=Avg('Wind_Speed'),
            Light_Intensity_avg=Avg('Light_Intensity'),
            UV_Index_avg=Avg('UV_Index'),
            Rain_avg=Avg('Rain'),
            Rain_acc_avg=Avg('Rain_acc'),
            Rain_act_avg=Avg('Rain_act'),
            Pr_avg=Avg('Pr'),
        )
        .order_by('hour')
    )
    df_data2 = pd.DataFrame(list(data2_hourly))

    # Ray2
    ray2_hourly = (
        Ray2.objects
        .filter(DateRay__gte=start_date, DateRay__lte=end_date)
        .annotate(hour=TruncHour('DateRay'))
        .values('hour')
        .annotate(
            Ray_avg=Avg('Ray'),
            Bat_avg=Avg('Bat'),
        )
        .order_by('hour')
    )
    df_ray2 = pd.DataFrame(list(ray2_hourly))

    # ET0o
    et0_hourly = (
        ET0o.objects
        .filter(Time_Stamp__gte=start_date, Time_Stamp__lte=end_date)
        .annotate(hour=TruncHour('Time_Stamp'))
        .values('hour')
        .annotate(
            Delta_avg=Avg('Delta'),
            ET0_value_avg=Avg('value'),
        )
        .order_by('hour')
    )
    df_et0 = pd.DataFrame(list(et0_hourly))

    # Fusion des trois DataFrames
    df = pd.merge(df_data2, df_ray2, on='hour', how='outer')
    df = pd.merge(df, df_et0, on='hour', how='outer')

    if df.empty:
        return HttpResponse("Aucune donnée disponible.", content_type="text/plain")

    # Formatage heure
    df['hour'] = df['hour'].apply(lambda x: x.astimezone(pytz.UTC).replace(tzinfo=None))
    df['Heure'] = df['hour'].dt.strftime('%Y-%m-%d %H:%M')
    cols = ['Heure'] + [col for col in df.columns if col not in ['hour', 'Heure']]
    df = df[cols]

    # Export CSV (compatible Excel FR)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="moyennes_horaires_25juin.csv"'
    df.to_csv(path_or_buf=response, index=False, sep=';')

    return response
########################""
def export_capsol2_csv(request):
    tz = timezone.get_current_timezone()
    start_date = timezone.make_aware(datetime.datetime(2026, 1, 1, 0, 0, 0), timezone=tz)
    end_date = timezone.make_aware(datetime.datetime.now(), timezone=tz)

    capsol_data = (
        CapSol2.objects
        .filter(
            dt__gte=start_date.date(),
            dt__lte=end_date.date(),
            devId__in=[2, 3, 4, 7, 8, 9]  # ✅ filtre sur les capteurs souhaités
        )
        .values('dt', 'devId', 'Temp', 'Hum', 'Bat', 'time')
        .order_by('devId', 'dt', 'time')
    )

    df = pd.DataFrame(list(capsol_data))

    if df.empty:
        return HttpResponse("Aucune donnée disponible.", content_type="text/plain")

    df['heure_tronquee'] = pd.to_datetime(
        df['dt'].astype(str) + ' ' + df['time'].astype(str)
    ).dt.floor('H').dt.strftime('%Y-%m-%d %H:%M')

    df_grouped = df.groupby(['heure_tronquee', 'devId']).agg(
        Temperature_avg=('Temp', 'mean'),
        Humidite_avg=('Hum', 'mean'),
        Batterie_avg=('Bat', 'mean'),
    ).reset_index()

    df_grouped.rename(columns={'heure_tronquee': 'Heure', 'devId': 'Capteur'}, inplace=True)

    # ✅ Pivot : une colonne par capteur pour chaque variable
    df_pivot = df_grouped.pivot(index='Heure', columns='Capteur')
    df_pivot.columns = [f'Cap{col[1]}_{col[0].replace("_avg", "")}' for col in df_pivot.columns]
    df_pivot = df_pivot.reset_index().sort_values('Heure')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="moyennes_horaires_capsol2.csv"'
    df_pivot.to_csv(path_or_buf=response, index=False, sep=';')
    return response
##################################################

def export_hourly_averages_wsd_et0dr_csv(request):
    tz = timezone.get_current_timezone()

    start_date = datetime.datetime(2025, 6, 25, 0, 0, 0)
    start_date = timezone.make_aware(start_date, timezone=tz)
    end_date = timezone.make_aware(datetime.datetime.now(), timezone=tz)

    # Moyennes horaires de WSD
    wsd_hourly = (
        wsd.objects
        .filter(Time_Stamp__gte=start_date, Time_Stamp__lte=end_date)
        .annotate(hour=TruncHour('Time_Stamp'))
        .values('hour')
        .annotate(
            wind_direction_angle_avg=Avg('wind_direction_angle'),
            HUM_avg=Avg('HUM'),
            Rg_avg=Avg('Rg'),
            rain_gauge_avg=Avg('rain_gauge'),
            wind_speed_avg=Avg('wind_speed'),
            illumination_avg=Avg('illumination'),
            TEM_avg=Avg('TEM'),
        )
        .order_by('hour')
    )
    df_wsd = pd.DataFrame(list(wsd_hourly))

    # Moyennes horaires de ET0DR
    et0dr_hourly = (
        ET0DR.objects
        .filter(Time_Stamp__gte=start_date, Time_Stamp__lte=end_date)
        .annotate(hour=TruncHour('Time_Stamp'))
        .values('hour')
        .annotate(
            Delta_avg=Avg('Delta'),
            ET0_value_avg=Avg('value'),
        )
        .order_by('hour')
    )
    df_et0dr = pd.DataFrame(list(et0dr_hourly))

    # Fusion
    df = pd.merge(df_wsd, df_et0dr, on='hour', how='outer')

    if df.empty:
        return HttpResponse("Aucune donnée disponible.", content_type="text/plain")

    # Mise en forme heure
    df['hour'] = df['hour'].apply(lambda x: x.astimezone(pytz.UTC).replace(tzinfo=None))
    df['Heure'] = df['hour'].dt.strftime('%Y-%m-%d %H:%M')
    cols = ['Heure'] + [col for col in df.columns if col not in ['hour', 'Heure']]
    df = df[cols]

    # Export CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="moyennes_horaires_wsd_et0dr_25juin.csv"'
    df.to_csv(path_or_buf=response, index=False, sep=';')

    return response


def lht65(request):
    # Liste fixe des capteurs
    capteurs = ['LHT2_Frigo', 'LHT_3', 'Capteur 3']

    # Champs disponibles
    available_fields = ['temp_ds', 'temp_sht', 'hum_sht', 'battery_voltage']

    # Valeurs par défaut
    default_capteur = 'LHT2_Frigo'
    default_field = 'temp_ds'

    # Lecture des paramètres GET avec valeurs par défaut
    selected_capteur = request.GET.get('capteur', default_capteur)
    selected_field = request.GET.get('field', default_field)
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Gestion des dates
    if start_date and end_date:
        start_date = make_aware(datetime.datetime.strptime(start_date, "%Y-%m-%d"))
        end_date = make_aware(datetime.datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59))
    else:
        one_day_ago = (datetime.datetime.now() - datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0)
        start_date = make_aware(one_day_ago)
        end_date = make_aware(datetime.datetime.now().replace(hour=23, minute=59, second=59))

    # Filtrage des données
    data_qs = DeviceData.objects.filter(
        timestamp__range=(start_date, end_date),
        device_name=selected_capteur
    )

    # Préparation des données
    labels = [entry.timestamp.strftime("%Y-%m-%d %H:%M:%S") for entry in data_qs]
    values = [getattr(entry, selected_field) if getattr(entry, selected_field) is not None else 0 for entry in data_qs]
    zipped_data = zip(labels, values)

    data1 = {}
    capteurs = ['LHT2_Frigo', 'LHT_3', 'Capteur 3']  # Les noms exacts de tes capteurs
    for capteur in capteurs:
        latest_data = DeviceData.objects.filter(device_name=capteur).order_by('-timestamp').first()
        data1[capteur] = latest_data
    context = {
        'capteurs': capteurs,
        'available_fields': available_fields,
        'selected_capteur': selected_capteur,
        'selected_field': selected_field,
        'start_date': start_date.strftime("%Y-%m-%d"),
        'end_date': end_date.strftime("%Y-%m-%d"),
        'zipped_data': list(zipped_data),
        'data1':data1,
        # 'available_fields': available_fields,
        # 'selected_field': selected_field,
        # 'start_date': start_date.strftime("%Y-%m-%d"),
        # 'end_date': end_date.strftime("%Y-%m-%d"),
        # 'data_by_sensor': data_by_sensor
    }

    return render(request, 'lht1.html', context)



def et0_view(request):
    # Récupération des dates
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date and end_date:
        start_date = make_aware(datetime.datetime.strptime(start_date, "%Y-%m-%d"))
        end_date = make_aware(datetime.datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59))
    else:
        one_day_ago = datetime.datetime.now() - datetime.timedelta(days=1)
        start_date = make_aware(one_day_ago.replace(hour=0, minute=0, second=0))
        end_date = make_aware(datetime.datetime.now().replace(hour=23, minute=59, second=59))

    # Filtrage des données par modèle
    data_dr = ET0DR.objects.filter(Time_Stamp__range=(start_date, end_date))
    data_drv = ET0DRv.objects.filter(Time_Stamp__range=(start_date, end_date))
    data_o = ET0o.objects.filter(Time_Stamp__range=(start_date, end_date))
    #data_FAO56_DR = ETODR_FAO56.objects.filter(Time_Stamp__range=(start_date, end_date)) # j'ai ajouter cette ligne
    # Préparation des données pour le graphique
    def extract_data(queryset):
        labels = [entry.Time_Stamp.strftime("%Y-%m-%d %H:%M:%S") for entry in queryset]
        values = [entry.value if entry.value is not None else 0 for entry in queryset]
        return list(zip(labels, values))

    zipped_dr = extract_data(data_dr)
    zipped_drv = extract_data(data_drv)
    zipped_o = extract_data(data_o)
    #zipped_FAO56_DR = extract_data(data_FAO56_DR) # j'ai ajouter cette ligne

    # Derniers paramètres
    latest_dr = ET0DR.objects.order_by('-Time_Stamp').first()
    latest_drv = ET0DRv.objects.order_by('-Time_Stamp').first()
    latest_o = ET0o.objects.order_by('-Time_Stamp').first()
    #latest_FAO56_DR = ETODR_FAO56.objects.order_by('-Time_Stamp').first()
    latest_models = {
        "ET0_Dragino": {
            "obj": latest_dr,
            "raym_converted": latest_dr.Raym / 24 if latest_dr and latest_dr.Raym else None,
            "raym": latest_dr.Raym,
        },
        "ET0_Dragino_irraVisioGrenn": {
            "obj": latest_drv,
            "raym_converted": latest_drv.Raym / 24 if latest_drv and latest_drv.Raym else None,
            "raym": latest_drv.Raym,
        },
        "ET0_SenseCap": {
            "obj": latest_o,
            "raym_converted": latest_o.Raym/24  if latest_o and latest_o.Raym else None,
            "raym": latest_o.Raym,
        }
        #"ET0DR_PM_FAO56": {                                                                                # j'ai ajouter cette ligne
        #    "obj":  latest_FAO56_DR,                                                                         # j'ai ajouter cette ligne
        #    "raym_converted":  latest_FAO56_DR.Raym/24  if  latest_FAO56_DR and latest_FAO56_DR.Raym else None,    # j'ai ajouter cette ligne
        #    "raym": latest_FAO56_DR.Raym,                                                                    # j'ai ajouter cette ligne
        #}
    }
    context = {
        'zipped_dr': zipped_dr,
        'zipped_drv': zipped_drv,
        'zipped_o': zipped_o,
        #'zipped_FAO56_DR': zipped_FAO56_DR,                      # j'ai ajouter cette ligne
        'latest_dr': latest_dr,
        'latest_drv': latest_drv,
        'latest_o': latest_o,
        #'latest_FAO56_DR': latest_FAO56_DR,
        'start_date': start_date.strftime("%Y-%m-%d"),
        'end_date': end_date.strftime("%Y-%m-%d"),
        'models_info': [
        (latest_dr, "ET0_Dragino"),
        (latest_drv, "ET0_Dragino_irraVisioGreen"),
        (latest_o, "ET0_SenseCap"),
        #(latest_FAO56_DR, "ET0DR_PM_FAO56"),
    ],
    'latest_models': latest_models,
    }

    return render(request, 'et0_graph.html', context)

##########################################vue sur l'interface pour ET0 FAO56##########################################################
def et0_FAO56_view(request):
    # Récupération des dates
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date and end_date:
        start_date = make_aware(datetime.datetime.strptime(start_date, "%Y-%m-%d"))
        end_date = make_aware(datetime.datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59))
    else:
        one_day_ago = datetime.datetime.now() - datetime.timedelta(days=1)
        start_date = make_aware(one_day_ago.replace(hour=0, minute=0, second=0))
        end_date = make_aware(datetime.datetime.now().replace(hour=23, minute=59, second=59))

    # Filtrage des données par modèle
    data_FAO56DR = ETODR_FAO56.objects.filter(Time_Stamp__range=(start_date, end_date)) # j'ai ajouter cette ligne
    data_FAO56S = ETOSensCap_FAO56.objects.filter(Time_Stamp__range=(start_date, end_date)) # j'ai ajouter cette ligne
    data_FAO56DRV = ETODRV_FAO56.objects.filter(Time_Stamp__range=(start_date, end_date)) # j'ai ajouter cette ligne

    # Préparation des données pour le graphique
    def extract_data(queryset):
        labels = [entry.Time_Stamp.strftime("%Y-%m-%d %H:%M:%S") for entry in queryset]
        values = [entry.value if entry.value is not None else 0 for entry in queryset]
        return list(zip(labels, values))

    zipped_FAO56DR = extract_data(data_FAO56DR) # j'ai ajouter cette ligne
    zipped_FAO56S = extract_data(data_FAO56S) # j'ai ajouter cette ligne
    zipped_FAO56DRV = extract_data(data_FAO56DRV) # j'ai ajouter cette ligne

    # Derniers paramètres
    latest_FAO56DR = ETODR_FAO56.objects.order_by('-Time_Stamp').first()           # j'ai ajouter cette ligne
    latest_FAO56S = ETOSensCap_FAO56.objects.order_by('-Time_Stamp').first()           # j'ai ajouter cette ligne
    latest_FAO56DRV = ETODRV_FAO56.objects.order_by('-Time_Stamp').first()           # j'ai ajouter cette ligne

    latest_models = {
         "ET0_PM_FAO56_Dragino": {                                                                                # j'ai ajouter cette ligne
            "obj":  latest_FAO56DR,                                                                         # j'ai ajouter cette ligne
            "raym_converted":  latest_FAO56DR.Raym/24  if  latest_FAO56DR and latest_FAO56DR.Raym else None,    # j'ai ajouter cette ligne
            "raym": latest_FAO56DR.Raym,                                                                    # j'ai ajouter cette ligne
        },
        "ET0_PM_FAO56_Senscap":{                                                                               # j'ai ajouter cette ligne
            "obj":  latest_FAO56S,                                                                         # j'ai ajouter cette ligne
            "raym_converted":  latest_FAO56S.Raym/24  if  latest_FAO56S and latest_FAO56S.Raym else None,    # j'ai ajouter cette ligne
            "raym": latest_FAO56S.Raym,                                                                    # j'ai ajouter cette ligne
        },
        "ET0_PM_FAO56_DraginoVisioGreen": {                                                                                # j'ai ajouter cette ligne
            "obj":  latest_FAO56DRV,                                                                                     # j'ai ajouter cette ligne
            "raym_converted":  latest_FAO56DRV.Raym/24  if  latest_FAO56DRV and latest_FAO56DRV.Raym else None,    # j'ai ajouter cette ligne
            "raym": latest_FAO56DRV.Raym,                                                                    # j'ai ajouter cette ligne
        }
    }
    context = {
        'zipped_FAO56DR': zipped_FAO56DR,                      # j'ai ajouter cette ligne
        'zipped_FAO56S': zipped_FAO56S,
        'zipped_FAO56DRV': zipped_FAO56DRV,
        'latest_FAO56DR': latest_FAO56DR,
        'latest_FAO56S': latest_FAO56S,
        'latest_FAO56DRV': latest_FAO56DRV,
        'start_date': start_date.strftime("%Y-%m-%d"),
        'end_date': end_date.strftime("%Y-%m-%d"),
        'models_info': [
        (latest_FAO56DR, "ET0_PM_FAO56_Dragino"),
        (latest_FAO56S, "ET0_PM_FAO56_Senscap"),
        (latest_FAO56DRV, "ET0_PM_FAO56_DraginoVisioGreen"),
    ],
    'latest_models': latest_models,
    }

    return render(request, 'et0_FAO56_graph.html', context)
####################################################################################################

@require_POST
@csrf_exempt
def v_chirpstack(request):
    print("**********************uplink")
    if 'event' in request.GET:
        event = str(request.GET['event'])
        if event == 'up' :
            print("*********************up")
            try :
                print("*************************try")
                data = json.loads(request.body)
                print(data)
                print("DEV EUI : ", data['deviceInfo']['devEui'])



                if data['deviceInfo']['devEui'] == 'a84041d10858e027':  # Vérifie si c'est bien le capteur de sol


                    print("📡 Données reçues du Capteur de sol")

                    # Récupération des données depuis 'object'
                    object_data = data.get('object', {})
                    batterie = object_data.get('Batterie', '0')  # Valeur par défaut '0' si absente

                    print("📊 object_data complet :", object_data)

                    # Boucle sur les capteurs de sol (Capteur_1 à Capteur_4)
                    #calibration_params = {
                     #   1: (5.4, 54.2),
                      #  2: (6.4, 44.9),
                       # 3: (5.1, 59.0),
                        #4: (0.0, 55.5),
                    #}

                    #def calibrate(val, mn, mx):
                     #   pct = (val - mn) * 100.0 / (mx - mn)
                     #   return max(0.0, min(100.0, pct))  # borne entre 0 et 100
                    #k=0
                    #for i in range(1, 10):      ##### j'ai modifie "for i in range(1, 8):" en ajoutant 2 capteurs 8 et 9
                     #   capteur_key = f"Capteur_{i}"
                      #  print("capteur_key : ", capteur_key)
                       # if capteur_key in object_data:
                        #    k=k+1
                    #print("le nombre des capteurs : ",k)
                    #z=0

                    for i in range(1, 10):      ##### j'ai modifie "for i in range(1, 8):" en ajoutant 2 capteurs 8 et 9
                        capteur_key = f"Capteur_{i}"
                        # print("capteur_key : ", capteur_key)
                        if capteur_key in object_data:
                            capteur_data = object_data[capteur_key]
                            print(f"🔎 {capteur_key} trouvé :", capteur_data)

                            # Lecture des données brutes
                            temperature = float(capteur_data.get('Temperature', '0'))
                            humidite_brut = float(capteur_data.get('Humidite', '0'))
                            conductivite = float(capteur_data.get('Conductivite', '0'))
                            azote = float(capteur_data.get('Azote', '0'))
                            phosphore = float(capteur_data.get('Phosphore', '0'))
                            potassium = float(capteur_data.get('Potassium', '0'))

                            # Application de la calibration uniquement si le capteur est dans la liste
                            # if i in calibration_params:
                            #     mn, mx = calibration_params[i]
                            #     humidite_pct = calibrate(humidite_brut, mn, mx)
                            # else:
                            #     humidite_pct = humidite_brut  # pas de calibration si inconnu
                    # for i in range(1, 8):
                    #     capteur_key = f"Capteur_{i}"
                    #     if capteur_key in object_data:
                    #         capteur_data = object_data[capteur_key]
                    #         print(f"🔎 {capteur_key} trouvé :", capteur_data)

                    #         # Vérification si l'une des valeurs dépasse 65000
                    #         temperature = float(capteur_data.get('Temperature', '0'))
                    #         humidite = float(capteur_data.get('Humidite', '0'))
                    #         conductivite = float(capteur_data.get('Conductivite', '0'))
                    #         azote = float(capteur_data.get('Azote', '0'))
                    #         phosphore = float(capteur_data.get('Phosphore', '0'))
                    #         potassium = float(capteur_data.get('Potassium', '0'))

                            if any(value > 65000 for value in [temperature, humidite_brut, conductivite, azote, phosphore, potassium]):
                                print(f"⚠️ Ignoré l'enregistrement pour {capteur_key} car une des valeurs dépasse 65000")
                                continue  # Ignorer cet enregistrement et passer au suivant
                            try:
                                CapSol2.objects.create(
                                    devId=i,
                                    Temp=temperature,
                                    Hum=humidite_brut,
                                    ec=conductivite,
                                    N=azote,
                                    P=phosphore,
                                    K=potassium,
                                    Sal=0,  # Valeur par défaut
                                    Bat=batterie
                                )
                                print(f"✅ Données enregistrées pour {capteur_key}: {capteur_data}")

                            except Exception as e:
                                print(f"❌ Erreur lors de l'enregistrement de {capteur_key}: {e}")
                            #z=z+1


                if data['deviceInfo']['devEui'] == '71b3d57ed00653c8':
                    print("Données reçues du dispositif rain_drop_sensor")

                    # Récupération des données depuis 'object'
                    object_data = data.get('object', {})

                    # Création de l'objet `greenHouse`
                    object_irrigation = greenHouse()

                    # Affectation des valeurs
                    object_irrigation.Soil_Humidity = object_data.get('Soil_Humidity', None)
                    object_irrigation.Rain_Drop = object_data.get('Rain_Drop', None)
                    object_irrigation.Rain_Drop_Sensor_State = object_data.get('Rain_Drop_Sensor_State', None)

                    # Time_Stamp peut être défini à partir du champ 'time' si présent dans les données reçues
                    if 'time' in data:
                        from django.utils.dateparse import parse_datetime
                        object_irrigation.Time_Stamp = parse_datetime(data['time'])

                    try:
                        # Sauvegarde dans la base de données
                        object_irrigation.save()
                        print("Données enregistrées avec succès :", object_irrigation)
                    except Exception as e:
                        print("Erreur lors de l'enregistrement :", e)
                else:
                    print("Dispositif non reconnu, données ignorées.")

                ################################## Fin ########################################################

                if data['deviceInfo']['devEui'] == 'a8404153d188114e':  # Vérifie si c'est bien le capteur LHT65N
                    print("📡 Données reçues du LHT65N")
                    DeviceData.objects.create(
                        device_name=data["deviceInfo"]["deviceName"],
                        temp_ds=data["object"]["TempC_DS"],
                        hum_sht=data["object"]["Hum_SHT"],
                        temp_sht=data["object"]["TempC_SHT"],
                        battery_voltage=data["object"]["BatV"]
                    )
                    print("Données enregistrées !")

                    print("*********************************FIN LHT65 *****************************")


                try:
                    if data['deviceInfo']['devEui'] == '70b3d58f8000062d':
                        print("📡 Données reçues de la station Davis")
                        obj = data.get('object', {})
                        record = Data3()
                        record.devEui         = '70b3d58f8000062d'
                        record.temperature_c  = obj.get('temperature_c')
                        record.humidity_pct   = obj.get('humidity_pct')
                        record.wind_speed_ms  = obj.get('wind_speed_ms')
                        record.wind_speed_kmh = obj.get('wind_speed_kmh')
                        record.wind_dir_deg   = obj.get('wind_dir_deg')
                        record.wind_dir_card  = obj.get('wind_dir_card')
                        record.rain_mm        = obj.get('rain_mm')
                        record.movement       = obj.get('movement', False)
                        rx_info = data.get('rxInfo', [{}])
                        if rx_info:
                            record.rssi = rx_info[0].get('rssi')
                            record.snr  = rx_info[0].get('snr')
                        record.save()
                        print("✅ Davis sauvegardé dans Data3 !")
                    else:
                        print("Dispositif non reconnu, données ignorées.")
                except Exception as e:
                    print(f"❌ Erreur Davis : {e}")


                if data['deviceInfo']['devEui'] == "a84041549188114d":
                    DeviceData.objects.create(
                        device_name=data["deviceInfo"]["deviceName"],
                        temp_ds=data["object"]["TempC_DS"],
                        hum_sht=data["object"]["Hum_SHT"],
                        temp_sht=data["object"]["TempC_SHT"],
                        battery_voltage=data["object"]["BatV"]
                    )
                    print("Données enregistrées !")
                    print("*********************************FIN LHT65 *****************************")
                # if data['deviceInfo']['devEui'] == 'a84041549188114d':  # Vérifie si c'est bien le capteur LHT65N
                #     print("📡 Données reçues du LHT65")
                #     print(data['deviceInfo']['object'])
                #     print("*********************************FIN LHT65 *****************************")

#############################################capteur sol calibré par graviométrie##################################
                    print("le nombre d'enregistrement :",z)
                # if data['deviceInfo']['devEui'] == 'a84041d10858e027':  # Vérifie si c'est bien le capteur de sol
                #     print("📡 Données reçues du Capteur de sol")

                #     # Récupération des données depuis 'object'
                #     object_data = data.get('object', {})
                #     batterie = object_data.get('Batterie', '0')  # Valeur par défaut '0' si absente

                #     print("📊 object_data complet :", object_data)

                #     # Boucle sur les capteurs de sol (Capteur_1 à Capteur_4)
                #     def calib_capteur1(x):
                #         return -0.0085 * x**2 + 1.2269 * x - 10.463
                #     def calib_capteur2(x):
                #         return 0.011 * x**2 - 0.5161 * x + 27.034
                #     def calib_capteur3(x):
                #         return -0.0145 * x**2 + 1.836 * x - 12.28
                #     def calib_capteur4(x):
                #         return 0.0068 * x**2 - 0.2393 * x + 24.092

                #     calibration_params = {
                #         1: calib_capteur1,
                #         2: calib_capteur2,
                #         3: calib_capteur3,
                #         4: calib_capteur4,
                #     }

                #     def calibrate(val, mn, mx):
                #         pct = (val - mn) * 100.0 / (mx - mn)
                #         return max(0.0, min(100.0, pct))  # borne entre 0 et 100

                #     for i in range(1, 8):
                #         capteur_key = f"Capteur_{i}"
                #         if capteur_key in object_data:
                #             capteur_data = object_data[capteur_key]
                #             print(f"🔎 {capteur_key} trouvé :", capteur_data)

                #             # Lecture des données brutes
                #             temperature = float(capteur_data.get('Temperature', '0'))
                #             humidite_brut = float(capteur_data.get('Humidite', '0'))
                #             conductivite = float(capteur_data.get('Conductivite', '0'))
                #             azote = float(capteur_data.get('Azote', '0'))
                #             phosphore = float(capteur_data.get('Phosphore', '0'))
                #             potassium = float(capteur_data.get('Potassium', '0'))

                #             # Application de la calibration uniquement si le capteur est dans la liste
                #             if i in calibration_funcs:
                #                 humidite_pct = calibration_funcs[i](humidite_brut)
                #                 humidite_pct = max(0.0, min(100.0, humidite_pct))
                #             else:
                #                 humidite_pct = humidite_brut  # pas de calibration si inconnu

                #             if any(value > 65000 for value in [temperature, humidite, conductivite, azote, phosphore, potassium]):
                #                 print(f"⚠️ Ignoré l'enregistrement pour {capteur_key} car une des valeurs dépasse 65000")
                #                 continue  # Ignorer cet enregistrement et passer au suivant
                #             try:
                #                 CapSolGraviometrie.objects.create(
                #                     devId=i,
                #                     TempGraviometrie=temperature,
                #                     HumGraviometrie=humidite_pct,
                #                     ecGraviometrie=conductivite,
                #                     NGraviometrie=azote,
                #                     PGraviometrie=phosphore,
                #                     KGraviometrie=potassium,
                #                     SalGraviometrie=0,  # Valeur par défaut
                #                     BatGraviometrie=batterie
                #                 )
                #                 print(f"✅ Données enregistrées pour {capteur_key}: {capteur_data}")
                #             except Exception as e:
                #                 print(f"❌ Erreur lors de l'enregistrement de {capteur_key}: {e}")

#####################################################################################################################
                if data['deviceInfo']['devEui'] == 'a84041834189a939':
                    print("📡 Données reçues du Capteur de sol (Capteurs 5 à 7)")

                    object_data = data.get('object', {})
                    batterie = float(object_data.get('Batterie', 0))

                    print("📊 object_data complet :", object_data)

                    for i in range(5, 8):
                        capteur_key = f"Capteur_{i}"
                        if capteur_key in object_data:
                            capteur_data = object_data[capteur_key]
                            print(f"🔎 {capteur_key} trouvé :", capteur_data)

                            temperature = float(capteur_data.get('Temperature', 0))
                            humidite = float(capteur_data.get('Humidite', 0))
                            conductivite = float(capteur_data.get('Conductivite', 0))
                            salinite = float(capteur_data.get('Salinite', 0))
                            azote = float(capteur_data.get('Azote', 0))
                            phosphore = float(capteur_data.get('Phosphore', 0))
                            potassium = float(capteur_data.get('Potassium', 0))

                            if any(value > 65000 for value in [temperature, humidite, conductivite, azote, phosphore, potassium]):
                                print(f"⚠️ Ignoré l'enregistrement pour {capteur_key} car une des valeurs dépasse 65000")
                                continue

                            try:
                                CapSol2.objects.create(
                                    devId=i,
                                    Temp=temperature,
                                    Hum=humidite,
                                    ec=conductivite,
                                    N=azote,
                                    P=phosphore,
                                    K=potassium,
                                    Sal=salinite,  # Ici, on enregistre la salinité
                                    Bat=batterie
                                )
                                print(f"✅ Données enregistrées pour {capteur_key}")
                            except Exception as e:
                                print(f"❌ Erreur lors de l'enregistrement de {capteur_key}: {e}")

#########################################EV1################################################################

                #if data['deviceInfo']['devEui'] == 'a84041834189a939':
                if data['deviceInfo']['devEui'] == 'ce7554dc00001057':
                    print("Données reçues du dispositif Vanne 1")

                    # Récupération des données depuis 'object'
                    object_data = data.get('object', {})

                    # Création de l'objet `temp_hum`
                    object_ev1Batt = ev_batt()
                    #object_tempHum = rs_temp()

                    # Affectation des valeurs
                    #object_tempHum.batt = object_data.get('batt', None)
                    #object_tempHum.hum1 = object_data.get('hum1', None)
                    #object_tempHum.temp1 = object_data.get('temp1', None)
                    #object_tempHum.hum2 = object_data.get('hum2', None)
                    #object_tempHum.temp2 = object_data.get('temp2', None)
                    object_ev1Batt.batt = object_data.get('battery_voltage', None)

                    # Time_Stamp peut être défini à partir du champ 'time' si présent dans les données reçues
                    if 'time' in data:
                        from django.utils.dateparse import parse_datetime
                        object_ev1Batt.Time_Stamp = parse_datetime(data['time'])

                    try:
                        # Sauvegarde dans la base de données
                        object_ev1Batt.save()
                        print("Données enregistrées avec succès :", object_ev1Batt)
                    except Exception as e:
                        print("Erreur lors de l'enregistrement :", e)
                else:
                    print("Dispositif non reconnu, données ignorées.")

        ###########################EV2##############################

                if data['deviceInfo']['devEui'] == '2e3554dc00001057':
                    print("Données reçues du dispositif Vanne 2")

                    # Récupération des données depuis 'object'
                    object_data = data.get('object', {})

                    # Création de l'objet `temp_hum`
                    object_ev2Batt = ev_batt2()

                    object_ev2Batt.batt = object_data.get('battery_voltage', None)

                    # Time_Stamp peut être défini à partir du champ 'time' si présent dans les données reçues
                    if 'time' in data:
                        from django.utils.dateparse import parse_datetime
                        object_ev2Batt.Time_Stamp = parse_datetime(data['time'])

                    try:
                        # Sauvegarde dans la base de données
                        object_ev2Batt.save()
                        print("Données enregistrées avec succès :", object_ev2Batt)
                    except Exception as e:
                        print("Erreur lors de l'enregistrement :", e)
                else:
                    print("Dispositif non reconnu, données ignorées.")

############################################EV3#####################################################################


                if data['deviceInfo']['devEui'] == '1e4554dc00001057':
                    print("Données reçues du dispositif Vanne 3")

                    # Récupération des données depuis 'object'
                    object_data = data.get('object', {})

                    # Création de l'objet `temp_hum`
                    object_ev3Batt = ev_batt3()


                    # Affectation des valeurs

                    object_ev3Batt.batt = object_data.get('battery_voltage', None)

                    # Time_Stamp peut être défini à partir du champ 'time' si présent dans les données reçues
                    if 'time' in data:
                        from django.utils.dateparse import parse_datetime
                        object_ev3Batt.Time_Stamp = parse_datetime(data['time'])

                    try:
                        # Sauvegarde dans la base de données
                        object_ev3Batt.save()
                        print("Données enregistrées avec succès :", object_ev3Batt)
                    except Exception as e:
                        print("Erreur lors de l'enregistrement :", e)
                else:
                    print("Dispositif non reconnu, données ignorées.")
#########################################Makerfabs################################################################

                #if data['deviceInfo']['devEui'] == 'a84041834189a939':
                if data['deviceInfo']['devEui'] == '48e663fffe300aed':
                    print("Données reçues du dispositif Makerfabs")

                    # Récupération des données depuis 'object'
                    object_data = data.get('object', {})

                    # Création de l'objet `Makerfabs`
                    object_makerFabs1 = Makerfabs()
                    #object_tempHum = rs_temp()

                    # Affectation des valeurs
                    object_makerFabs1.batt = object_data.get('field2', None)
                    object_makerFabs1.valve = object_data.get('field3', None)
                    #object_makerFabs1.Volume = object_data.get('field5', None)
                    object_makerFabs1.Volume = 0
                    object_makerFabs1.debit = object_data.get('field4', None)
                    #object_tempHum.temp2 = object_data.get('temp2', None)
                    #object_makerFabs1.durée = object_data.get('field6', None)
                    object_makerFabs1.durée = 0

                    # Time_Stamp peut être défini à partir du champ 'time' si présent dans les données reçues
                    if 'time' in data:
                        from django.utils.dateparse import parse_datetime
                        object_makerFabs1.Time_Stamp = parse_datetime(data['time'])

                    try:
                        # Sauvegarde dans la base de données
                        object_makerFabs1.save()
                        print("Données enregistrées avec succès :", object_makerFabs1)
                        calculate_duration_and_volume(object_makerFabs1)
                    except Exception as e:
                        print("Erreur lors de l'enregistrement :", e)

                else:
                    print("Dispositif non reconnu, données ignorées.")

        ###########################FIN##############################

#################################################################################################################
                if data['deviceInfo']['devEui'] == 'a84041685458e15b':
                    print("Données reçues du dispositif SW3L-010")

                    # Récupération des données depuis 'object'
                    object_data = data.get('object', {})

                    # Création de l'objet `debitcap`
                    object_debit = debitcap()

                    # Affectation des valeurs
                    object_debit.debit = object_data.get('debit', None)
                    object_debit.pulse = object_data.get('pulse', None)
                    object_debit.flag = object_data.get('flag', None)

                    # Time_Stamp peut être défini à partir du champ 'time' si présent dans les données reçues
                    if 'time' in data:
                        from django.utils.dateparse import parse_datetime
                        object_debit.Time_Stamp = parse_datetime(data['time'])

                    try:
                        # Sauvegarde dans la base de données
                        object_debit.save()
                        print("Données enregistrées avec succès :", object_debit)
                    except Exception as e:
                        print("Erreur lors de l'enregistrement :", e)
                else:
                    print("Dispositif non reconnu, données ignorées.")
                if data['deviceInfo']['devEui'] == WsSENSECAP_WeatherStation:
                    messages = data['object']['messages']
                    print("messages: ", messages)
                    batt_mesure = False
                    for mesage in messages:
                        for measurement in mesage:
                            print("lenght messages: ", len(messages))
                            if len(messages) >= 3 and not batt_mesure:
                                bat = measurement['Battery(%)']
                                batt_mesure = True
                                break
                            print(measurement['type'],measurement['measurementValue'])
                            if measurement['type'] =="Air Temperature":
                                airTemp = measurement['measurementValue']
                                continue
                            elif measurement['type'] =="Air Humidity":
                                airHum = measurement['measurementValue']
                                continue
                            elif measurement['type'] =="Light Intensity":
                                light = measurement['measurementValue']
                                continue
                            elif measurement['type'] =="UV Index":
                                uv = measurement['measurementValue']
                                continue
                            elif measurement['type'] =="Wind Speed":
                                windSpeed = measurement['measurementValue']
                                continue
                            elif measurement['type'] =="Wind Direction Sensor":
                                windDirection = measurement['measurementValue']
                                continue
                            elif measurement['type'] =="Rain Gauge":
                                rainfall = measurement['measurementValue']
                                print("rain_fall : sense cap : ", rainfall, type(rainfall))
                                continue
                            elif measurement['type'] =="Barometric Pressure":
                                pressure = measurement['measurementValue']
                                continue


                    object_WsSENSECAP = Data2()
                    object_WsSENSECAP.Temp = airTemp
                    # print(object_WsSENSECAP)
                    object_WsSENSECAP.Hum = airHum
                    object_WsSENSECAP.Wind_Speed = round((float(windSpeed)*3.6),4)
                    object_WsSENSECAP.Light_Intensity = light
                    object_WsSENSECAP.UV_Index = uv
                    object_WsSENSECAP.Rain_acc = rainfall
                    last_Rain_acc = Data2.objects.order_by('-Time_Stamp').first()
                    print("last_Rain_acc : ",last_Rain_acc, type(last_Rain_acc.Rain_acc))
                    if float(rainfall) < float(last_Rain_acc.Rain_acc):
                        object_WsSENSECAP.Rain_act = rainfall
                    else:
                        object_WsSENSECAP.Rain_act = float(rainfall-float(last_Rain_acc.Rain_acc))
                    print("object_WsSENSECAP.Rain_act: ",object_WsSENSECAP.Rain_act)
                    object_WsSENSECAP.Rain = rainfall/4
                    print("object_WsSENSECAP.Rain : ",object_WsSENSECAP.Rain)
                    # object_WsSENSECAP.Light = light
                    # object_WsSENSECAP.UV = uv
                    object_WsSENSECAP.Pr = pressure
                    # if batt_mesure:
                    #     object_WsSENSECAP.Bat = bat
                    # else:
                    #     object_WsSENSECAP_last_val_batt = WsSENSECAP.objects.last()
                    #     object_WsSENSECAP.Bat = object_WsSENSECAP_last_val_batt.Bat
                    object_WsSENSECAP.save()

                    # Vérifier si le devEui correspond au dispositif Model WSC1-L
                # if data['deviceInfo']['devEui'] == 'a84041b02458e028':
                #     print("Données reçues du dispositif Model WSC1-L")

                #     # Récupération des données depuis 'object'
                #     object_data = data.get('object', {})

                #     # Création de l'objet `wsd`
                #     object_wsd = wsd()

                #     # Affectation des valeurs avec `get()` pour éviter les erreurs si une clé est absente
                #     object_wsd.wind_direction_angle = object_data.get('wind_direction_angle', None)
                #     object_wsd.wind_direction = object_data.get('wind_direction', None)
                #     object_wsd.HUM = object_data.get('humidity', None)
                #     object_wsd.TEM = object_data.get('temperature', None)
                #     # Dernier enregistrement avec une pluie non nulle
                #     last_record = wsd.objects.exclude(Rg=0).order_by('-Time_Stamp').first()
                #     print("last_record from DB:", last_record)

                #     # Pluie brute reçue du capteur (accumulée depuis le début)
                #     current_rain_raw = object_data.get('rain_instant', None)
                #     print("current_rain_raw:", current_rain_raw)

                #     try:
                #         # Conversion en float
                #         current_rain = round(float(current_rain_raw), 2)
                #         print("current_rain:", current_rain)

                #         # Enregistrement de la valeur brute dans Rg
                #         object_wsd.Rg = current_rain

                #         # Si c'est la première mesure ou pas de précédent, on met 0 comme incrément
                #         if last_record is None:
                #             object_wsd.rain_gauge = 0
                #         else:
                #             previous_rain = round(float(last_record.Rg), 2)
                #             print("previous_rain:", previous_rain)

                #             # Calcul de l'incrément uniquement si la nouvelle valeur est supérieure ou égale
                #             if current_rain >= previous_rain:
                #                 rain_increment = round(current_rain - previous_rain, 2)
                #                 print("rain_increment:", rain_increment)
                #                 object_wsd.rain_gauge = rain_increment
                #             else:
                #                 # Le capteur a peut-être été remis à zéro (nouveau cycle) : on enregistre 0 ou current_rain
                #                 print("Reset detected or invalid data. Resetting increment.")
                #                 object_wsd.rain_gauge = 0

                #     except (TypeError, ValueError) as e:
                #         # En cas de problème de conversion ou valeur absente
                #         print("Error parsing rain_gauge:", e)
                #         object_wsd.rain_gauge = 0
                #         object_wsd.Rg = 0
                #     object_wsd.wind_speed = round((float(object_data.get('wind_speed', 0.0)) * 3.6), 4)  # Convertir en km/h
                #     object_wsd.illumination = object_data.get('irradiation', None)
                #     if object_wsd.illumination is not None:  # Vérifie que la valeur n'est pas None
                #         object_wsd.illumination = round((float(object_wsd.illumination) * 0.8),2)  # Convertir et multiplier
                #     #object_wsd.TEM = object_data.get('HUM', None)


                #     try:
                #         # Sauvegarde dans la base de données
                #         object_wsd.save()
                #         print("Données enregistrées avec succès :", object_wsd)
                #     except Exception as e:
                #         print("Erreur lors de l'enregistrement :", e)
                # else:
                #     print("Dispositif non reconnu, données ignorées.")
                if data['deviceInfo']['devEui'] == 'a84041b02458e028':
                    print("Données reçues du dispositif Model WSC1-L")

                    # Récupération des données depuis 'object'
                    object_data = data.get('object', {})

                    # Création de l'objet wsd
                    object_wsd = wsd()

                    # Affectation des valeurs avec get() pour éviter les erreurs si une clé est absente
                    object_wsd.wind_direction_angle = object_data.get('wind_direction_angle', None)
                    object_wsd.wind_direction = object_data.get('wind_direction', None)
                    object_wsd.HUM = object_data.get('humidity', None)
                    object_wsd.TEM = object_data.get('temperature', None)
                    # Dernier enregistrement avec une pluie non nulle
                    last_record = wsd.objects.exclude(Rg=0).order_by('-Time_Stamp').first()
                    print("last_record from DB:", last_record)

                    # Pluie brute reçue du capteur (accumulée depuis le début)
                    current_rain_raw = object_data.get('rain_instant', None)
                    print("current_rain_raw:", current_rain_raw)

                    try:
                        # Conversion en float
                        current_rain = round(float(current_rain_raw), 2)
                        print("current_rain:", current_rain)

                        # Enregistrement de la valeur brute dans Rg
                        object_wsd.Rg = current_rain

                        # Si c'est la première mesure ou pas de précédent, on met 0 comme incrément
                        if last_record is None:
                            object_wsd.rain_gauge = 0
                        else:
                            previous_rain = round(float(last_record.Rg), 2)
                            print("previous_rain:", previous_rain)

                            # Calcul de l'incrément uniquement si la nouvelle valeur est supérieure ou égale
                            if current_rain >= previous_rain:
                                rain_increment = round(current_rain - previous_rain, 2)
                                print("rain_increment:", rain_increment)
                                object_wsd.rain_gauge = rain_increment
                            else:
                                # Le capteur a peut-être été remis à zéro (nouveau cycle) : on enregistre 0 ou current_rain
                                print("Reset detected or invalid data. Resetting increment.")
                                object_wsd.rain_gauge = 0

                    except (TypeError, ValueError) as e:
                        # En cas de problème de conversion ou valeur absente
                        print("Error parsing rain_gauge:", e)
                        object_wsd.rain_gauge = 0
                        object_wsd.Rg = 0
                    object_wsd.wind_speed = round((float(object_data.get('wind_speed', 0.0)) * 3.6), 4)  # Convertir en km/h
                    object_wsd.illumination = object_data.get('irradiation', None)
                    if object_wsd.illumination is not None:  # Vérifie que la valeur n'est pas None
                        object_wsd.illumination = round((float(object_wsd.illumination) * 0.8),2)  # Convertir et multiplier
                    #object_wsd.TEM = object_data.get('HUM', None)


                    try:
                        # Sauvegarde dans la base de données
                        if float(object_wsd.illumination)>50000:
                            print("irradiation superior ")
                        else:
                            object_wsd.save()
                            print("Données enregistrées avec succès :", object_wsd)
                    except Exception as e:
                        print("Erreur lors de l'enregistrement :", e)
                else:
                    print("Dispositif non reconnu, données ignorées.")

                if data['deviceInfo']['devEui']==pyraGV:
                    input_mA: float = data['object']['IDC_intput_mA']
                    ray = 2000 * (1 + (input_mA - 20) / 16)
                    bat = data['object']['Bat_V']
                    db_obj = Ray2()
                    db_obj.Ray = round(ray,2)
                    db_obj.Bat = bat

                    try:
                        # Sauvegarde dans la base de données
                        db_obj.save()
                        print("Données enregistrées avec succès greeene vision :", db_obj)
                    except Exception as e:
                        print("Erreur lors de l'enregistrement :", e)
                else:
                    print("Dispositif non reconnu, données ignorées.")

                if data['deviceInfo']['devEui'] == '0100000044000000':
                    print("📡 Données reçues du capteur RS485 Rayonnement Solaire")

                    object_data = data.get('object', {})
                    print("📊 object_data RS485 :", object_data)

                    irradiance   = object_data.get('Irradiance_Wm2', None)
                    batterie     = object_data.get('Batterie', None)
                    power_status = object_data.get('Power_Status', None)

                    print(f"☀️  Irradiance  : {irradiance} W/m²")
                    print(f"🔋 Batterie    : {batterie} V")
                    print(f"⚡ Power Status: {power_status}")

                    try:
                        if irradiance is None:
                            print("⚠️ Irradiance absente, données ignorées.")
                        else:
                            db_rs485 = PyraRS485()
                            db_rs485.Irradiance   = round(float(irradiance) * 0.6482, 2)
                            db_rs485.Batterie     = round(float(batterie), 3) if batterie is not None else None
                            db_rs485.Power_Status = int(power_status) if power_status is not None else None
                            db_rs485.save()
                            print(f"✅ RS485 enregistré : {irradiance} W/m², {batterie} V, Power={power_status}")

                    except Exception as e:
                        print(f"❌ Erreur enregistrement RS485 : {e}")

                # if data['deviceInfo']['devEui'] == 'a84041d10858e027':  # Vérifie si c'est bien le capteur de sol
                #     print("📡 Données reçues du Capteur de sol")

                #     # Récupération des données depuis 'object'
                #     object_data = data.get('object', {})
                #     batterie = object_data.get('Batterie', '0')  # Valeur par défaut '0' si absente

                #     print("📊 object_data complet :", object_data)

                #     # Boucle sur les capteurs de sol (Capteur_1 à Capteur_4)
                #     for i in range(1, 5):
                #         capteur_key = f"Capteur_{i}"
                #         if capteur_key in object_data:
                #             capteur_data = object_data[capteur_key]
                #             print(f"🔎 {capteur_key} trouvé :", capteur_data)

                #             try:
                #                 CapSol2.objects.create(
                #                     devId=i,
                #                     Temp=capteur_data.get('Temperature', '0'),
                #                     Hum=capteur_data.get('Humidite', '0'),
                #                     ec=capteur_data.get('Conductivite', '0'),
                #                     N=capteur_data.get('Azote', '0'),
                #                     P=capteur_data.get('Phosphore', '0'),
                #                     K=capteur_data.get('Potassium', '0'),
                #                     Sal=0,  # Valeur par défaut
                #                     Bat=batterie
                #                 )
                #                 print(f"✅ Données enregistrées pour {capteur_key}: {capteur_data}")
                #             except Exception as e:
                #                 print(f"❌ Erreur lors de l'enregistrement de {capteur_key}: {e}")
                #if data['deviceInfo']['devEui'] == 'a84041d10858e027':  # Vérifie si c'est bien le capteur de sol
                #    print("📡 Données reçues du Capteur de sol")

                    # Récupération des données depuis 'object'
                #    object_data = data.get('object', {})
                #    batterie = object_data.get('Batterie', '0')  # Valeur par défaut '0' si absente

                #    print("📊 object_data complet :", object_data)

                    # Boucle sur les capteurs de sol (Capteur_1 à Capteur_4)
                #    for i in range(1, 5):
                #        capteur_key = f"Capteur_{i}"
                #        if capteur_key in object_data:
                #            capteur_data = object_data[capteur_key]
                #            print(f"🔎 {capteur_key} trouvé :", capteur_data)

                            # Vérification si l'une des valeurs dépasse 65000
                #            temperature = float(capteur_data.get('Temperature', '0'))
                #            humidite = float(capteur_data.get('Humidite', '0'))
                #            conductivite = float(capteur_data.get('Conductivite', '0'))
                #            azote = float(capteur_data.get('Azote', '0'))
                #            phosphore = float(capteur_data.get('Phosphore', '0'))
                #            potassium = float(capteur_data.get('Potassium', '0'))

                #            if any(value > 65000 for value in [temperature, humidite, conductivite, azote, phosphore, potassium]):
                #                print(f"⚠️ Ignoré l'enregistrement pour {capteur_key} car une des valeurs dépasse 65000")
                #                continue  # Ignorer cet enregistrement et passer au suivant
                #            try:
                #                CapSol2.objects.create(
                #                    devId=i,
                #                    Temp=temperature,
                #                    Hum=humidite,
                #                    ec=conductivite,
                #                    N=azote,
                #                    P=phosphore,
                #                    K=potassium,
                #                    Sal=0,  # Valeur par défaut
                #                    Bat=batterie
                #                )
                #                print(f"✅ Données enregistrées pour {capteur_key}: {capteur_data}")
                #            except Exception as e:
                #                print(f"❌ Erreur lors de l'enregistrement de {capteur_key}: {e}")




                if data['deviceInfo']['devEui'] == '2cf7f1c064900b68':
                    print("📡 Données reçues du SenseCAP T1000-A")

                    messages = data.get('object', {}).get('messages', [])
                    print("📊 messages :", messages)

                    battery     = None
                    light       = None
                    temperature = None
                    latitude    = None
                    longitude   = None
                    positing    = None

                    for group in messages:
                        if isinstance(group, list):
                            for item in group:
                                t = item.get('type', '')
                                v = item.get('measurementValue')
                                if t == 'Battery':
                                    battery = v
                                elif t == 'Light':
                                    light = v
                                elif t == 'Air Temperature':
                                    temperature = v
                                elif t == 'Latitude':
                                    latitude = v
                                elif t == 'Longitude':
                                    longitude = v
                                elif t == 'Positing Status':
                                    positing = v
                        elif isinstance(group, dict):
                            t = group.get('type', '')
                            v = group.get('measurementValue')
                            if t == 'Battery':
                                battery = v
                            elif t == 'Light':
                                light = v
                            elif t == 'Air Temperature':
                                temperature = v
                            elif t == 'Latitude':
                                latitude = v
                            elif t == 'Longitude':
                                longitude = v
                            elif t == 'Positing Status':
                                positing = v

                    # Déterminer indoor/outdoor
                    if latitude is not None and longitude is not None:
                        indoor_outdoor = 'Outdoor'
                    else:
                        indoor_outdoor = 'Indoor'

                    try:
                        obj = SenseCAPT1000()
                        obj.Battery         = float(battery)     if battery     is not None else None
                        obj.Light           = float(light)       if light       is not None else None
                        obj.Temperature     = float(temperature) if temperature is not None else None
                        obj.Latitude        = float(latitude)    if latitude    is not None else None
                        obj.Longitude       = float(longitude)   if longitude   is not None else None
                        obj.Positing_Status = int(positing)      if positing    is not None else None
                        obj.Indoor_Outdoor  = indoor_outdoor
                        obj.save()
                        print(f"✅ SenseCAP T1000 enregistré : Light={light}% Bat={battery}% {indoor_outdoor}")
                    except Exception as e:
                        print(f"❌ Erreur SenseCAP T1000 : {e}")


                if data['devEui'] == 'a84041d10858e027':
                    print("Données reçues du dispositif contenant plusieurs capteurs")

                    # Extraction des valeurs des capteurs
                    humidites = data.get("Humidite", [])
                    temperatures = data.get("Temperature", [])
                    conductivites = data.get("Conductivite", [])
                    azotes = data.get("Azote", [])
                    phosphores = data.get("Phosphore", [])
                    potassiums = data.get("Potassium", [])

                    # Vérifier que toutes les listes ont la même longueur (nombre de capteurs détectés)
                    capteur_count = min(len(humidites), len(temperatures), len(conductivites), len(azotes), len(phosphores), len(potassiums))

                    for i in range(capteur_count):
                        print(f"Traitement du capteur {i + 1}")

                        capteur = CapSol()
                        capteur.sensor_id = i + 1  # Numéro du capteur
                        capteur.Hum = humidites[i]
                        capteur.Temp = temperatures[i]
                        capteur.Ec = conductivites[i]
                        capteur.N = azotes[i]
                        capteur.P = phosphores[i]
                        capteur.K = potassiums[i]

                        try:
                            # Sauvegarde dans la base de données
                            capteur.save()
                            print(f"Données du capteur {i + 1} enregistrées avec succès :", capteur)
                        except Exception as e:
                            print(f"Erreur lors de l'enregistrement du capteur {i + 1} :", e)
                else:
                    print("Dispositif non reconnu, données ignorées.")
                if data['deviceInfo']['devEui'] == 'ce7554dc00001057':
                    print("Données reçues de l'electrovanne")

                    # Récupération des données depuis 'object'
                    object_data = data.get('object', {})

                    # Création de l'objet `ev_batt`
                    object_batt = ev_batt()

                    # Affectation des valeurs
                    object_batt.batt = object_data.get('battery_voltage', None)

                    # Time_Stamp peut être défini à partir du champ 'time' si présent dans les données reçues
                    if 'time' in data:
                        from django.utils.dateparse import parse_datetime
                        object_batt.Time_Stamp = parse_datetime(data['time'])

                    try:
                        # Sauvegarde dans la base de données
                        object_batt.save()
                        print("Données enregistrées avec succès :", object_batt)
                    except Exception as e:
                        print("Erreur lors de l'enregistrement :", e)
                else:
                    print("Dispositif non reconnu, données ignorées.")





            except :
                print("chirpstack integration error")


    return HttpResponse(status=200)




##-----Les alertes de mes capteurs---------------------####"


# def cwsi_data(request):
#     # Retrieve all records from the cwsi model
#     cwsi_records = cwsi.objects.all()

#     # Pass the data to the template
#     context = {
#         'cwsi_records': cwsi_records
#     }
#     return render(request, 'cwsi/cwsi01.html', context)

from django.utils.timezone import make_aware
import datetime
from django.shortcuts import render
from .models import Data2, wsd  # Assurez-vous que ces modèles sont correctement importés

def filter_data(request, field_data2, field_wsd, field_rs_temp1, field_rs_temp2, field_WD, template_name):                              ###### 2 arg ++
    """
    Fonction générique pour filtrer les données avec des champs différents pour Data2 et wsd.
    - field_data2 : Nom du champ à récupérer pour Data2 (ex : 'Temp', 'Hum', etc.).
    - field_wsd : Nom du champ à récupérer pour wsd (ex : 'TEM', 'HUM', etc.).
    - template_name : Nom du fichier HTML à rendre.
    """
    # Récupération des dates depuis le formulaire GET
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Si l'utilisateur a spécifié des dates, les convertir en datetime
    if start_date and end_date:
        start_date = make_aware(datetime.datetime.strptime(start_date, "%Y-%m-%d"))
        end_date = make_aware(datetime.datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59))
    else:
        # Sinon, récupérer les données de la dernière journée
        one_day_ago = (datetime.datetime.now() - datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = make_aware(one_day_ago)
        end_date = make_aware(datetime.datetime.now().replace(hour=23, minute=59, second=59))

    # Filtrage des données dans la plage spécifiée
    all_data2 = Data2.objects.filter(Time_Stamp__range=(start_date, end_date))
    all_wsd = wsd.objects.filter(Time_Stamp__range=(start_date, end_date))
    #print("Dta filter wsd : ",all_wsd,all_data2)                                               #####!!!!!!!!!!!!!!!!!!!!!!!!
    # Extraction des données pour les graphiques
    labels_data2 = [data.Time_Stamp.strftime("%Y-%m-%d %H:%M:%S") for data in all_data2]
    labels_wsd = [data.Time_Stamp.strftime("%Y-%m-%d %H:%M:%S") for data in all_wsd]

    #######################!!!!!!!!!!!!!!#######################################

        # Filtrage des données dans la plage spécifiée
    all_rs_temp = rs_temp.objects.filter(Time_Stamp__range=(start_date, end_date))
    print("Dta filter wsd : ",all_wsd,all_data2,all_rs_temp)
    # Extraction des données pour les graphiques
    labels_rs_temp = [data.Time_Stamp.strftime("%Y-%m-%d %H:%M:%S") for data in all_rs_temp]

    data_rs_temp1 = [getattr(data, field_rs_temp1, 0) if getattr(data, field_rs_temp1, None) is not None else 0 for data in all_rs_temp] if field_rs_temp1 else []
    data_rs_temp2 = [getattr(data, field_rs_temp2, 0) if getattr(data, field_rs_temp2, None) is not None else 0 for data in all_rs_temp] if field_rs_temp2 else []


    ###############################################################

    data_data2 = [getattr(data, field_data2, 0) if getattr(data, field_data2, None) is not None else 0 for data in all_data2]
    data_wsd = [getattr(data, field_wsd, 0) if getattr(data, field_wsd, None) is not None else 0 for data in all_wsd]
    print("Dta filter wsd : ",data_wsd,data_data2,data_rs_temp1,data_rs_temp2)                                           ##########!!!!!!!!!!!!!!!!!!!!!!!
    # Récupération du dernier enregistrement (gestion des valeurs `None`)
    lst_data2 = Data2.objects.last()
    lst_wsd = wsd.objects.last()

    ##############!!!!!!!!!!!!!!!!!#######################
    lst_rs_temp = rs_temp.objects.last()
    last_rs_temp1_value = getattr(lst_rs_temp, field_rs_temp1, 0) if lst_rs_temp and field_rs_temp1 and getattr(lst_rs_temp, field_rs_temp1, None) is not None else 0
    last_rs_temp2_value = getattr(lst_rs_temp, field_rs_temp2, 0) if lst_rs_temp and field_rs_temp2 and getattr(lst_rs_temp, field_rs_temp2, None) is not None else 0

    #############################

    #visioGreen WS
    all_weather = WeatherData.objects.filter(created_at__range=(start_date, end_date))
    labels_weather = [data.created_at.strftime("%Y-%m-%d %H:%M:%S") for data in all_weather]
    data_wind_speed = [data.wind_speed_ms or 0 for data in all_weather]
    data_temperature = [data.temperature_c or 0 for data in all_weather]
    data_humidity = [data.humidity_pct or 0 for data in all_weather]
    data_rain = [data.rain_mm or 0 for data in all_weather]
    last_weather = WeatherData.objects.last()

    last_temp = last_weather.temperature_c if last_weather else 0
    last_hum = last_weather.humidity_pct if last_weather else 0
    last_wind = last_weather.wind_speed_kmh if last_weather else 0
    last_rain = last_weather.rain_mm if last_weather else 0

    zipped_weather_temp = zip(labels_weather, data_temperature)
    zipped_weather_hum = zip(labels_weather, data_humidity)
    zipped_weather_wind = zip(labels_weather, data_wind_speed)
    zipped_weather_rain = zip(labels_weather, data_rain)
    #Fin WS VG

    last_data2_value = getattr(lst_data2, field_data2, 0) if lst_data2 and getattr(lst_data2, field_data2, None) is not None else 0
    last_wsd_value = getattr(lst_wsd, field_wsd, 0) if lst_wsd and getattr(lst_wsd, field_wsd, None) is not None else 0
    zipped_data2 = zip(labels_data2, data_data2)
    print("zipped : ",zipped_data2)
    zipped_datawsd = zip(labels_wsd, data_wsd)
    print("zipped : ",zipped_datawsd)

    #############!!!!!!!!!!!!!!!!!!#############
    zipped_rs_temp1 = zip(labels_rs_temp, data_rs_temp1)
    print("zipped : ",zipped_rs_temp1)
    zipped_rs_temp2 = zip(labels_rs_temp, data_rs_temp2)
    print("zipped : ",zipped_rs_temp2)
    ##########################################

    # Création du contexte
    context = {
        'all_data2': all_data2,
        'all_wsd': all_wsd,
        'lst_data2': last_data2_value,
        'lst_wsd': last_wsd_value,
        'labels_data2': labels_data2,
        'labels_wsd': labels_wsd,
        'data_data2': data_data2,
        'data_wsd': data_wsd,
        'start_date': start_date.strftime("%Y-%m-%d"),
        'end_date': end_date.strftime("%Y-%m-%d"),
        'zipped_data2': list(zipped_data2),
        'zipped_datawsd': list(zipped_datawsd),
        ###############!!!!!!!!!!!!!!!!!!!!!!!##################
        'zipped_rs_temp1': list(zipped_rs_temp1),
        'zipped_rs_temp2': list(zipped_rs_temp2),
        'lst_rs_temp1': last_rs_temp1_value,
        'lst_rs_temp2': last_rs_temp2_value,
        'all_rs_temp': all_rs_temp,
        'labels_rs_temp': labels_rs_temp,
        'data_rs_temp1': data_rs_temp1,
        'data_rs_temp2': data_rs_temp2,
        # WeatherData
        'all_weather': all_weather,
        'labels_weather': labels_weather,

        'data_weather_temp': data_temperature,
        'data_weather_hum': data_humidity,
        'data_weather_wind': data_wind_speed,
        'data_weather_rain': data_rain,

        'zipped_weather_temp': list(zipped_weather_temp),
        'zipped_weather_hum': list(zipped_weather_hum),
        'zipped_weather_wind': list(zipped_weather_wind),
        'zipped_weather_rain': list(zipped_weather_rain),

        'last_weather_temp': last_temp,
        'last_weather_hum': last_hum,
        'last_weather_wind': last_wind,
        'last_weather_rain': last_rain,

    }

    return render(request, template_name, context)

# Vue pour la température
def data_filter(request):
    return filter_data(request, field_data2='Temp', field_wsd='TEM',field_rs_temp1='temp1',field_rs_temp2='temp2', field_WD='temperature_c',template_name="enviro/temp1.html")   ############!!!!!!!!!!!

# Vue pour l'humidité
def data_filter_hum(request):
    return filter_data(request, field_data2='Hum', field_wsd='HUM',field_rs_temp1='hum1',field_rs_temp2='hum2', field_WD='humidity_pct',template_name="enviro/hum1.html")       ###########!!!!!!!!!!!!

# Vue pour la vitesse de vent
def data_filter_ws(request):
    return filter_data(request, field_data2='Wind_Speed', field_wsd='wind_speed',field_rs_temp1='temp1',field_rs_temp2='temp2', field_WD='wind_speed_ms',template_name="enviro/tvoc1.html")

# Vue pour la pluie
def data_filter_pl(request):
    return filter_data(request, field_data2='Rain', field_wsd='rain_gauge',field_rs_temp1='temp1',field_rs_temp2='temp2', field_WD='rain_mm',template_name="enviro/tvoc3.html")

# def data_filter_pl(request):
#     return filter_data(request, field_data2='Rain', field_wsd='rain_gauge', template_name="enviro/tvoc3.html")

from django.shortcuts import render
from django.utils.timezone import make_aware
import datetime
from .models import Ray2, wsd, PyraRS485

def data_filter_ry(request):
    """
    Vue pour afficher les données des pyranomètres Ray2, wsd et PyraRS485
    - Par défaut affiche la journée d'aujourd'hui
    - Permet de filtrer via start_date et end_date en GET (format 'YYYY-MM-DD')
    """

    # Récupération des dates depuis GET
    start_date_str = request.GET.get('start_date')
    end_date_str   = request.GET.get('end_date')

    if start_date_str and end_date_str:
        # Dates fournies par l'utilisateur
        start_date = make_aware(datetime.datetime.strptime(start_date_str, "%Y-%m-%d"))
        end_date   = make_aware(datetime.datetime.strptime(end_date_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59))
    else:
        # Par défaut : journée d'aujourd'hui
        today = datetime.datetime.now()
        start_date = make_aware(datetime.datetime(today.year, today.month, today.day, 0, 0, 0))
        end_date   = make_aware(datetime.datetime(today.year, today.month, today.day, 23, 59, 59))

    # --- Requête des données ---
    all_data2 = Ray2.objects.filter(DateRay__range=(start_date, end_date)).order_by('DateRay')
    all_wsd   = wsd.objects.filter(Time_Stamp__range=(start_date, end_date)).order_by('Time_Stamp')

    # Préparer les listes pour les graphiques
    labels_data2 = [data.DateRay.strftime("%Y-%m-%d %H:%M:%S") for data in all_data2]
    data_data2   = [data.Ray if data.Ray is not None else 0 for data in all_data2]

    labels_wsd = [data.Time_Stamp.strftime("%Y-%m-%d %H:%M:%S") for data in all_wsd]
    data_wsd   = [data.illumination if data.illumination is not None else 0 for data in all_wsd]

    zipped_data2   = list(zip(labels_data2, data_data2))
    zipped_datawsd = list(zip(labels_wsd, data_wsd))

    # Données PyraRS485
    rs485_qs = PyraRS485.objects.filter(DateRay__range=(start_date, end_date)).order_by('DateRay')
    zipped_rs485 = [
        (entry.DateRay.strftime("%Y-%m-%dT%H:%M:%S"), entry.Irradiance)
        for entry in rs485_qs if entry.Irradiance is not None
    ]

    last = PyraRS485.objects.order_by('-DateRay').first()

    context = {
        'zipped_data2':   zipped_data2,
        'zipped_datawsd': zipped_datawsd,
        'zipped_rs485':   zipped_rs485,
        'last':           last,
        'start_date':     start_date.strftime("%Y-%m-%d"),
        'end_date':       end_date.strftime("%Y-%m-%d"),
        'data_data2':     data_data2,
        'labels_data2':   labels_data2,
        'data_wsd':       data_wsd,
        'labels_wsd':     labels_wsd,
    }

    return render(request, "enviro/temp3_rs485.html", context)
def comparaison_rayonnement(request):
    from django.utils.timezone import now
    from datetime import timedelta
    import datetime

    une_heure = now() - timedelta(hours=1)

    # Dernières valeurs instantanées
    tab2      = Ray2.objects.order_by('-DateRay').first()
    tab_rs485 = PyraRS485.objects.order_by('-DateRay').first()

    # Paires synchronisées sur la dernière heure
    rs485_qs  = PyraRS485.objects.filter(DateRay__gte=une_heure, Irradiance__gt=0).order_by('DateRay')
    pyragv_qs = Ray2.objects.filter(DateRay__gte=une_heure, Ray__gt=0).order_by('DateRay')

    pairs_rs = []
    pairs_gv = []

    for rs in rs485_qs:
        window_start = rs.DateRay - datetime.timedelta(minutes=8)
        window_end   = rs.DateRay + datetime.timedelta(minutes=8)
        closest = pyragv_qs.filter(DateRay__gte=window_start, DateRay__lte=window_end).first()
        if closest:
            pairs_rs.append(rs.Irradiance)
            pairs_gv.append(closest.Ray)

    # Moyennes synchronisées
    Ravg_1h     = round(sum(pairs_gv) / len(pairs_gv), 2) if pairs_gv else 0
    Rs485avg_1h = round(sum(pairs_rs) / len(pairs_rs), 2) if pairs_rs else 0

    # Max/Min sur la dernière heure
    from django.db.models import Max, Min, Avg
    Rx_1h  = Ray2.objects.filter(DateRay__gte=une_heure, Ray__gt=0).aggregate(Max('Ray'))['Ray__max']
    Rm_1h  = Ray2.objects.filter(DateRay__gte=une_heure, Ray__gt=0).aggregate(Min('Ray'))['Ray__min']
    Rs485x_1h = PyraRS485.objects.filter(DateRay__gte=une_heure, Irradiance__gt=0).aggregate(Max('Irradiance'))['Irradiance__max']
    Rs485m_1h = PyraRS485.objects.filter(DateRay__gte=une_heure, Irradiance__gt=0).aggregate(Min('Irradiance'))['Irradiance__min']

    context = {
        'tab2':         tab2,
        'tab_rs485':    tab_rs485,
        'Ravg_1h':      Ravg_1h,
        'Rx_1h':        round(Rx_1h, 2)    if Rx_1h    else 0,
        'Rm_1h':        round(Rm_1h, 2)    if Rm_1h    else 0,
        'Rs485avg_1h':  Rs485avg_1h,
        'Rs485x_1h':    round(Rs485x_1h, 2) if Rs485x_1h else 0,
        'Rs485m_1h':    round(Rs485m_1h, 2) if Rs485m_1h else 0,
    }
    return render(request, 'enviro/comparaison_rayonnement.html', context)

def sensecap_t1000_view(request):
    start_date = request.GET.get('start_date')
    end_date   = request.GET.get('end_date')

    if start_date and end_date:
        start_date = make_aware(datetime.datetime.strptime(start_date, "%Y-%m-%d"))
        end_date   = make_aware(datetime.datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59))
    else:
        one_day_ago = (datetime.datetime.now() - datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0)
        start_date  = make_aware(one_day_ago)
        end_date    = make_aware(datetime.datetime.now().replace(hour=23, minute=59, second=59))

    qs = SenseCAPT1000.objects.filter(Time_Stamp__range=(start_date, end_date)).order_by('Time_Stamp')

    zipped_light = [
        (e.Time_Stamp.strftime("%Y-%m-%dT%H:%M:%S"), e.Light)
        for e in qs if e.Light is not None
    ]
    zipped_temp = [
        (e.Time_Stamp.strftime("%Y-%m-%dT%H:%M:%S"), e.Temperature)
        for e in qs if e.Temperature is not None
    ]
    zipped_bat = [
        (e.Time_Stamp.strftime("%Y-%m-%dT%H:%M:%S"), e.Battery)
        for e in qs if e.Battery is not None
    ]

    last = SenseCAPT1000.objects.order_by('-Time_Stamp').first()

    # Dernières positions GPS (outdoor uniquement)
    gps_points = list(
        SenseCAPT1000.objects.filter(
            Time_Stamp__range=(start_date, end_date),
            Latitude__isnull=False,
            Longitude__isnull=False
        ).order_by('-Time_Stamp').values('Latitude', 'Longitude', 'Time_Stamp')[:50]
    )

    context = {
        'zipped_light': zipped_light,
        'zipped_temp':  zipped_temp,
        'zipped_bat':   zipped_bat,
        'last':         last,
        'gps_points':   gps_points,
        'start_date':   start_date.strftime("%Y-%m-%d"),
        'end_date':     end_date.strftime("%Y-%m-%d"),
    }
    return render(request, 'enviro/sensecap_t1000.html', context)

def filter_ray_battery(request):
    """
    Filtrer les valeurs de la batterie (Bat) du modèle Ray2 sur une période donnée ou par défaut sur la dernière journée.
    - template_name : le nom du fichier HTML à afficher.
    """

    # 1. Récupération des dates depuis le formulaire GET
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # 2. Conversion des dates ou utilisation de la journée précédente
    if start_date and end_date:
        start_date = make_aware(datetime.datetime.strptime(start_date, "%Y-%m-%d"))
        end_date = make_aware(datetime.datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59))
    else:
        one_day_ago = (datetime.datetime.now() - datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0)
        start_date = make_aware(one_day_ago)
        end_date = make_aware(datetime.datetime.now().replace(hour=23, minute=59, second=59))

    # 3. Filtrage des données dans l'intervalle de dates
    all_ray = Ray2.objects.filter(DateRay__range=(start_date, end_date))

    # 4. Extraction des labels (timestamps) et des valeurs de la batterie
    labels = [entry.DateRay.strftime("%Y-%m-%d %H:%M:%S") for entry in all_ray]
    bat_values = [entry.Bat if entry.Bat is not None else 0 for entry in all_ray]

    # 5. Récupération de la dernière valeur connue de la batterie
    last_ray = Ray2.objects.last()
    last_bat_value = last_ray.Bat if last_ray and last_ray.Bat is not None else 0

    # 6. Données groupées pour affichage
    zipped_data = zip(labels, bat_values)

    # 7. Contexte à envoyer au template
    context = {
        'all_ray': all_ray,
        'labels': labels,
        'bat_values': bat_values,
        'last_bat_value': last_bat_value,
        'start_date': start_date.strftime("%Y-%m-%d"),
        'end_date': end_date.strftime("%Y-%m-%d"),
        'zipped_data': list(zipped_data),
    }

    return render(request, "enviro/temp15.html", context)

def pyra_rs485(request):
    """
    Page de visualisation du capteur RS485 de rayonnement solaire.
    Affiche :
      - Valeur instantanée (dernière mesure)
      - Jauge W/m²
      - Courbe historique avec filtre de dates
      - Comparaison avec pyraGV (Ray2 commun)
    """
    # --- Filtre de dates ---
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date and end_date:
        start_date = make_aware(datetime.datetime.strptime(start_date, "%Y-%m-%d"))
        end_date   = make_aware(datetime.datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59))
    else:
        one_day_ago = (datetime.datetime.now() - datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0)
        start_date  = make_aware(one_day_ago)
        end_date    = make_aware(datetime.datetime.now().replace(hour=23, minute=59, second=59))

    # --- Données RS485 (stockées dans Ray2) ---
    # Note : Ray2 ne distingue pas les sources par devEUI.
    # Les deux pyranomètres (pyraGV + RS485) partagent Ray2.
    # Pour différencier : si vous souhaitez à l'avenir les séparer,
    # il faudra créer un modèle distinct. Pour l'instant on affiche tout Ray2.
    all_ray = Ray2.objects.filter(DateRay__range=(start_date, end_date)).order_by('DateRay')

    labels_ray = [entry.DateRay.strftime("%Y-%m-%d %H:%M:%S") for entry in all_ray]
    values_ray  = [round(entry.Ray, 2) if entry.Ray is not None else 0 for entry in all_ray]
    zipped_ray  = list(zip(labels_ray, values_ray))

    # --- Dernière valeur instantanée ---
    last_ray = Ray2.objects.order_by('-DateRay').first()
    last_ray_value = round(last_ray.Ray, 2) if last_ray and last_ray.Ray is not None else 0
    last_bat_value = round(last_ray.Bat, 2) if last_ray and last_ray.Bat is not None else None
    last_timestamp  = last_ray.DateRay.strftime("%Y-%m-%d %H:%M:%S") if last_ray else "—"

    # --- Statistiques du jour ---
    agg = Ray2.objects.filter(DateRay__range=(start_date, end_date)).aggregate(
        ray_max=Max('Ray'),
        ray_min=Min('Ray'),
        ray_avg=Avg('Ray'),
    )
    ray_max = round(agg['ray_max'], 2) if agg['ray_max'] is not None else 0
    ray_min = round(agg['ray_min'], 2) if agg['ray_min'] is not None else 0
    ray_avg = round(agg['ray_avg'], 2) if agg['ray_avg'] is not None else 0

    context = {
        # Données graphique
        'zipped_ray':    zipped_ray,
        'labels_ray':    labels_ray,
        'values_ray':    values_ray,

        # Valeur instantanée + jauge
        'last_ray_value':  last_ray_value,
        'last_bat_value':  last_bat_value,
        'last_timestamp':  last_timestamp,

        # Stats
        'ray_max': ray_max,
        'ray_min': ray_min,
        'ray_avg': ray_avg,

        # Filtre dates (pour ré-afficher dans le formulaire)
        'start_date': start_date.strftime("%Y-%m-%d"),
        'end_date':   end_date.strftime("%Y-%m-%d"),
    }

    return render(request, "pyra_rs485.html", context)

def data_filter_et0(request):
    # Récupération des valeurs du formulaire
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Si l'utilisateur a spécifié des dates, on les utilise, sinon 15 derniers jours
    if start_date and end_date:
        start_date = make_aware(datetime.datetime.strptime(start_date, "%Y-%m-%d"))
        end_date = make_aware(datetime.datetime.strptime(end_date, "%Y-%m-%d")).replace(hour=23, minute=59, second=59)
    else:
        now = datetime.datetime.now()
        start_date = make_aware((now - datetime.timedelta(days=15)).replace(hour=0, minute=0, second=0, microsecond=0))
        end_date = make_aware(now.replace(hour=23, minute=59, second=59))

    # Filtrage des données pour ET0o et ET0DR
    all_et0 = ET0o.objects.filter(Time_Stamp__range=(start_date, end_date))
    all_et0dr = ET0DR.objects.filter(Time_Stamp__range=(start_date, end_date))

    # Collecte des labels et données
    labels_et0 = []
    data_et0 = []
    for data in all_et0:
        labels_et0.append(data.Time_Stamp.strftime("%Y-%m-%d"))
        data_et0.append(data.value if data.value is not None else 0)

    labels_et0dr = []
    data_et0dr = []
    for data in all_et0dr:
        labels_et0dr.append(data.Time_Stamp.strftime("%Y-%m-%d"))
        data_et0dr.append(data.value if data.value is not None else 0)

    # Construction de listes zip
    list_zipped_data2 = list(zip(labels_et0dr, data_et0dr))
    list_zipped_datawsd = list(zip(labels_et0, data_et0))

    # Derniers objets
    last_et0 = ET0o.objects.last()
    last_et0dr = ET0DR.objects.last()

    # Liste de toutes les dates
    all_dates = sorted(set(labels_et0dr) | set(labels_et0))

    # Dictionnaires date -> valeur
    zipped_data2_dates = {date: value for date, value in list_zipped_data2}
    zipped_datawsd_dates = {date: value for date, value in list_zipped_datawsd}

    # Initialiser les listes
    dragino_data = []
    sensecap_data = []

    # Variables pour mémoriser la dernière valeur
    last_dragino_value = 0
    last_sensecap_value = 0

    # Générer les données alignées
    for date in all_dates:
        dragino_y = zipped_data2_dates.get(date, None)
        sensecap_y = zipped_datawsd_dates.get(date, None)

        if dragino_y is None:
            dragino_y = last_dragino_value
        else:
            last_dragino_value = dragino_y

        if sensecap_y is None:
            sensecap_y = last_sensecap_value
        else:
            last_sensecap_value = sensecap_y

        dragino_data.append({'x': date, 'y': dragino_y})
        sensecap_data.append({'x': date, 'y': sensecap_y})

    # Préparer le contexte pour le template
    context = {
        'all_et0': all_et0,
        'all_et0dr': all_et0dr,
        'last_et0': last_et0,
        'last_et0dr': last_et0dr,
        'labels_et0': labels_et0,
        'labels_et0dr': labels_et0dr,
        'data_et0': data_et0,
        'data_et0dr': data_et0dr,
        'start_date': start_date.strftime("%Y-%m-%d"),
        'end_date': end_date.strftime("%Y-%m-%d"),
        'zipped_data2': list_zipped_data2,
        'zipped_datawsd': list_zipped_datawsd,
        'dragino_data': dragino_data,
        'sensecap_data': sensecap_data,
    }

    return render(request, "enviro/hum15.html", context)

from django.utils.timezone import make_aware
from django.shortcuts import render
import datetime
from .models import Data2

def filter_light_intensity(request):
    """
    Filtrer les valeurs de Light_Intensity du modèle Data2 sur une période donnée
    ou par défaut sur la dernière journée.
    """

    # 1. Récupération des dates depuis le formulaire GET
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # 2. Conversion des dates ou utilisation de la journée précédente
    if start_date and end_date:
        start_date = make_aware(datetime.datetime.strptime(start_date, "%Y-%m-%d"))
        end_date = make_aware(datetime.datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59))
    else:
        one_day_ago = (datetime.datetime.now() - datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0)
        start_date = make_aware(one_day_ago)
        end_date = make_aware(datetime.datetime.now().replace(hour=23, minute=59, second=59))

    # 3. Filtrage des données dans l'intervalle de dates
    all_data = Data2.objects.filter(Time_Stamp__range=(start_date, end_date))

    # 4. Extraction des labels (timestamps) et des valeurs de Light_Intensity
    labels = [entry.Time_Stamp.strftime("%Y-%m-%d %H:%M:%S") for entry in all_data]
    light_values = [entry.Light_Intensity if entry.Light_Intensity is not None else 0 for entry in all_data]

    # 5. Récupération de la dernière valeur connue
    last_entry = Data2.objects.last()
    last_light_value = last_entry.Light_Intensity if last_entry and last_entry.Light_Intensity is not None else 0

    # 6. Données groupées pour affichage
    zipped_data = zip(labels, light_values)

    # 7. Contexte à envoyer au template
    context = {
        'all_data': all_data,
        'labels': labels,
        'light_values': light_values,
        'last_light_value': last_light_value,
        'start_date': start_date.strftime("%Y-%m-%d"),
        'end_date': end_date.strftime("%Y-%m-%d"),
        'zipped_data': list(zipped_data),
    }

    return render(request, "enviro/light.html", context)
##################################################################

###########################batt_Vannes#################################
#def batt_vannes(request):

 #   lasted = ev_batt.objects.last()
  #  context={'lasted':lasted}
   # return render(request,"batt_niveau.html",context)
    ############EV1##################
def batt_vannes(request):

    lasted = ev_batt.objects.last()
    lasted2 = ev_batt2.objects.last()
    lasted3 = ev_batt3.objects.last()

    # Lecture des paramètres GET avec valeurs par défaut

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Gestion des dates
    if start_date and end_date:
        start_date = make_aware(datetime.datetime.strptime(start_date, "%Y-%m-%d"))
        end_date = make_aware(datetime.datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59))
    else:
        one_day_ago = (datetime.datetime.now() - datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0)
        start_date = make_aware(one_day_ago)
        end_date = make_aware(datetime.datetime.now().replace(hour=23, minute=59, second=59))

      # Filtrage des données dans la plage spécifiée
    all_ev_batt = ev_batt.objects.filter(Time_Stamp__range=(start_date, end_date))
    all_ev_batt2 = ev_batt2.objects.filter(Time_Stamp__range=(start_date, end_date))
    all_ev_batt3 = ev_batt3.objects.filter(Time_Stamp__range=(start_date, end_date))
    print("Dta filter EV battrie : ",all_ev_batt)
    print("Dta filter EV2 battrie : ",all_ev_batt2)
    print("Dta filter EV3 battrie : ",all_ev_batt3)
    # Extraction des données pour les graphiques
    labels = [data.Time_Stamp.strftime("%Y-%m-%d %H:%M:%S") for data in all_ev_batt]
    data = [data.batt if data.batt is not None else 0 for data in all_ev_batt]
    zipped_data = zip(labels, data)
    print("zipped : ",zipped_data)
    labels2 = [data.Time_Stamp.strftime("%Y-%m-%d %H:%M:%S") for data in all_ev_batt2]
    data2 = [data.batt if data.batt is not None else 0 for data in all_ev_batt2]
    zipped_data2 = zip(labels2, data2)
    print("zipped2 : ",zipped_data2)
    labels3 = [data.Time_Stamp.strftime("%Y-%m-%d %H:%M:%S") for data in all_ev_batt3]
    data3 = [data.batt if data.batt is not None else 0 for data in all_ev_batt3]
    zipped_data3 = zip(labels3, data3)
    print("zipped3 : ",zipped_data3)

    context = {
	    'lasted':lasted,
	    'lasted2':lasted2,
	    'lasted3':lasted3,
        'all_ev_batt': all_ev_batt,
        'all_ev_batt2': all_ev_batt2,
        'all_ev_batt3': all_ev_batt3,
        'start_date': start_date.strftime("%Y-%m-%d"),
        'end_date': end_date.strftime("%Y-%m-%d"),
        'zipped_data': list(zipped_data),
        'zipped_data2': list(zipped_data2),
        'zipped_data3': list(zipped_data3),


    }

    return render(request,"batt_niveau.html",context)





##################################################################
   ############Makerfabs##################

# Fonction pour envoyer une commande MQTT
def send_makerfabs_command(command_base64):
    client = mqtt.Client()
    # client.username_pw_set("mqttuser", "mqttp$$ow")
    client.connect("161.97.107.82", 80)

    topic = "application/7dd86cd4-ab8a-449f-814c-36c5c061eb7e/device/48e663fffe300aed/command/down"
    payload = f"""{{
        "devEui": "48e663fffe300aed",
        "confirmed": true,
        "fPort": 6,
        "data": "{command_base64}"
    }}"""

    client.publish(topic, payload)
    client.disconnect()

def makerFabs_ev(request):

    lasted = Makerfabs.objects.last()
    if request.method == "POST":
        action = request.POST.get("action")  # récupère "on" ou "off"

        if action == "on":
            send_makerfabs_command("AQ==")   # 0x01 = ON

        elif action == "off":
            send_makerfabs_command("AA==")   # 0x00 = OFF


    # Lecture des paramètres GET avec valeurs par défaut

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Gestion des dates
    if start_date and end_date:
        start_date = make_aware(datetime.datetime.strptime(start_date, "%Y-%m-%d"))
        end_date = make_aware(datetime.datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59))
    else:
        one_day_ago = (datetime.datetime.now() - datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0)
        start_date = make_aware(one_day_ago)
        end_date = make_aware(datetime.datetime.now().replace(hour=23, minute=59, second=59))

      # Filtrage des données dans la plage spécifiée
    all_Makerfabs = Makerfabs.objects.filter(Time_Stamp__range=(start_date, end_date))
    print("Dta filter Makerfabs : ",all_Makerfabs)

        # CUMULÉ TOTAL DU VOLUME NORMAL
    total_volume = sum(
        record.Volume for record in all_Makerfabs
        if record.Volume is not None and record.valve == 1
    )

    # Extraction des données pour les graphiques
    labels = [data.Time_Stamp.strftime("%Y-%m-%d %H:%M:%S") for data in all_Makerfabs]
    data = [data.batt if data.batt is not None else 0 for data in all_Makerfabs]
    zipped_data = zip(labels, data)
    print("zipped : ",zipped_data)


    context = {
	    'lasted':lasted,
        'all_Makerfabs': all_Makerfabs,

        'start_date': start_date.strftime("%Y-%m-%d"),
        'end_date': end_date.strftime("%Y-%m-%d"),
        'zipped_data': list(zipped_data),
        'total_volume': round(total_volume, 3),

    }

    return render(request,"makerfabs.html",context)






##################################################################



def filter_uv_index(request):
    """
    Filtrer les valeurs de UV_Index du modèle Data2 sur une période donnée
    ou par défaut sur la dernière journée.
    """

    # Récupération des dates
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Conversion ou valeurs par défaut
    if start_date and end_date:
        start_date = make_aware(datetime.datetime.strptime(start_date, "%Y-%m-%d"))
        end_date = make_aware(datetime.datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59))
    else:
        one_day_ago = (datetime.datetime.now() - datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0)
        start_date = make_aware(one_day_ago)
        end_date = make_aware(datetime.datetime.now().replace(hour=23, minute=59, second=59))

    # Filtrage des données
    all_data = Data2.objects.filter(Time_Stamp__range=(start_date, end_date))

    # Extraction labels et valeurs
    labels = [entry.Time_Stamp.strftime("%Y-%m-%d %H:%M:%S") for entry in all_data]
    uv_values = [entry.UV_Index if entry.UV_Index is not None else 0 for entry in all_data]

    # Dernière valeur connue
    last_entry = Data2.objects.last()
    last_uv_value = last_entry.UV_Index if last_entry and last_entry.UV_Index is not None else 0

    # Données groupées
    zipped_data = zip(labels, uv_values)

    # Contexte
    context = {
        'all_data': all_data,
        'labels': labels,
        'uv_values': uv_values,
        'last_uv_value': last_uv_value,
        'start_date': start_date.strftime("%Y-%m-%d"),
        'end_date': end_date.strftime("%Y-%m-%d"),
        'zipped_data': list(zipped_data),
    }

    return render(request, "enviro/uv.html", context)
# def wind_rose_data(request):
#     # Filtrer les données sur les 7 derniers jours
#     wind_data = wsd.objects.filter(Time_Stamp__gte=timezone.now() - timezone.timedelta(days=7)).values_list('wind_direction', flat=True)

#     # Compter les occurrences de chaque direction
#     direction_counts = Counter(wind_data)

#     # Calculer le pourcentage
#     total = sum(direction_counts.values())
#     wind_percentages = [{"direction": direction, "percentage": round((count / total) * 100, 2)} for direction, count in direction_counts.items()]

#     return JsonResponse(wind_percentages, safe=False)

# from django.shortcuts import render
# import json

# def mych(request):
#     # Supposons que vous avez des données de ventes et des catégories de l'année
#     sales_data = [30, 40, 35, 50, 49, 60, 70, 91, 125]
#     categories_data = [1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999]

#     # Convertir les données en JSON
#     sales_data_json = json.dumps(sales_data)
#     categories_data_json = json.dumps(categories_data)

#     # Affichez le contenu de votre contexte pour le débogage
#     print("Sales data JSON:", sales_data_json)
#     print("Categories data JSON:", categories_data_json)

#     # Passer les données vers le modèle HTML
#     context = {
#         'sales_data_json': sales_data_json,
#         'categories_data_json': categories_data_json,
#     }

#     # Rendre le modèle HTML avec les données
#     return render(request, 'test.html', context)

# Configuration de ChirpStack
CHIRPSTACK_API_URL = "http://213.32.91.140:8080/api/devices/ce7554dc00001057/queue"
CHIRPSTACK_API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjaGlycHN0YWNrIiwiaXNzIjoiY2hpcnBzdGFjayIsInN1YiI6IjY5NTMzMjAxLWFmMzYtNDliNS05MjQxLTE5ZTBjMTg4MDFhMiIsInR5cCI6ImtleSJ9.klR4xIax_a1IOf5nDLlhosJHSU7_fmtCio1Jd6MGHJs"  # Remplace avec ta clé API
@csrf_exempt
def send_command(request):
    if request.method == "POST":
        command = request.POST.get("command")  # "ON" ou "OFF"
        value = request.POST.get("value")  # Valeur entière (0-255)

        if not command or not value:
            return render(request, "control.html", {"error": "Commande ou valeur manquante !"})

        # Convertir ON/OFF en binaire
        command_bin = 1 if command == "ON" else 0
        value_int = int(value)

        # Création du payload : [ON/OFF, valeur]
        payload_bytes = bytes([command_bin, value_int])
        payload_hex = payload_bytes.hex()  # Conversion en hexadécimal

        headers = {
            "Content-Type": "application/json",
            "Grpc-Metadata-Authorization": f"Bearer {CHIRPSTACK_API_KEY}"
        }

        payload = {
            "deviceQueueItem": {
                "confirmed": True,
                "fPort": 1,
                "data": payload_hex  # Encodé en hexadécimal
            }
        }

        response = requests.post(CHIRPSTACK_API_URL, json=payload, headers=headers)

        if response.status_code == 200:
            return render(request, "control.html", {"success": "Commande envoyée avec succès !"})
        else:
            return render(request, "control.html", {"error": f"Échec de l'envoi ! {response.text}"})

    return render(request, "control.html")

from django.utils.timezone import now

def compare_sensors(request):
    # Définir la date limite (3 jours avant aujourd'hui)
    date_limite = now() - pd.Timedelta(days=3)

    # Récupérer les données des capteurs
    ref_data = Ray2.objects.filter(DateRay__gte=date_limite).values("DateRay", "Ray")
    dragino_data = wsd.objects.filter(Time_Stamp__gte=date_limite).values("Time_Stamp", "illumination")

    # Convertir en DataFrame pandas
    ref_df = pd.DataFrame(list(ref_data)).rename(columns={"DateRay": "timestamp", "Ray": "sensecap"})
    dragino_df = pd.DataFrame(list(dragino_data)).rename(columns={"Time_Stamp": "timestamp", "illumination": "dragino"})

    # Vérifier s'il y a assez de données
    if ref_df.empty or dragino_df.empty:
        return JsonResponse({"error": "Pas assez de données sur les 3 derniers jours"}, status=400)

    # Filtrer les valeurs extrêmes (exemple : valeurs supérieures à 2000 W/m² ou nulles)
    ref_df = ref_df[(ref_df["sensecap"] > 0) & (ref_df["sensecap"] < 2000)]
    dragino_df = dragino_df[(dragino_df["dragino"] > 0) & (dragino_df["dragino"] < 2000)]

    # Vérifier si les données sont encore valides après filtrage
    if ref_df.empty or dragino_df.empty:
        return JsonResponse({"error": "Toutes les valeurs valides ont été filtrées"}, status=400)

    # Ajouter une colonne de date uniquement (sans l'heure) pour extraire la valeur maximale par jour
    ref_df["date"] = ref_df["timestamp"].dt.date
    dragino_df["date"] = dragino_df["timestamp"].dt.date

    # Calculer les valeurs maximales par jour
    max_ref = ref_df.groupby("date")["sensecap"].max().reset_index()
    max_dragino = dragino_df.groupby("date")["dragino"].max().reset_index()

    # Fusionner les résultats maximaux des deux capteurs sur la colonne 'date'
    max_df = pd.merge(max_ref, max_dragino, on="date", how="inner")

    # Vérifier si les données maximales existent
    if max_df.empty:
        return JsonResponse({"error": "Pas de données maximales disponibles"}, status=400)

    # Calculer le facteur de calibration pour chaque jour en comparant les valeurs maximales
    max_df["calibration_factor"] = max_df["sensecap"] / max_df["dragino"]

    # Calculer la moyenne du facteur de calibration pour l'ensemble des jours
    avg_calibration_factor = max_df["calibration_factor"].mean()

    # Appliquer l'inverse du facteur de calibration (pour diminuer la valeur de dragino)
    dragino_df["calibrated_dragino"] = dragino_df["dragino"] / avg_calibration_factor

    # Fusionner les données de calibration avec celles de sensecap sur la base de 'date' (et non 'timestamp')
    merged_df = pd.merge(dragino_df, ref_df[["timestamp", "sensecap", "date"]], on="date", how="left")

    # Retourner les résultats en JSON avec les valeurs calibrées et les valeurs de sensecap
    return JsonResponse({
        "calibration_factor": round(avg_calibration_factor, 2),
        "calibrated_values": merged_df[["timestamp", "sensecap", "dragino", "calibrated_dragino"]].to_dict(orient="records")
    })


from .models import PyraRS485

def data_filter_ry_rs485(request):
    start_date_str = request.GET.get('start_date')
    end_date_str   = request.GET.get('end_date')

    # Initialisation des listes
    labels_data2, labels_wsd = [], []
    data_data2, data_wsd = [], []

    if start_date_str and end_date_str:
        # Cas où l'utilisateur filtre manuellement
        start_date = make_aware(datetime.datetime.strptime(start_date_str, "%Y-%m-%d"))
        end_date   = make_aware(datetime.datetime.strptime(end_date_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59))

        all_data2 = Ray2.objects.filter(DateRay__range=(start_date, end_date))
        all_wsd   = wsd.objects.filter(Time_Stamp__range=(start_date, end_date))
        # Pour le RS485 on utilise la même plage filtrée
        rs485_qs  = PyraRS485.objects.filter(DateRay__range=(start_date, end_date)).order_by('DateRay')
    else:
        # Cas par défaut (Affichage automatique)
        today       = datetime.datetime.now()
        # On définit le point de départ à hier 00:00 pour TOUS les capteurs
        one_day_ago = make_aware((today - datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0))
        end_date    = make_aware(today.replace(hour=23, minute=59, second=59))

        all_data2 = Ray2.objects.filter(DateRay__gte=one_day_ago)
        all_wsd   = wsd.objects.filter(Time_Stamp__gte=one_day_ago)
        # ✅ CORRECTION ICI : On utilise one_day_ago au lieu de start_date
        rs485_qs  = PyraRS485.objects.filter(DateRay__gte=one_day_ago).order_by('DateRay')

        # On garde ces variables pour le contexte (affichage des dates dans le template)
        start_date = one_day_ago

    # Remplissage des données Ray2
    for data in all_data2:
        labels_data2.append(data.DateRay.strftime("%Y-%m-%d %H:%M:%S"))
        data_data2.append(data.Ray if data.Ray is not None else 0)

    # Remplissage des données wsd
    for data in all_wsd:
        labels_wsd.append(data.Time_Stamp.strftime("%Y-%m-%d %H:%M:%S"))
        data_wsd.append(data.illumination if data.illumination is not None else 0)

    # Remplissage des données RS485 (Zippage pour le template)
    zipped_rs485 = [
        (entry.DateRay.strftime("%Y-%m-%dT%H:%M:%S"), entry.Irradiance)
        for entry in rs485_qs if entry.Irradiance is not None
    ]

    zipped_data2   = list(zip(labels_data2, data_data2))
    zipped_datawsd = list(zip(labels_wsd, data_wsd))
    last = PyraRS485.objects.order_by('-DateRay').first()

    context = {
        'zipped_data2':   zipped_data2,
        'zipped_datawsd': zipped_datawsd,
        'zipped_rs485':   zipped_rs485,
        'last':           last,
        'start_date':     start_date.strftime("%Y-%m-%d"),
        'end_date':       end_date.strftime("%Y-%m-%d"),
        'data_data2':     data_data2,
        'labels_data2':   labels_data2,
        'data_wsd':       data_wsd,
        'labels_wsd':     labels_wsd,
    }
    return render(request, "enviro/temp3_rs485.html", context)

# import grpc
# from chirpstack_api import api

# def send_downlink(api_token, dev_eui, server, milliseconds=0):
#     """
#     Envoie un message downlink à un périphérique via l'API gRPC de ChirpStack.

#     :param api_token: Le jeton API pour l'authentification.
#     :param dev_eui: L'ID unique du périphérique.
#     :param server: L'adresse du serveur ChirpStack (par défaut '51.38.188.212:8080').
#     :param milliseconds: Le temps en millisecondes à envoyer (sur 6 bits).
#     :return: L'ID de la requête de mise en file d'attente ou une erreur.
#     """
#     try:
#         # Connexion au serveur gRPC sans TLS.
#         channel = grpc.insecure_channel(server)

#         # Client de l'API DeviceService
#         client = api.DeviceServiceStub(channel)

#         # Définir le jeton d'authentification.
#         auth_token = [("authorization", "Bearer %s" % api_token)]

#         # Convertir les millisecondes en hexadécimal sur 6 bits.
#         hex_value = format(int(milliseconds), '06x').upper()  # Conversion en hex avec 6 chiffres

#         # Ajouter '01' au début.
#         final_value = '01' + hex_value  # 01 suivi des millisecondes en hexadécimal

#         # Construire la requête.
#         req = api.EnqueueDeviceQueueItemRequest()
#         req.queue_item.confirmed = False  # Non confirmé
#         req.queue_item.data = bytes.fromhex(final_value)  # Données converties en bytes
#         req.queue_item.dev_eui = dev_eui  # L'ID du périphérique
#         req.queue_item.f_port = 1  # Le port de l'application

#         # Envoi de la requête au serveur ChirpStack.
#         resp = client.Enqueue(req, metadata=auth_token)

#         # Retourner l'ID du downlink
#         return resp.id

#     except grpc.RpcError as e:
#         # Gestion des erreurs gRPC
#         print(f"Erreur lors de l'envoi du downlink: {e}")
#         return None


# Votre jeton API
api_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjaGlycHN0YWNrIiwiaXNzIjoiY2hpcnBzdGFjayIsInN1YiI6IjA4ODBmOWY4LTU5NzktNDNlOC1iNjEyLTE0YmQ3M2YyNmI4NiIsInR5cCI6ImtleSJ9.XKsZDC4EUtsgJctOkJ_e-sQMS7lADDP3ManxNWzyYOo"

# ID du périphérique (dev_eui)
dev_eui = "ce7554dc00001057"
dev_eui_1 ="ab7554dc00001075"
# Adresse du serveur ChirpStack (si différente)
server = "51.38.188.212:8080"





def debit_data(request):

    lasted = debitcap.objects.last()
    irrigation_time = None
    milliseconds = None
    hex_milliseconds = None
    # Appeler la fonction pour envoyer le downlink
    # downlink_id = send_downlink(api_token, dev_eui, server)

    # if downlink_id:
    #     print(f"Downlink envoyé avec succès, ID : {downlink_id}")
    # else:
    #     print("Erreur lors de l'envoi du downlink.")
    if request.method == 'POST':
        action = request.POST.get('action')
        irrigation_time = request.POST.get('irrigation_time')
        milliseconds = request.POST.get('milliseconds')

        if action == 'set_time' and irrigation_time:
            # Traiter l'heure d'irrigation ici
            print(f"Heure d'irrigation : {irrigation_time}")

        if action == 'send_time' and milliseconds:
            # Traiter le temps en ms ici
            print(f"Temps d'irrigation : {milliseconds}")
            hex_value = hex(int(milliseconds))[2:].upper()  # Enlever le '0x' et mettre en majuscule
            print(f"Temps hex_value : {hex_value}")
            # S'assurer que la longueur est de 6 caractères, en ajoutant des zéros à gauche si nécessaire
            hex_value = hex_value.zfill(6)
            print(f"Temps hex_value : {hex_value}")
            # Ajouter '01' au début
            final_value = '01' + hex_value
            print(f"Temps final_value : {final_value}")
            #send_downlink(api_token, dev_eui, server, milliseconds)

        if action == 'on':
            milliseconds_on_off = request.POST.get('milliseconds_on_off')
            print("on relay : ", milliseconds_on_off)
            #send_downlink(api_token, dev_eui_1, server, milliseconds_on_off)
            # Faire quelque chose pour ouvrir avec durée milliseconds_on_off
        if action == 'off':
            milliseconds_on_off = request.POST.get('milliseconds_on_off')
            print("off relay : ",milliseconds_on_off)
            #send_downlink(api_token, dev_eui_1, server, "00")
            # Faire quelque chose pour fermer

        return redirect('debit')  # 👈 rediriger vers la page 'home' pour éviter re-post
    context={'lasted':lasted}

    return render(request,"debitControl.html",context)

############################# Greenhouse ################################
import csv
def export_greenhouse_to_excel(request):
    # Créer la réponse HTTP avec le bon type MIME
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="greenhouse_data.csv"'

    # Création de l’écrivain CSV
    writer = csv.writer(response)

    # Écrire les entêtes
    writer.writerow(['Soil Humidity', 'Rain Drop', 'Rain Drop Sensor State', 'Time Stamp'])

    # Récupérer toutes les données
    data = greenHouse.objects.all().order_by('-Time_Stamp')

    # Écrire les lignes
    for item in data:
        writer.writerow([
            item.Soil_Humidity,
            item.Rain_Drop,
            item.Rain_Drop_Sensor_State,
            item.Time_Stamp.strftime("%Y-%m-%d %H:%M:%S")
        ])

    return response


@csrf_exempt  # utile si tu ne veux pas gérer csrf dans le HTML
def green_house(request):

    lasted = greenHouse.objects.last()
    if request.method == "POST":
        if 'btn_on' in request.POST:
            send_mqtt_command("AQ==")  # Commande ON
        elif 'btn_off' in request.POST:
            send_mqtt_command("AA==")  # Commande OFF
    context={'lasted':lasted}
    return render(request,"greenHousePropagation.html",context)

# Fonction pour envoyer une commande MQTT
def send_mqtt_command(command_base64):
    client = mqtt.Client()
    # client.username_pw_set("mqttuser", "mqttp$$ow")
    client.connect("161.97.107.82", 80)

    topic = "application/41a6740f-8706-49f5-8cdb-e074094b3ee8/device/ab7554dc00001075/command/down"
    payload = f"""{{
        "devEui": "ab7554dc00001075",
        "confirmed": true,
        "fPort": 1,
        "data": "{command_base64}"
    }}"""

    client.publish(topic, payload)
    client.disconnect()
#########################################################################


def check_alerts(sensor_type, data_dict):
    """
    sensor_type : 'pyra', 'sensecap' ou 'lht65n'
    data_dict   : dictionnaire {field_name: valeur}
    """
    rules = AlertRule.objects.filter(sensor=sensor_type, is_active=True)
    for rule in rules:
        value = data_dict.get(rule.field_name)
        if value is None:
            continue
        triggered = (rule.condition == '>' and value > rule.threshold) or \
                    (rule.condition == '<' and value < rule.threshold)
        if triggered:
            Alert.objects.create(rule=rule, value_at_trigger=value)
            print(f"🚨 ALERTE : {rule} | valeur actuelle = {value}")






##########################################################################

# if data['deviceInfo']['devEui']==pyranometre:
                #     time_test = datetime.datetime.now()
                #     hour_minute = time_test.strftime('%H:%M')
                #     print("***************************************pyranometre")
                #     print(hour_minute)
                #     payload_data = data["object"]["bytes"]
                #     xpayload_data = [int(_byte) for _byte in payload_data]
                #     taille_xpayload_data = len(xpayload_data)
                #     print(xpayload_data)
                #     print(taille_xpayload_data)
                #     if taille_xpayload_data == 8:
                #         ray = (xpayload_data[0]*256 + xpayload_data[1])
                #         print(ray)
                #         v_batt = (xpayload_data[2] * 256) + xpayload_data[3]
                #         v_batt = float(v_batt/100)
                #         print(v_batt)
                #         db_obj = Ray()
                #         db_obj.Bat = v_batt
                #         db_obj.Ray = ray
                #         db_obj.save()
                #         print("******* les données du pyra sont bien registées")




                # if (data['deviceInfo']['devEui']== black_device_eui or data['deviceInfo']['devEui']==  red_device_eui):
                #     payload_data= data['object']['bytes']
                #     xpayload_data= [int(_byte) for _byte in payload_data]
                #     taille_xpayload_data = len(xpayload_data)
                #     print(xpayload_data)
                #     print(taille_xpayload_data)
                #     if taille_xpayload_data == 14:
                #         temp = (xpayload_data[0] * 256) + xpayload_data[1]
                #         temp = float(temp/100)

                #         hum = (xpayload_data[2] * 256) + xpayload_data[3]
                #         hum = float(hum/100)

                #         ec = (xpayload_data[4] * 256) + xpayload_data[5]
                #         ec = float(ec)

                #         sal = (xpayload_data[6] * 256) + xpayload_data[7]
                #         sal = float(sal)

                #         v_batt = (xpayload_data[8] * 256) + xpayload_data[9]
                #         v_batt = float(v_batt/100)

                #         deepsleep = (xpayload_data[13] << 24)  + (xpayload_data[12] << 16) + (xpayload_data[11] << 8) + (xpayload_data[10])
                #         print('deepsleep : ', deepsleep)
                #         if data['deviceInfo']['devEui']== black_device_eui:
                #             db_obj= CapSol()
                #             db_obj.devId= 2
                #             db_obj.Temp= temp
                #             db_obj.Hum= hum
                #             db_obj.Ec= ec
                #             db_obj.Sal= sal
                #             db_obj.Bat= v_batt
                #             db_obj.save()
                #         else:
                #             db_obj= CapSol2()
                #             db_obj.devId= 3
                #             db_obj.Temp= temp
                #             db_obj.Hum= hum
                #             db_obj.Ec= ec
                #             db_obj.Sal= sal
                #             db_obj.Bat= v_batt
                #             db_obj.save()
                #     else :
                #         print("ya pas des données????!!!!")
                #         v_batt = (xpayload_data[0] * 256) + xpayload_data[1]
                #         v_batt = float(v_batt/100)
                #         print(v_batt)
                #         deepsleep = (xpayload_data[5] << 24)  + (xpayload_data[4] << 16) + (xpayload_data[3] << 8) + (xpayload_data[2])
                #         print('deepsleep : ', deepsleep)

                # if data['deviceInfo']['devEui']==npk_device_eui:
                #     payload_data= data['object']['bytes']
                #     xpayload_data= [int(_byte) for _byte in payload_data]
                #     taille_xpayload_data = len(xpayload_data)
                #     print(xpayload_data)
                #     print(taille_xpayload_data)
                #     if taille_xpayload_data == 12:
                #         azt = xpayload_data[0]*256 + xpayload_data[1]
                #         azt = float(azt)
                #         pho = xpayload_data[2]*256 + xpayload_data[3]
                #         pho = float(pho)
                #         pot = xpayload_data[4]*256 + xpayload_data[5]
                #         pot = float(pot)
                #         v_batt = xpayload_data[6]*256 + xpayload_data[7]
                #         v_batt = float(v_batt/100)
                #         deepsleep = (xpayload_data[8]) + (xpayload_data[9] << 8) + (xpayload_data[10] << 16) + (xpayload_data[11] << 24)
                #         print(azt)
                #         db_obj= CapNPK()
                #         db_obj.devId=4
                #         db_obj.Azoute= azt
                #         db_obj.Phosphore= pho
                #         db_obj.Potassium= pot
                #         db_obj.Bat= v_batt
                #         db_obj.save()
                #         print("deepsleep : ", deepsleep)
                #     else :
                #         print("ya pas des données????!!!!")
                #         v_batt = (xpayload_data[0] * 256) + xpayload_data[1]
                #         v_batt = float(v_batt/100)
                #         print(v_batt)
                #         deepsleep = (xpayload_data[5] << 24)  + (xpayload_data[4] << 16) + (xpayload_data[3] << 8) + (xpayload_data[2])
                #         print('deepsleep : ', deepsleep)

                # object_wsd = wsd()
                    # object_wsd.wind_direction_angle = data['object']['wind_direction_angle']  # Direction du vent en degrés
                    # print(data['object']['wind_direction_angle'])
                    # object_wsd.wind_direction = data['object']['wind_direction']  # Direction du vent ('E' pour Est)
                    # object_wsd.HUM = data['object']['TEM']  # Humidité
                    # object_wsd.rain_gauge = data['object']['rain_gauge']  # Pluviométrie
                    # object_wsd.wind_speed = data['object']['wind_speed']  # Vitesse du vent
                    # object_wsd.illumination = data['object']['illumination']  # Illumination
                    # object_wsd.TEM = data['object']['HUM']  # Température
                    # object_wsd.pressure = data['object']['pressure']  # Pression
                    # D'autres champs peuvent être affectés de manière similaire

                    # Attribution des valeurs aux champs de l'objet à partir du dictionnaire
                    # object_wsd.wind_direction_angle = wind_direction_angle  # Direction du vent en degrés
                    # object_wsd.wind_direction = wind_direction # Direction du vent (ex: 'E' pour Est)
                    # object_wsd.HUM = TEM  # Humidité
                    # object_wsd.rain_gauge = rain_gauge  # Pluviométrie

                    # object_wsd.wind_speed = wind_speed  # Vitesse du vent
                    # object_wsd.illumination = illumination  # Illumination

                    # object_wsd.TEM = HUM  # Température
                    # object_wsd.save()

                    # Vous pouvez aussi imprimer l'objet pour vérifier
                    # print(object_wsd)
                    # object_wsd.PM2_5 = 0.0  # Particules fines PM2.5
                    # object_wsd.PM10 = 0.0  # Particules fines PM10
                    # object_wsd.TSR = 0.0  # Taux de réflectance solaire (ou autre valeur si vous avez une autre signification)
                    # object_wsd.wind_speed_level = 0.0  # Niveau de la vitesse du vent
                    # object_wsd.pressure = 48.8  # Pression
                    # object_wsd.CO2 = 0.0  # CO2
                    # Sauvegarde de l'objet dans la base de données

                #     payload_data= data['object']['bytes']
                #     xpayload_data= [int(_byte) for _byte in payload_data]
                #     taille_xpayload_data = len(xpayload_data)
                #     print(xpayload_data)
                #     print(taille_xpayload_data)
                #     batt = (xpayload_data[0]*256 + xpayload_data[1])/1000
                #     temp1 = (xpayload_data[3]*256 + xpayload_data[4])/10
                #     hum1 = (xpayload_data[5]*256 + xpayload_data[6])/10
                #     ce1 = xpayload_data[7]*256 + xpayload_data[8]
                #     azt1 = xpayload_data[9]*256 + xpayload_data[10]
                #     pho1 = xpayload_data[11]*256 + xpayload_data[12]
                #     pot1 = xpayload_data[13]*256 + xpayload_data[14]

                #     hum2 = (xpayload_data[15]*256 + xpayload_data[16])/10
                #     temp2 = (xpayload_data[17]*256 + xpayload_data[18])/10
                #     ce2 = xpayload_data[19]*256 + xpayload_data[20]
                #     azt2 = xpayload_data[21]*256 + xpayload_data[22]
                #     pho2 = xpayload_data[23]*256 + xpayload_data[24]
                #     pot2 = xpayload_data[25]*256 + xpayload_data[26]

                #     temp3 = (xpayload_data[27]*256 + xpayload_data[28])/100
                #     hum3 = (xpayload_data[29]*256 + xpayload_data[30])/100
                #     ce3 = xpayload_data[31]*256 + xpayload_data[32]
                #     sal3 = xpayload_data[33]*256 + xpayload_data[34]

                #     azt3 = xpayload_data[35]*256 + xpayload_data[36]
                #     pho3 = xpayload_data[37]*256 + xpayload_data[38]
                #     pot3 = xpayload_data[39]*256 + xpayload_data[40]

                #     db_obj_THSCE= CapSol()
                #     db_obj_THSCE.devId = 2
                #     db_obj_THSCE.Temp = temp3
                #     db_obj_THSCE.Hum = hum3
                #     db_obj_THSCE.Sal = sal3
                #     db_obj_THSCE.EC = ce3
                #     db_obj_THSCE.Bat = batt
                #     db_obj_THSCE.save()

                #     db_obj_NPK = CapNPK()
                #     db_obj_NPK.devId = 4
                #     db_obj_NPK.Azoute = azt3
                #     db_obj_NPK.Phosphore = pho3
                #     db_obj_NPK.Potassium = pot3
                #     db_obj_NPK.Bat = batt
                #     db_obj_NPK.save()

                #     db_obj_THSCEAPh1 = CapTHSCEAPhPo1()
                #     db_obj_THSCEAPh1.Temp = temp1
                #     db_obj_THSCEAPh1.Hum = hum1
                #     db_obj_THSCEAPh1.CE = ce1
                #     db_obj_THSCEAPh1.Azoute = azt1
                #     db_obj_THSCEAPh1.Phosphore = pho1
                #     db_obj_THSCEAPh1.Potassium = pot1
                #     db_obj_THSCEAPh1.Bat = batt
                #     db_obj_THSCEAPh1.save()

                #     db_obj_THSCEAPh = CapTHSCEAPhPo()
                #     db_obj_THSCEAPh.Temp = temp2
                #     db_obj_THSCEAPh.Hum = hum2
                #     db_obj_THSCEAPh.CE = ce2
                #     db_obj_THSCEAPh.Azoute = azt2
                #     db_obj_THSCEAPh.Phosphore = pho2
                #     db_obj_THSCEAPh.Potassium = pot2
                #     db_obj_THSCEAPh.Bat = batt
                #     db_obj_THSCEAPh.save()

                # if data['deviceInfo']['devEui'] == 'a84041b02458e028':
                #     messages = data['object']['messages']
                #     print("messages WEATHER STATION : ", messages)

 # {'wind_direction_angle': 201.2, 'wind_direction': 'E', 'HUM': 16.7, 'rain_gauge': 51.2,
    # 'CO2': 0.0, 'wind_speed': 0.0, 'illumination': 0.0, 'wind_speed_level': 0.0, 'pressure': 48.8, 'TEM': 57.2, 'PM2_5': 0.0, 'PM10': 0.0, 'TSR': 0.0}
                    # Attribution des valeurs aux champs de l'objet
                    # Instanciation de l'objet wsd
                    # object_wsd = wsd(
                    #     wind_direction_angle=201.2,
                    #     wind_direction='E',
                    #     HUM=16.7,
                    #     rain_gauge=51.2,
                    #     wind_speed=5.0,
                    #     illumination=10.0,
                    #     TEM=22.5
                    #     # pressure=1013.0
                    # )
                    # object_wsd.save()
                    # object_wsd.pressure = object_data.get('pressure', None)
                    # object_wsd.CO2 = object_data.get('CO2', None)
                    # object_wsd.wind_speed_level = object_data.get('wind_speed_level', None)
                    # object_wsd.TSR = object_data.get('TSR', None)
                    # object_wsd.PM2_5 = object_data.get('PM2_5', None)
                    # object_wsd.PM10 = object_data.get('PM10', None)

        # bv= batvanne.objects.last()
    # # print("last",str((tab.time)))

    # f = CapSol.objects.first()
    # tab2=CapSol.objects.all()

    # max_temp=CapSol.objects.all().aggregate(Max('Temp'))
    # min_temp = CapSol.objects.all().aggregate(Min('Temp'))
    # moy=(max_temp["Temp__max"]+min_temp["Temp__min"])/2
    # print((max_temp["Temp__max"]+min_temp["Temp__min"])/2)

    # context = {'tab': tab,'tab2':tab2,'max_temp':max_temp,'min_temp':min_temp,'moy':moy,'f':f,'cap1_last_data':cap1_last_data,'cap2_last_data':cap2_last_data,
    # 'cap3_last_data':cap3_last_data, 'cap4_last_data':cap4_last_data}

    # #tab2 = CapSol.objects.last().filter(devId='03')
    # if (request.method == "POST"):
    #     if (request.POST.get('btn1', False)) == 'two':
    #         new_value_button = vann(onoff=request.POST.get(
    #             'btn1'))
    #         print(request.POST.get('btn1', False))
    #         new_value_button.save()
    #         x=vann.objects.create(onoff=False)
    #         print("x :", x)
    #         return HttpResponseRedirect('/')

    #     if (request.POST.get('btn', True)) == 'two':
    #         new_value_button1 = vann(onoff=request.POST.get(
    #             'btn'))
    #         print(request.POST.get('btn', True))
    #         new_value_button1.save()

    #         w=vann.objects.create(onoff=True)
    #         print("w :", w)
    #         return HttpResponseRedirect('/')

    #     elif request.POST.get('startdate') == 'one':
    #         fromdate = request.POST.get('startdate')
    #         # print(type(datetime.datetime.now()))
    #         print("fromdate")
    #         print(fromdate)
    #         client1 = mqtt.Client()

    #         client1.connect("broker.hivemq.com", 1883, 80)
    #         client1.publish("time", str(fromdate))

    #         return HttpResponseRedirect('/')

    # # if (request.method == "POST"):
    # #     fromdate = request.POST.get('startdate')
    # #     # print(type(datetime.datetime.now()))
    # #     print("fromdate" , fromdate)

    # date_from = datetime.datetime.now() - datetime.timedelta(days=1)
    # date_from2 = datetime.datetime.now() - datetime.timedelta(days=7)
    # date_from3 = datetime.datetime.now() - datetime.timedelta(days=14)
    # date_from4 = datetime.datetime.now() - datetime.timedelta(days=30)
    # created_documents = CapSol.objects.filter(dt__gte=date_from)

    # created_documents2 = CapSol.objects.filter(dt__gte=date_from2).count()
    # created_documents3 = CapSol.objects.filter(dt__gte=date_from3).count()
    # created_documents4 = CapSol.objects.filter(dt__gte=date_from4).count()

    # now = (datetime.datetime.now()).strftime("%M")
    # x = CapSol.objects.filter(time__minute=now).count()
    # # print("x", str(x))
    # labels = []
    # dataa = []
    # dataa2 = []
    # alla = CapSol.objects.all()
    # for data in alla:
    #     labels.append((data.dt).strftime("%d %b %Y %H:%M:%S"))
    #     dataa.append(data.Temp)
    #     dataa2.append(data.Hum)
    #     # print("labels0",labels)

    # # print("labelall",labels)
    # if (request.method == "POST"):
    #     labels.clear()
    #     dataa.clear()
    #     dataa2.clear()

    #     fromdate = request.POST.get('startdate')
    #     # print(type(datetime.datetime.now()))
    #     print("fromdate")
    #     print(fromdate)

from .models import SensorData

@csrf_exempt
def gprs_receive(request):
    if request.method == 'GET':
        try:
            raw_temp = request.GET.get('temp')
            raw_hum  = request.GET.get('hum')

            if raw_temp is None or raw_hum is None:
                return JsonResponse({'status': 'error', 'msg': 'Missing parameters'}, status=400)

            temperature = int(raw_temp) / 10.0
            humidity    = int(raw_hum)  / 10.0

            SensorData.objects.create(
                temperature = temperature,
                humidity    = humidity,
            )

            return JsonResponse({
                'status'     : 'ok',
                'temperature': temperature,
                'humidity'   : humidity
            })

        except Exception as e:
            return JsonResponse({'status': 'error', 'msg': str(e)}, status=500)

    return JsonResponse({'status': 'method not allowed'}, status=405)


def comparaison(request):
    from django.db.models import Avg, Max, Min, Sum
    import json, datetime
    from django.utils import timezone as tz

    since = tz.now() - datetime.timedelta(hours=24)

    sc = Data2.objects.order_by('-Time_Stamp').first()
    dv = Data3.objects.order_by('-Time_Stamp').first()

    sc_agg = Data2.objects.aggregate(
        T_avg=Avg('Temp'), T_max=Max('Temp'), T_min=Min('Temp'),
        H_avg=Avg('Hum'),  H_max=Max('Hum'),  H_min=Min('Hum'),
        W_avg=Avg('Wind_Speed'), W_max=Max('Wind_Speed'), W_min=Min('Wind_Speed'),
        R_sum=Sum('Rain'),
    )
    dv_agg = Data3.objects.aggregate(
        T_avg=Avg('temperature_c'), T_max=Max('temperature_c'), T_min=Min('temperature_c'),
        H_avg=Avg('humidity_pct'),  H_max=Max('humidity_pct'),  H_min=Min('humidity_pct'),
        W_avg=Avg('wind_speed_kmh'), W_max=Max('wind_speed_kmh'), W_min=Min('wind_speed_kmh'),
        R_sum=Sum('rain_mm'),
    )

    def fmt(qs, time_field):
        return [{**r, time_field: r[time_field].strftime('%Y-%m-%dT%H:%M:%S')} for r in qs]

    sc_series = json.dumps(fmt(list(
        Data2.objects.filter(Time_Stamp__gte=since).order_by('Time_Stamp')
        .values('Time_Stamp', 'Temp', 'Hum', 'Wind_Speed', 'Rain')
    ), 'Time_Stamp'))

    dv_series = json.dumps(fmt(list(
        Data3.objects.filter(Time_Stamp__gte=since).order_by('Time_Stamp')
        .values('Time_Stamp', 'temperature_c', 'humidity_pct', 'wind_speed_kmh', 'rain_mm')
    ), 'Time_Stamp'))

    return render(request, 'comparaison.html', {
        'sc': sc, 'dv': dv,
        'sc_agg': sc_agg, 'dv_agg': dv_agg,
        'sc_series': sc_series, 'dv_series': dv_series,
    })


@require_POST
@csrf_exempt
def davis_uplink(request):
    try:
        data = json.loads(request.body)
        obj = data.get('object', {})
        record = Data3()
        record.devEui        = data.get('devEui', '70b3d58f8000062d')
        record.temperature_c = obj.get('temperature_c')
        record.humidity_pct  = obj.get('humidity_pct')
        record.wind_speed_ms = obj.get('wind_speed_ms')
        record.wind_speed_kmh= obj.get('wind_speed_kmh')
        record.wind_dir_deg  = obj.get('wind_dir_deg')
        record.wind_dir_card = obj.get('wind_dir_card')
        record.rain_mm       = obj.get('rain_mm')
        record.movement      = obj.get('movement', False)
        rx_info = data.get('rxInfo', [{}])
        if rx_info:
            record.rssi = rx_info[0].get('rssi')
            record.snr  = rx_info[0].get('snr')
        record.save()
        return JsonResponse({'status': 'ok davis'}, status=201)
    except Exception as e:
        return JsonResponse({'status': 'error', 'detail': str(e)}, status=400)



from django.utils import timezone
from datetime import timedelta

def device_status(request):
    from django.db import connection
    now = timezone.now()

    def get_status(last_seen, threshold_minutes):
        if not last_seen:
            return 'unknown'
        delta = now - last_seen
        if delta < timedelta(minutes=threshold_minutes):
            return 'online'
        elif delta < timedelta(minutes=threshold_minutes * 2):
            return 'warning'
        else:
            return 'offline'

    # Toutes les requêtes groupées — une seule par modèle
    last = {
        'davis':     Data3.objects.only('Time_Stamp').order_by('-Time_Stamp').first(),
        'sensecap':  Data2.objects.only('Time_Stamp').order_by('-Time_Stamp').first(),
        'capsol':    CapSol2.objects.only('dt').order_by('-dt').first(),
        'lht65':     DeviceData.objects.only('timestamp').filter(device_name='LHT2_Frigo').order_by('-timestamp').first(),
        'pyragv':    Ray2.objects.only('DateRay').order_by('-DateRay').first(),
        'pyrars485': PyraRS485.objects.only('DateRay').order_by('-DateRay').first(),
        'wsc1l':     wsd.objects.only('Time_Stamp').order_by('-Time_Stamp').first(),
        'makerfabs': Makerfabs.objects.only('Time_Stamp').order_by('-Time_Stamp').first(),
        'ev1':       ev_batt.objects.only('Time_Stamp').order_by('-Time_Stamp').first(),
        'ev2':       ev_batt2.objects.only('Time_Stamp').order_by('-Time_Stamp').first(),
        'ev3':       ev_batt3.objects.only('Time_Stamp').order_by('-Time_Stamp').first(),
        'senscapt':  SenseCAPT1000.objects.only('Time_Stamp').order_by('-Time_Stamp').first(),
        'debit':     debitcap.objects.only('Time_Stamp').order_by('-Time_Stamp').first(),
    }

    devices = [
        {'name': 'Station Davis',           'eui': '70b3d58f8000062d', 'type': 'LoRaWAN', 'last_seen': getattr(last['davis'],     'Time_Stamp', None), 'threshold': 15},
        {'name': 'SenseCAP Weather Station','eui': '2cf7f1c064900b68', 'type': 'LoRaWAN', 'last_seen': getattr(last['sensecap'],  'Time_Stamp', None), 'threshold': 15},
        {'name': 'Capteur de sol (Dragino)','eui': 'a84041d10858e027', 'type': 'LoRaWAN', 'last_seen': getattr(last['capsol'],    'dt',         None), 'threshold': 30},
        {'name': 'LHT65N',                  'eui': 'a8404153d188114e', 'type': 'LoRaWAN', 'last_seen': getattr(last['lht65'],     'timestamp',  None), 'threshold': 20},
        {'name': 'PyraGV (Pyranomètre)',    'eui': 'a84041fc4188657b', 'type': 'LoRaWAN', 'last_seen': getattr(last['pyragv'],    'DateRay',    None), 'threshold': 15},
        {'name': 'PyraRS485',               'eui': '0100000044000000', 'type': 'LoRaWAN', 'last_seen': getattr(last['pyrars485'], 'DateRay',    None), 'threshold': 15},
        {'name': 'Station WSC1-L (Dragino)','eui': 'a84041b02458e028', 'type': 'LoRaWAN', 'last_seen': getattr(last['wsc1l'],     'Time_Stamp', None), 'threshold': 15},
        {'name': 'Makerfabs (Vanne)',        'eui': '48e663fffe300aed', 'type': 'LoRaWAN', 'last_seen': getattr(last['makerfabs'], 'Time_Stamp', None), 'threshold': 120},
        {'name': 'Electrovanne EV1',         'eui': 'ce7554dc00001057', 'type': 'LoRaWAN', 'last_seen': getattr(last['ev1'],       'Time_Stamp', None), 'threshold': 60},
        {'name': 'Electrovanne EV2',         'eui': '2e3554dc00001057', 'type': 'LoRaWAN', 'last_seen': getattr(last['ev2'],       'Time_Stamp', None), 'threshold': 60},
        {'name': 'Electrovanne EV3',         'eui': '1e4554dc00001057', 'type': 'LoRaWAN', 'last_seen': getattr(last['ev3'],       'Time_Stamp', None), 'threshold': 60},
        {'name': 'SenseCAP T1000-A',         'eui': '2cf7f1c064900b68', 'type': 'LoRaWAN', 'last_seen': getattr(last['senscapt'],  'Time_Stamp', None), 'threshold': 60},
        {'name': 'Débitmètre SW3L',          'eui': 'a84041685458e15b', 'type': 'LoRaWAN', 'last_seen': getattr(last['debit'],     'Time_Stamp', None), 'threshold': 60},
    ]

    for d in devices:
        d['status'] = get_status(d['last_seen'], d['threshold'])
        d['last_seen_str'] = d['last_seen'].strftime('%Y-%m-%d %H:%M:%S') if d['last_seen'] else 'Jamais'

    summary = {
        'online':  sum(1 for d in devices if d['status'] == 'online'),
        'warning': sum(1 for d in devices if d['status'] == 'warning'),
        'offline': sum(1 for d in devices if d['status'] == 'offline'),
        'unknown': sum(1 for d in devices if d['status'] == 'unknown'),
        'total':   len(devices),
    }

    return render(request, 'device_status.html', {'devices': devices, 'summary': summary})