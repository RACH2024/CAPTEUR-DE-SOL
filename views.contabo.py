# Create your views here.
import datetime
import math
from django.utils.timezone import localtime
import numpy as np
import pandas as pd
from django.utils import timezone
from django.db.models import Max, Min, Sum, Avg
from django.http import HttpResponseRedirect
from django.shortcuts import render,HttpResponse, redirect
from django.views.generic import TemplateView
#import paho.mqtt.client as mqtt
from collections import defaultdict
from django.utils.timezone import make_aware
from .models import *
import requests
import json
import paho.mqtt.publish as publish
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

import base64
import requests

import grpc
from chirpstack_api import api
api_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjaGlycHN0YWNrIiwiaXNzIjoiY2hpcnBzdGFjayIsInN1YiI6IjQ2NzYxZTliLWUwZjktNDQ3NC04NjZkLTY2Yjc3MTAzMzc4NiIsInR5cCI6ImtleSJ9.o4HH0KhQk6IcGxvtK4RQjDwDeMAYhsSgGNH3DXnZ8QY"
# ID du périphérique (dev_eui)
dev_eui = "ce7554dc00001057"

# Adresse du serveur ChirpStack (si différente)
server = "161.97.107.82:8080"
def send_downlink_1(api_token, dev_eui, server, etat=1):
    """
    Envoie un message ON (0x01) ou OFF (0x00) via l'API gRPC de ChirpStack.

    :param api_token: Jeton API pour l'authentification.
    :param dev_eui: DevEUI du périphérique.
    :param server: Adresse du serveur ChirpStack.
    :param etat: 1 pour ON (0x01), 0 pour OFF (0x00).
    :return: ID du message envoyé ou None en cas d'erreur.
    """
    try:
        # Connexion gRPC
        channel = grpc.insecure_channel(server)
        client = api.DeviceServiceStub(channel)
        auth_token = [("authorization", f"Bearer {api_token}")]

        # Construction du message
        req = api.EnqueueDeviceQueueItemRequest()
        req.queue_item.confirmed = False
        req.queue_item.dev_eui = dev_eui
        req.queue_item.f_port = 10
        req.queue_item.data = bytes([0x01]) if etat else bytes([0x00])

        # Envoi
        resp = client.Enqueue(req, metadata=auth_token)
        return resp.id

    except grpc.RpcError as e:
        print(f"Erreur lors de l'envoi du downlink: {e}")
        return None

def send_downlink(api_token, dev_eui="ce7554dc00001057", server="161.97.107.82:8080", milliseconds=0):
    """
    Envoie un message downlink à un périphérique via l'API gRPC de ChirpStack.

    :param api_token: Le jeton API pour l'authentification.
    :param dev_eui: L'ID unique du périphérique.
    :param server: L'adresse du serveur ChirpStack (par défaut '51.38.188.212:8080').
    :param milliseconds: Le temps en millisecondes à envoyer (sur 6 bits).
    :return: L'ID de la requête de mise en file d'attente ou une erreur.
    """
    try:
        # Connexion au serveur gRPC sans TLS.
        channel = grpc.insecure_channel(server)

        # Client de l'API DeviceService
        client = api.DeviceServiceStub(channel)

        # Définir le jeton d'authentification.
        auth_token = [("authorization", "Bearer %s" % api_token)]

        # Convertir les millisecondes en hexadécimal sur 6 bits.
        hex_value = format(int(milliseconds), '06x').upper()  # Conversion en hex avec 6 chiffres

        # Ajouter '01' au début.
        final_value = '01' + hex_value  # 01 suivi des millisecondes en hexadécimal

        # Construire la requête.
        req = api.EnqueueDeviceQueueItemRequest()
        req.queue_item.confirmed = False  # Non confirmé
        req.queue_item.data = bytes.fromhex(final_value)  # Données converties en bytes
        req.queue_item.dev_eui = dev_eui  # L'ID du périphérique
        req.queue_item.f_port = 1  # Le port de l'application

        # Envoi de la requête au serveur ChirpStack.
        resp = client.Enqueue(req, metadata=auth_token)

        # Retourner l'ID du downlink
        return resp.id

    except grpc.RpcError as e:
        # Gestion des erreurs gRPC
        print(f"Erreur lors de l'envoi du downlink: {e}")
        return None
import pytz

from django.db.models.functions import TruncHour
import pytz
import subprocess

from django.contrib import messages

@csrf_exempt
def green_house(request):
    lasted = greenHouse.objects.last()
    context={'lasted':lasted}
    if request.method == 'POST':
        action = request.POST.get('action')  # 'ouvrir' ou 'fermer'
        data = "AQ==" if action == "ouvrir" else "AA=="

        topic = "application/6f065213-3091-483b-a8a0-7a8adb9e442e/device/f29ea90aba287401/command/down"

        message = {
            "devEui": "f29ea90aba287401",
            "confirmed": True,
            "fPort": 1,
            "data": data
        }

        try:
            publish.single(
                topic,
                payload=json.dumps(message),
                hostname="mosquitto",   # 🔁 Docker: nom du service
                port=1883
            )
            messages.success(request, f"Commande '{action}' envoyée avec succès.")
        except Exception as e:
            messages.error(request, f"Erreur d'envoi MQTT : {e}")

        return redirect('greenhouse')

    return render(request, 'greenHousePropagation.html',context)

def fetch_data_for_etoDR():
    start_of_yesterday = (timezone.now() - timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    start_of_today = start_of_yesterday + timedelta(days=1)

    qs_wsd = wsd.objects.filter(Time_Stamp__range=(start_of_yesterday, start_of_today))

    if not qs_wsd.exists():
        logger.warning("Aucune donnée WSD pour la journée → ET0 impossible")
        return None

    weather_data = qs_wsd.aggregate(
        temp_avg=Avg('TEM'),
        temp_min=Min('TEM'),
        temp_max=Max('TEM'),
        humidity_min=Min('HUM'),
        humidity_max=Max('HUM'),
        wind_avg=Avg('wind_speed'),
    )

    weather_data1 = Data2.objects.filter(
        Time_Stamp__range=(start_of_yesterday, start_of_today)
    ).aggregate(pressure=Avg('Pr'))

    if weather_data1['pressure'] is None:
        logger.warning("Pression manquante → ET0 impossible")
        return None

    # Illumination horaire
    hourly_illum = []
    for hour in range(24):
        interval_start = start_of_yesterday + timedelta(hours=hour)
        interval_end = interval_start + timedelta(hours=1)

        val = qs_wsd.filter(
            Time_Stamp__range=(interval_start, interval_end)
        ).aggregate(avg=Avg('illumination'))['avg']

        if val is not None:
            hourly_illum.append(val)

    if not hourly_illum:
        logger.warning("Radiation manquante → ET0 impossible")
        return None

    radiation_sum = sum(hourly_illum)

    wind_speed_avg = (
        round(weather_data['wind_avg'] / 3.6, 2)
        if weather_data['wind_avg'] is not None
        else None
    )

    day_of_year = start_of_yesterday.timetuple().tm_yday

    return {
        'altitude': 532,
        'latitude': 33.51,
        'day_of_year': day_of_year,
        'pressure': weather_data1['pressure'],
        'humidity_max': weather_data['humidity_max'],
        'humidity_min': weather_data['humidity_min'],
        'temp_avg': weather_data['temp_avg'],
        'temp_max': weather_data['temp_max'],
        'temp_min': weather_data['temp_min'],
        'radiation_sum': radiation_sum,
        'wind_speed_avg': wind_speed_avg,
    }
def ETODRv():
    data = fetch_data_for_etoDRv()
    A6 = data['altitude']  # Altitude (m)
    B6 = data['latitude']  # Latitude (degrés)
    C6 = 2  # Hauteur de l'anémomètre (m)
    D11 = data['day_of_year']  # Jour de l'année
    E6 = data['pressure']  # Pression moyenne (hPa)
    F11 = data['humidity_max']  # Humidité max (%)
    G11 = data['humidity_min']  # Humidité min (%)
    H11 = data['temp_avg']  # Température moyenne (°C)
    I11 = data['temp_max']  # Température max (°C)
    J11 = data['temp_min']  # Température min (°C)
    K11 = data['radiation_sum']  # Radiation solaire (MJ/m²)
    L11 = data['wind_speed_avg']  # Vitesse moyenne du vent (m/s)

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

    # Résultats
    print(f"ETo: {ETo} mm/jour")

    # Enregistrement dans la base de données
    ET0DRv.objects.create(
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

    # Préparation des données pour le graphique
    def extract_data(queryset):
        labels = [entry.Time_Stamp.strftime("%Y-%m-%d %H:%M:%S") for entry in queryset]
        values = [entry.value if entry.value is not None else 0 for entry in queryset]
        return list(zip(labels, values))

    zipped_dr = extract_data(data_dr)
    zipped_drv = extract_data(data_drv)
    zipped_o = extract_data(data_o)

    # Derniers paramètres
    latest_dr = ET0DR.objects.order_by('-Time_Stamp').first()
    latest_drv = ET0DRv.objects.order_by('-Time_Stamp').first()
    latest_o = ET0o.objects.order_by('-Time_Stamp').first()
    latest_models = {
        "ET0_Dragino": {
            "obj": latest_dr,
            "raym_converted": latest_dr.Raym /24 if latest_dr and latest_dr.Raym else None,
            "raym": latest_dr.Raym,
        },
        "ET0_Dragino_irraVisioGrenn": {
            "obj": latest_drv,
            "raym_converted": latest_drv.Raym / 24 if latest_drv and latest_drv.Raym else None,
            "raym": latest_drv.Raym,
        },
        "ET0_SenseCap": {
            "obj": latest_o,
            "raym_converted": latest_o.Raym / 24 if latest_o and latest_o.Raym else None,
            "raym": latest_o.Raym,
        }
    }
    context = {
        'zipped_dr': zipped_dr,
        'zipped_drv': zipped_drv,
        'zipped_o': zipped_o,
        'latest_dr': latest_dr,
        'latest_drv': latest_drv,
        'latest_o': latest_o,
        'start_date': start_date.strftime("%Y-%m-%d"),
        'end_date': end_date.strftime("%Y-%m-%d"),
        'models_info': [
        (latest_dr, "ET0_Dragino"),
        (latest_drv, "ET0_Dragino_irraVisioGreen"),
        (latest_o, "ET0_SenseCap"),
    ],
    'latest_models': latest_models,
    }

    return render(request, 'et0_graph.html', context)
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


def aqi(request):
    context={}
    return render(request,"tab.html",context)


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

    def main():
        one_day_ago = datetime.datetime.now() - datetime.timedelta(days=1)
        posts = Ws.objects.filter(date__gte=one_day_ago)
        print("posts :", posts)
        # vent calcul
        totalVent = posts.values('Vent').aggregate(Sum('Vent'))
        nbrVent = posts.values('Vent').count()
        wind = round((totalVent["Vent__sum"] / nbrVent), 2)
        print("totalevent : ", totalVent, nbrVent, wind)
        # temperature calcul
        Maxtemp = posts.values('Temperature').aggregate(Max('Temperature'))
        Mintemp = posts.values('Temperature').aggregate(Min('Temperature'))
        temp = (Maxtemp["Temperature__max"] + Mintemp["Temperature__min"]) / 2
        print("moyTemp :", moyTemp)
        # humiidity calcul
        MaxHum = posts.values('Humidity').aggregate(Max('Humidity'))
        MinHum = posts.values('Humidity').aggregate(Min('Humidity'))
        rhum = (MaxHum["Humidity__max"] + MinHum["Humidity__min"]) / 2
        print("moyHum : ", rhum)
        if rhum > 100.0:
            rhum = 100.0
        # pluie calcul
        totalrain = posts.values('Pluv').aggregate(Sum('Pluv'))
        nmbrRain = posts.values('Pluv').count()
        prcp = totalrain['Pluv__sum'] / nmbrRain
        print("moyRain :", prcp)
        initfw = DataFwi.objects.filter(timestamp__date=one_day_ago)
        ffmc0 = initfw.ffmc
        print("ffmc0 :",ffmc0)
        dmc0 = initfw.dmc
        print("dmc0 :", dmc0)
        dc0 = initfw.dc
        print("dc0 :", dc0)
        mth = datetime.datetime.today().month
        print(mth)#4
        fwisystem = FWICLASS(temp, rhum, wind, prcp)
        ffmc = fwisystem.FFMCcalc(ffmc0)
        dmc = fwisystem.DMCcalc(dmc0, mth)
        dc = fwisystem.DCcalc(dc0, mth)
        isi = fwisystem.ISIcalc(ffmc)
        bui = fwisystem.BUIcalc(dmc, dc)
        fwi = fwisystem.FWIcalc(isi, bui)
        DataFwi.objects.create(ffmc=round(ffmc,1), dmc=round(dmc,1), dc=round(dc,1), isi=round(isi,1), bui=round(bui,1), fwi=round(fwi,2))

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


def home(request):
    # print("date",str((datetime.datetime.now())))
    # print("date2", str((datetime.datetime.now()).strftime("%M")))
    tab=CapSol.objects.last()
    cap1_last_data = CapSol2.objects.filter(devId="1").latest('dt')
    cap2_last_data = CapSol2.objects.filter(devId="2").latest('dt')
    cap3_last_data = CapSol2.objects.filter(devId="3").latest('dt')
    cap4_last_data = CapSol2.objects.filter(devId="4").latest('dt')
    cap2 = CapSol2.objects.last()
    #****************cmd vanne *********
    # Votre jeton API
    api_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjaGlycHN0YWNrIiwiaXNzIjoiY2hpcnBzdGFjayIsInN1YiI6IjA4ODBmOWY4LTU5NzktNDNlOC1iNjEyLTE0YmQ3M2YyNmI4NiIsInR5cCI6ImtleSJ9.XKsZDC4EUtsgJctOkJ_e-sQMS7lADDP3ManxNWzyYOo"

# ID du périphérique (dev_eui)
    dev_eui = "ce7554dc00001057"

# Adresse du serveur ChirpStack (si différente)
    server = "51.38.188.212:8080"

# Appeler la fonction pour envoyer le downlink
    #downlink_id = send_downlink(api_token, dev_eui, server)

    #if downlink_id:
    #    print(f"Downlink envoyé avec succès, ID : {downlink_id}")
    #else:
    #    print("Erreur lors de l'envoi du downlink.")

    #***************fin cmd ************
    bv= batvanne.objects.last()
    # print("last",str((tab.time)))

    f = CapSol.objects.first()
    tab2=CapSol.objects.all()
#    send_downlink_to_node()
    max_temp=CapSol.objects.all().aggregate(Max('Temp'))
    min_temp = CapSol.objects.all().aggregate(Min('Temp'))
    moy=(max_temp["Temp__max"]+min_temp["Temp__min"])/2
    print((max_temp["Temp__max"]+min_temp["Temp__min"])/2)

    context = {'tab': tab,'tab2':tab2,'max_temp':max_temp,'min_temp':min_temp,'moy':moy,'f':f,'cap1_last_data':cap1_last_data,'cap2_last_data':cap2_last_data,
    'cap3_last_data':cap3_last_data, 'cap4_last_data':cap4_last_data}

    #tab2 = CapSol.objects.last().filter(devId='03')
    if (request.method == "POST"):
        if (request.POST.get('btn1', False)) == 'two':
            new_value_button = vann(onoff=request.POST.get(
                'btn1'))
            print(request.POST.get('btn1', False))
            new_value_button.save()
            x=vann.objects.create(onoff=False)
            print("x :", x)
            return HttpResponseRedirect('/')

        if (request.POST.get('btn', True)) == 'two':
            new_value_button1 = vann(onoff=request.POST.get(
                'btn'))
            print(request.POST.get('btn', True))
            new_value_button1.save()

            w=vann.objects.create(onoff=True)
            print("w :", w)
            return HttpResponseRedirect('/')

        elif request.POST.get('startdate') == 'one':
            fromdate = request.POST.get('startdate')
            # print(type(datetime.datetime.now()))
            print("fromdate")
            print(fromdate)
            client1 = mqtt.Client()

            client1.connect("broker.hivemq.com", 1883, 80)
            client1.publish("time", str(fromdate))

            return HttpResponseRedirect('/')

    # if (request.method == "POST"):
    #     fromdate = request.POST.get('startdate')
    #     # print(type(datetime.datetime.now()))
    #     print("fromdate" , fromdate)

    date_from = datetime.datetime.now() - datetime.timedelta(days=1)
    date_from2 = datetime.datetime.now() - datetime.timedelta(days=7)
    date_from3 = datetime.datetime.now() - datetime.timedelta(days=14)
    date_from4 = datetime.datetime.now() - datetime.timedelta(days=30)
    created_documents = CapSol.objects.filter(dt__gte=date_from)

    created_documents2 = CapSol.objects.filter(dt__gte=date_from2).count()
    created_documents3 = CapSol.objects.filter(dt__gte=date_from3).count()
    created_documents4 = CapSol.objects.filter(dt__gte=date_from4).count()

    now = (datetime.datetime.now()).strftime("%M")
    x = CapSol.objects.filter(time__minute=now).count()
    # print("x", str(x))
    labels = []
    dataa = []
    dataa2 = []
    alla = CapSol.objects.all()
    for data in alla:
        labels.append((data.dt).strftime("%d %b %Y %H:%M:%S"))
        dataa.append(data.Temp)
        dataa2.append(data.Hum)
        # print("labels0",labels)

    # print("labelall",labels)
    if (request.method == "POST"):
        labels.clear()
        dataa.clear()
        dataa2.clear()

        fromdate = request.POST.get('startdate')
        # print(type(datetime.datetime.now()))
        print("fromdate")
        print(fromdate)

    context = {'tab': tab,'tab2':tab2,'max_temp':max_temp,'min_temp':min_temp,'moy':moy,'f':f,'labels':labels,'dataa':dataa,'dataa2':dataa2,'cap2':cap2, 'bv':bv,'cap1_last_data':cap1_last_data,'cap2_last_data':cap2_last_data,
    'cap3_last_data':cap3_last_data, 'cap4_last_data':cap4_last_data}
    return render(request, "index.html", context)


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
    for dev_id in [1, 2, 3, 4]:
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

    # completed = request.POST('checks')
    # print(completed)
    # if 'checks' in request.GET:

    # toSave = vanne.objects.all()
    # geek_object = vanne.objects.create(onoff=True)
    # geek_object.save()
    # toSave.save()
    # print(toSave)
def fetch_data_for_eto():
    # Période de données : hier de 00:00 à aujourd’hui 00:00
    start_of_yesterday = (timezone.now() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_today = start_of_yesterday + timedelta(days=1)

    # Moyennes des autres paramètres (hors Ray)
    weather_data = Data2.objects.filter(Time_Stamp__range=(start_of_yesterday, start_of_today)).aggregate(
        Avg('Temp'),
        Avg('Hum'),
        Avg('Wind_Speed'),
        Avg('Pr')
    )

    # Min/max température et humidité
    temp_max = Data2.objects.filter(Time_Stamp__range=(start_of_yesterday, start_of_today)).order_by('-Temp').first().Temp
    temp_min = Data2.objects.filter(Time_Stamp__range=(start_of_yesterday, start_of_today)).order_by('Temp').first().Temp
    hum_max = Data2.objects.filter(Time_Stamp__range=(start_of_yesterday, start_of_today)).order_by('-Hum').first().Hum
    hum_min = Data2.objects.filter(Time_Stamp__range=(start_of_yesterday, start_of_today)).order_by('Hum').first().Hum

    temp_avg = weather_data['Temp__avg']
    wind_speed_avg = round(weather_data['Wind_Speed__avg'] / 3.6, 2) if weather_data['Wind_Speed__avg'] else 0

    # Moyenne horaire de Ray (24 intervalles horaires)
    hourly_ray_averages = []
    for hour in range(24):
        interval_start = start_of_yesterday + timedelta(hours=hour)
        interval_end = interval_start + timedelta(hours=1)
        avg_ray = Ray2.objects.filter(DateRay__range=(interval_start, interval_end)).aggregate(avg=Avg('Ray'))['avg']
        if avg_ray is not None:
            hourly_ray_averages.append(avg_ray)

    # Moyenne journalière sur les 24 heures
    if hourly_ray_averages:
        daily_ray_avg = sum(hourly_ray_averages)
    else:
        daily_ray_avg = 0

    # Conversion en MJ/m²
    radiation_sum = daily_ray_avg

    # Numéro du jour dans l’année (pour hier)
    day_of_year = start_of_yesterday.timetuple().tm_yday

    return {
        'altitude': 532,
        'latitude': 33.51,
        'day_of_year': day_of_year,
        'pressure': weather_data['Pr__avg'],
        'humidity_max': hum_max,
        'humidity_min': hum_min,
        'temp_avg': temp_avg,
        'temp_max': temp_max,
        'temp_min': temp_min,
        'radiation_sum': radiation_sum,
        'wind_speed_avg': wind_speed_avg
    }

def fetch_data_for_etoDR():
    start_of_yesterday = (timezone.now() - timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    start_of_today = start_of_yesterday + timedelta(days=1)

    qs_wsd = wsd.objects.filter(Time_Stamp__range=(start_of_yesterday, start_of_today))

    if not qs_wsd.exists():
        logger.warning("Aucune donnée WSD pour la journée → ET0 impossible")
        return None

    weather_data = qs_wsd.aggregate(
        temp_avg=Avg('TEM'),
        temp_min=Min('TEM'),
        temp_max=Max('TEM'),
        humidity_min=Min('HUM'),
        humidity_max=Max('HUM'),
        wind_avg=Avg('wind_speed'),
    )

    weather_data1 = Data2.objects.filter(
        Time_Stamp__range=(start_of_yesterday, start_of_today)
    ).aggregate(pressure=Avg('Pr'))

    if weather_data1['pressure'] is None:
        logger.warning("Pression manquante → ET0 impossible")
        return None

    # Illumination horaire
    hourly_illum = []
    for hour in range(24):
        interval_start = start_of_yesterday + timedelta(hours=hour)
        interval_end = interval_start + timedelta(hours=1)

        val = qs_wsd.filter(
            Time_Stamp__range=(interval_start, interval_end)
        ).aggregate(avg=Avg('illumination'))['avg']

        if val is not None:
            hourly_illum.append(val)

    if not hourly_illum:
        logger.warning("Radiation manquante → ET0 impossible")
        return None

    radiation_sum = sum(hourly_illum)

    wind_speed_avg = (
        round(weather_data['wind_avg'] / 3.6, 2)
        if weather_data['wind_avg'] is not None
        else None
    )

    day_of_year = start_of_yesterday.timetuple().tm_yday

    return {
        'altitude': 532,
        'latitude': 33.51,
        'day_of_year': day_of_year,
        'pressure': weather_data1['pressure'],
        'humidity_max': weather_data['humidity_max'],
        'humidity_min': weather_data['humidity_min'],
        'temp_avg': weather_data['temp_avg'],
        'temp_max': weather_data['temp_max'],
        'temp_min': weather_data['temp_min'],
        'radiation_sum': radiation_sum,
        'wind_speed_avg': wind_speed_avg,
    }


def ETODR():
    data = fetch_data_for_etoDR()

    A6 = data['altitude']  # Altitude (m)
    B6 = data['latitude']  # Latitude (degrés)
    C6 = 2  # Hauteur de l'anémomètre (m)
    D11 = data['day_of_year']  # Jour de l'année
    E6 = data['pressure']  # Pression moyenne (hPa)
    F11 = data['humidity_max']  # Humidité max (%)
    G11 = data['humidity_min']  # Humidité min (%)
    H11 = data['temp_avg']  # Température moyenne (°C)
    I11 = data['temp_max']  # Température max (°C)
    J11 = data['temp_min']  # Température min (°C)
    K11 = data['radiation_sum']  # Radiation solaire (MJ/m²)
    L11 = data['wind_speed_avg']  # Vitesse moyenne du vent (m/s)

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

    # Résultats
    print(f"ETo: {ETo} mm/jour")

    # Enregistrement dans la base de données
    ET0DR.objects.create(
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

def ETO():
    data = fetch_data_for_eto()

    A6 = data['altitude']  # Altitude (m)
    B6 = data['latitude']  # Latitude (degrés)
    C6 = 2  # Hauteur de l'anémomètre (m)
    D11 = data['day_of_year']  # Jour de l'année
    E6 = data['pressure']  # Pression moyenne (hPa)
    F11 = data['humidity_max']  # Humidité max (%)
    G11 = data['humidity_min']  # Humidité min (%)
    H11 = data['temp_avg']  # Température moyenne (°C)
    I11 = data['temp_max']  # Température max (°C)
    J11 = data['temp_min']  # Température min (°C)
    K11 = data['radiation_sum']  # Radiation solaire (MJ/m²)
    L11 = data['wind_speed_avg']  # Vitesse moyenne du vent (m/s)

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

    # Résultats
    print(f"ETo: {ETo} mm/jour")

    # Enregistrement dans la base de données
    ET0o.objects.create(
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
    print(f"🔍 Dernière entrée ET0 : {last_eto_entry}")
    print(f"🔍 Dernière entrée ET0 Dragino : {last_eto_entry1}")
    print(f"🔍 Dernière entrée ET0 Dragino visiogreen : {last_eto_entry2}")

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

    else:
        print("⏳ Il n'est pas encore temps de calculer ET0 (attendre entre 0h et 2h du matin).")

    return render(request, "job.html", {})

from django.utils import timezone
import pytz

def wsopen(request):
    maroc_tz = pytz.timezone('Africa/Casablanca')
    now = timezone.now().astimezone(maroc_tz).replace(hour=0, minute=0, second=0, microsecond=0)
    print("La date aujourd'hui est ", now)

    current_time = timezone.now().astimezone(maroc_tz)
    current_date = current_time.date()  # Date actuelle sans l'heure
    print("Le temps de comparaison : ", current_time)

    # Récupération des données à partir de minuit
    hm = Data2.objects.filter(Time_Stamp__gte=now)
    hm1 = Ray2.objects.filter(DateRay__gte=now)
    # send_simple_message()
    # Calcul des valeurs max et min
    light_max = hm.aggregate(Max('Light_Intensity'))['Light_Intensity__max'] or 0
    light_min = hm.aggregate(Min('Light_Intensity'))['Light_Intensity__min'] or 0
    light_avg = hm.aggregate(Avg('Light_Intensity'))['Light_Intensity__avg'] or 0
    uv_max= hm.aggregate(Max('UV_Index'))['UV_Index__max'] or 0
    uv_min= hm.aggregate(Min('UV_Index'))['UV_Index__min'] or 0
    uv_avg= hm.aggregate(Avg('UV_Index'))['UV_Index__avg'] or 0
    Tmmax = hm.aggregate(Max('Temp'))['Temp__max'] or 0
    Tmmin = hm.aggregate(Min('Temp'))['Temp__min'] or 0
    Hx = hm.aggregate(Max('Hum'))['Hum__max'] or 0
    Hm = hm.aggregate(Min('Hum'))['Hum__min'] or 0
    Sx = hm.aggregate(Max('Wind_Speed'))['Wind_Speed__max'] or 0
    Sm = hm.aggregate(Min('Wind_Speed'))['Wind_Speed__min'] or 0
    Rx = hm1.aggregate(Max('Ray'))['Ray__max'] or 0
    Rm = hm1.aggregate(Min('Ray'))['Ray__min'] or 0
    Tmavg = hm.aggregate(Avg('Temp'))['Temp__avg'] or 0
    Havg = hm.aggregate(Avg('Hum'))['Hum__avg'] or 0
    Savg = hm.aggregate(Avg('Wind_Speed'))['Wind_Speed__avg'] or 0
    Ravg = hm1.aggregate(Avg('Ray'))['Ray__avg'] or 0

    # Fonction pour récupérer les précipitations sur une période donnée
    def get_rain_sum(start_time):
        return Data2.objects.filter(Time_Stamp__gte=start_time, Time_Stamp__lte=current_time).aggregate(Sum('Rain'))['Rain__sum'] or 0
    def get_rain_sum_(start_time):
        return Data2.objects.filter(Time_Stamp__gte=start_time, Time_Stamp__lte=current_time).aggregate(Sum('Rain_act'))['Rain_act__sum'] or 0

    one_hour_ago = current_time - timezone.timedelta(hours=1)
    eight_hours_ago = current_time - timezone.timedelta(hours=8)
    one_day_ago = current_time - timezone.timedelta(days=1)
    one_week_ago = current_time - timezone.timedelta(days=7)

    p1h = round(get_rain_sum(one_hour_ago), 2)
    p8h = round(get_rain_sum(eight_hours_ago), 2)
    p24h = round(get_rain_sum(one_day_ago), 2)
    p1w = round(get_rain_sum(one_week_ago), 2)

    # p1h_ = round(get_rain_sum_(one_hour_ago), 2)
    # p8h_ = round(get_rain_sum_(eight_hours_ago), 2)
    # p24h_ = round(get_rain_sum_(one_day_ago), 2)
    # p1w_ = round(get_rain_sum_(one_week_ago), 2)
    last_two_rain_acc_1 = Data2.objects.order_by('-Time_Stamp')[:2]
    print("last_record databases :", last_two_rain_acc_1)
    # Récupérer les enregistrements par ordre décroissant de date
    all_rain = Data2.objects.order_by('-Time_Stamp')

    # Initialiser une liste pour stocker les 2 enregistrements valides
    last_two_rain_acc = []

    for record in all_rain:
        if not last_two_rain_acc:
            # Premier enregistrement, on l'ajoute
            last_two_rain_acc.append(record)
        else:
            # Comparer avec le précédent : au moins 5 minutes d’écart ?
            time_diff = last_two_rain_acc[0].Time_Stamp - record.Time_Stamp
            if time_diff >= timedelta(minutes=5):
                last_two_rain_acc.append(record)
                break  # On a trouvé les deux, on peut arrêter
    one_hour = current_time - datetime.timedelta(hours=1)
    huit_hour = current_time - datetime.timedelta(hours=8)
    one_day = current_time - datetime.timedelta(days=1)
    week = current_time - datetime.timedelta(days=7)
    posts = Data2.objects.filter(Time_Stamp__gte=one_hour, Time_Stamp__lte=current_time)
    post8 = Data2.objects.filter(Time_Stamp__gte=huit_hour, Time_Stamp__lte=current_time)
    post24 = Data2.objects.filter(Time_Stamp__gte=one_day, Time_Stamp__lte=current_time)
    postweek = Data2.objects.filter(Time_Stamp__gte=week, Time_Stamp__lte=current_time)

    def get_rain_sum_(queryset):
        rain_sum = queryset.aggregate(Sum('Rain'))['Rain__sum'] or 0
        rain_sum = round(rain_sum,2)
        return round(rain_sum, 2) if rain_sum is not None else 0
    # fwi()
    p1h = get_rain_sum_(posts)
    p8h = get_rain_sum_(post8)
    p24h = get_rain_sum_(post24)
    p1w = get_rain_sum_(postweek)

    # print("last_record.last_two_rain_acc : ", last_two_rain_acc.Rain_acc,type(last_two_rain_acc.Rain_acc))
    tab = Data2.objects.last()
    tab2 = Ray2.objects.last()
    eto = ET0o.objects.last()
    lstfwi = DataFwiO.objects.last()
    # derniers_enregistrements = wsd.objects.exclude(Rg=0).order_by('-Time_Stamp')[:2]
    data = fetch_data_for_eto()
    altitude = data['altitude']  # Altitude (m)
    latitude = data['latitude']  # Latitude (degrés)
    C6 = 2  # Hauteur de l'anémomètre (m)
    day_of_year = data['day_of_year']  # Jour de l'année
    pressure = data['pressure']  # Pression moyenne (hPa)
    humidity_max = data['humidity_max']  # Humidité max (%)
    humidity_min = data['humidity_min']  # Humidité min (%)
    temp_avg = data['temp_avg']  # Température moyenne (°C)
    temp_max = data['temp_max']  # Température max (°C)
    temp_min = data['temp_min']  # Température min (°C)
    radiation_sum = data['radiation_sum']/24  # Radiation solaire (MJ/m²)
    wind_speed_avg = data['wind_speed_avg']  # Vitesse moyenne du vent (m/s)
    context = {
    'tab': tab, 'tab2': tab2, 'eto': eto, 'p1w': p1w, 'p24h': p24h, 'p8h': p8h, 'p1h': p1h,
    'rg_data': last_two_rain_acc,'Rx': Rx, 'Rm': Rm, 'Sx': Sx, 'Sm': Sm, 'Hx': Hx, 'Hm': Hm, 'Tmmax': Tmmax, 'Tmmin': Tmmin,
    'Tmavg': round(Tmavg, 2), 'Havg': round(Havg, 2), 'Savg': round(Savg, 2), 'Ravg': round(Ravg, 2),
    'lstfwi': lstfwi,'wind_speed_avg':wind_speed_avg,
    'radiation_sum':radiation_sum,'temp_min':temp_min,'temp_max':temp_max,'temp_avg':temp_avg,'humidity_min':humidity_min,'humidity_max':humidity_max,'altitude':altitude,'latitude':latitude,
    'light_max':round(light_max,2),'light_min':round(light_min,2),'light_avg':round(light_avg,2),'uv_max':uv_max,'uv_min':uv_min,'uv_avg':round(uv_avg,2),
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

def wsopen1(request):
    now = (datetime.datetime.now()).replace(hour=0, minute=0, second=0, microsecond=0)
    print(now)
    current_time = datetime.datetime.now()
    current_date = current_time.date()
    print(current_time)
    #ETODR_FAO56_DR()
    #ETOS_FAO56_S()
    #ETODRV_FAO56_DRV()
    # last_eto_entry = ET0o.objects.filter(Time_Stamp__date=current_date).last()

    # if current_time.hour == 1 and not last_eto_entry:
    #     ETO()
    #     print("ET0 calculé et enregistré.")
    # else:
    #     print("ET0 a déjà été calculé aujourd'hui ou il n'est pas encore temps.")

    hm = wsd.objects.filter(Time_Stamp__gte=now)
    lstfwi = DataFwiO.objects.last()

###################################################################
####################################################################

    # ETODR()
    """ Température """
    Tmmax = hm.aggregate(Max('TEM'))['TEM__max']
    Tmmin = hm.aggregate(Min('TEM'))['TEM__min']
    Tmavg = hm.aggregate(Avg('TEM'))['TEM__avg'] or 0

    """ Humidité """
    Hx = hm.aggregate(Max('HUM'))['HUM__max']
    Hm = hm.aggregate(Min('HUM'))['HUM__min']
    Havg = hm.aggregate(Avg('HUM'))['HUM__avg'] or 0

    """ Vitesse du vent """
    Sx = hm.aggregate(Max('wind_speed'))['wind_speed__max']
    print("sppped max :",Sx)
    Sm = hm.aggregate(Min('wind_speed'))['wind_speed__min']
    Savg = hm.aggregate(Avg('wind_speed'))['wind_speed__avg'] or 0

    """ Illumination """
    Rx = hm.aggregate(Max('illumination'))['illumination__max']
    Rm = hm.aggregate(Min('illumination'))['illumination__min']
    Ravg = hm.aggregate(Avg('illumination'))['illumination__avg'] or 0

    """ Pluie """
    one_hour = current_time - datetime.timedelta(hours=1)
    huit_hour = current_time - datetime.timedelta(hours=8)
    one_day = current_time - datetime.timedelta(days=1)
    week = current_time - datetime.timedelta(days=7)

    posts = wsd.objects.filter(Time_Stamp__gte=one_hour, Time_Stamp__lte=current_time)
    post8 = wsd.objects.filter(Time_Stamp__gte=huit_hour, Time_Stamp__lte=current_time)
    post24 = wsd.objects.filter(Time_Stamp__gte=one_day, Time_Stamp__lte=current_time)
    postweek = wsd.objects.filter(Time_Stamp__gte=week, Time_Stamp__lte=current_time)

    def get_rain_sum(queryset):
        rain_sum = queryset.aggregate(Sum('rain_gauge'))['rain_gauge__sum'] or 0
        rain_sum = round(rain_sum,2)
        return round(rain_sum, 2) if rain_sum is not None else 0

    p1h = get_rain_sum(posts)
    p8h = get_rain_sum(post8)
    p24h = get_rain_sum(post24)
    p1w = get_rain_sum(postweek)
    derniers_enregistrements = wsd.objects.exclude(Rg=0).order_by('-Time_Stamp')[:2]
    tab = wsd.objects.last()
    eto = ET0o.objects.last()
    last_et0dr = ET0DR.objects.last()
    #lasted = rs_temp.objects.last()
    data = fetch_data_for_etoDR()
    eto_data_valid = validate_eto_data(data)
    altitude = latitude = day_of_year = pressure = None
    humidity_max = humidity_min = None
    temp_avg = temp_max = temp_min = None
    radiation_sum = radiation_sum1 = None
    wind_speed_avg = None
    if eto_data_valid:
        altitude = data['altitude']  # Altitude (m)
        latitude = data['latitude']  # Latitude (degrés)
        C6 = 2  # Hauteur de l'anémomètre (m)
        day_of_year = data['day_of_year']  # Jour de l'année
        pressure = data['pressure']  # Pression moyenne (hPa)
        humidity_max = data['humidity_max']  # Humidité max (%)
        humidity_min = data['humidity_min']  # Humidité min (%)
        temp_avg = data['temp_avg']  # Température moyenne (°C)
        temp_max = data['temp_max']  # Température max (°C)
        temp_min = data['temp_min']  # Température min (°C)
        radiation_sum = data['radiation_sum'] /24 # Radiation solaire (MJ/m²)
        radiation_sum1 = data['radiation_sum'] # Radiation solaire (MJ/m²)
        wind_speed_avg = data['wind_speed_avg']  # Vitesse moyenne du vent (m/s)
    context = {
    'tab': tab, 'eto': eto, 'p1w': p1w, 'p24h': p24h, 'p8h': p8h, 'p1h': p1h,
    'Rx': Rx, 'Rm': Rm, 'Ravg': round(Ravg, 2),
    'Sx': Sx, 'Sm': Sm, 'Savg': round(Savg, 2),
    'Hx': Hx, 'Hm': Hm, 'Havg': round(Havg, 2),
    'Tmmax': Tmmax, 'Tmmin': Tmmin, 'Tmavg': round(Tmavg, 2),'rg_data': derniers_enregistrements,
    'lstfwi': lstfwi, 'last_et0dr': last_et0dr,
    'wind_speed_avg':wind_speed_avg,
    'radiation_sum':radiation_sum,'temp_min':temp_min,'temp_max':temp_max,'temp_avg':temp_avg,'humidity_min':humidity_min,'humidity_max':humidity_max,'altitude':altitude,'latitude':latitude,
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
                        rain_drop = object_irrigation.Rain_Drop
                        humidity = object_irrigation.Soil_Humidity
                        if float(rain_drop) is not None and 40 <= float(rain_drop) <= 80 : #float(rain_drop) < 40 :
                            action = "ouvrir"
                            data_encoded = "AQ=="
                        #elif float(rain_drop) is not None and float(rain_drop) > 70:
                            #action = 'ouvrir'
                            #data_base64 = "AQ=="
                        else:
                            action = "fermer"
                            data_encoded = "AA=="
                        if action:
                            topic = "application/6f065213-3091-483b-a8a0-7a8adb9e442e/device/f29ea90aba287401/command/down"
                            message = {
                                       "devEui": "f29ea90aba287401",
                                       "confirmed": True,
                                       "fPort": 1,
                                       "data": data_encoded
                            }

                            publish.single(
                                        topic,
                                        payload=json.dumps(message),
                                        hostname="mosquitto",  # ou "localhost" si hors docker
                                        port=1883
                            )
                            print(f"🚀 Commande '{action}' envoyée avec succès.")
                        mqtt_topic = "capteurs/mesures"
                        USERNAME = "mqttuser"
                        PASSWORD = "mqttp$$ow"

                        # Prépare les données à publier
                        mqtt_payload = {
                         "Soil_Humidity": object_irrigation.Soil_Humidity,
                         "Rain_Drop": object_irrigation.Rain_Drop,
                         "Rain_Drop_Sensor_State": object_irrigation.Rain_Drop_Sensor_State,
                         "Timestamp": object_irrigation.Time_Stamp.isoformat() if object_irrigation.Time_Stamp else None
                             }
                        
                        try:
                            publish.single(
                             topic=mqtt_topic,
                             payload=json.dumps(mqtt_payload),
                             hostname="10.30.10.50",
                             port=1883,
                             auth={'username': USERNAME, 'password': PASSWORD},
                             keepalive=60,
                             protocol=publish.MQTTv311
                             )
                            print("✅ Données publiées vers le broker externe")
                        except Exception as e:
                            print(f"❌ Erreur lors de la publication MQTT : {e}")
                        
                        
                        
                    except Exception as e:
                        print("Erreur lors de l'enregistrement :", e)
                else:
                    print("Dispositif non reconnu, données ignorées.")
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
                    # object_WsSENSECAP.WindDirection = windDirection
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
                            print("donnée superior 50000")
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
                if data['deviceInfo']['devEui'] == 'a84041d10858e027':  # Vérifie si c'est bien le capteur de sol
                    print("📡 Données reçues du Capteur de sol")

                    # Récupération des données depuis 'object'
                    object_data = data.get('object', {})
                    batterie = object_data.get('Batterie', '0')  # Valeur par défaut '0' si absente

                    print("📊 object_data complet :", object_data)

                    # Boucle sur les capteurs de sol (Capteur_1 à Capteur_4)
                    for i in range(1, 10):
                        capteur_key = f"Capteur_{i}"
                        if capteur_key in object_data:
                            capteur_data = object_data[capteur_key]
                            print(f"🔎 {capteur_key} trouvé :", capteur_data)

                            # Vérification si l'une des valeurs dépasse 65000
                            temperature = float(capteur_data.get('Temperature', '0'))
                            humidite = float(capteur_data.get('Humidite', '0'))
                            conductivite = float(capteur_data.get('Conductivite', '0'))
                            azote = float(capteur_data.get('Azote', '0'))
                            phosphore = float(capteur_data.get('Phosphore', '0'))
                            potassium = float(capteur_data.get('Potassium', '0'))

                            if any(value > 65000 for value in [temperature, humidite, conductivite, azote, phosphore, potassium]):
                                print(f"⚠️ Ignoré l'enregistrement pour {capteur_key} car une des valeurs dépasse 65000")
                                continue  # Ignorer cet enregistrement et passer au suivant

                            try:
                                CapSol2.objects.create(
                                    devId=i,
                                    Temp=temperature,
                                    Hum=humidite,
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

def filter_data(request, field_data2, field_wsd, template_name):
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
    print("Dta filter wsd : ",all_wsd,all_data2)
    # Extraction des données pour les graphiques
    labels_data2 = [data.Time_Stamp.strftime("%Y-%m-%d %H:%M:%S") for data in all_data2]
    labels_wsd = [data.Time_Stamp.strftime("%Y-%m-%d %H:%M:%S") for data in all_wsd]

    data_data2 = [getattr(data, field_data2, 0) if getattr(data, field_data2, None) is not None else 0 for data in all_data2]
    data_wsd = [getattr(data, field_wsd, 0) if getattr(data, field_wsd, None) is not None else 0 for data in all_wsd]
    print("Dta filter wsd : ",data_wsd,data_data2)
    # Récupération du dernier enregistrement (gestion des valeurs `None`)
    lst_data2 = Data2.objects.last()
    lst_wsd = wsd.objects.last()

    last_data2_value = getattr(lst_data2, field_data2, 0) if lst_data2 and getattr(lst_data2, field_data2, None) is not None else 0
    last_wsd_value = getattr(lst_wsd, field_wsd, 0) if lst_wsd and getattr(lst_wsd, field_wsd, None) is not None else 0
    zipped_data2 = zip(labels_data2, data_data2)
    print("zipped : ",zipped_data2)
    zipped_datawsd = zip(labels_wsd, data_wsd)
    print("zipped : ",zipped_datawsd)
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
    }

    return render(request, template_name, context)

# Vue pour la température
def data_filter(request):
    return filter_data(request, field_data2='Temp', field_wsd='TEM', template_name="enviro/temp1.html")

# Vue pour l'humidité
def data_filter_hum(request):
    return filter_data(request, field_data2='Hum', field_wsd='HUM', template_name="enviro/hum1.html")

# Vue pour la vitesse de vent
def data_filter_ws(request):
    return filter_data(request, field_data2='Wind_Speed', field_wsd='wind_speed', template_name="enviro/tvoc1.html")

# Vue pour la pluie
def data_filter_pl(request):
    return filter_data(request, field_data2='Rain', field_wsd='rain_gauge', template_name="enviro/tvoc3.html")

# def data_filter_pl(request):
#     return filter_data(request, field_data2='Rain', field_wsd='rain_gauge', template_name="enviro/tvoc3.html")

def data_filter_ry(request):
    # Récupération des valeurs du formulaire
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Initialisation des listes
    labels_data2 = []
    labels_wsd = []
    data_data2 = []
    data_wsd = []

    # Si l'utilisateur a spécifié des dates, on les utilise, sinon on prend la journée actuelle
    if start_date and end_date:
        # Conversion des chaînes de caractères en objets datetime
        start_date = make_aware(datetime.datetime.strptime(start_date, "%Y-%m-%d"))
        end_date = make_aware(datetime.datetime.strptime(end_date, "%Y-%m-%d"))

        # Ajout de la fin de journée (23:59:59) à la date de fin pour inclure toute la journée
        end_date = end_date.replace(hour=23, minute=59, second=59)

        # Filtrage des données entre la date de début et la date de fin pour les deux modèles
        all_data2 = Ray2.objects.filter(DateRay__range=(start_date, end_date))
        all_wsd = wsd.objects.filter(Time_Stamp__range=(start_date, end_date))

    else:
        # Si aucune date n'est spécifiée, on récupère les données de la journée en cours
        today = datetime.datetime.now()
        one_day_ago = (datetime.datetime.now() - datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0,
                                                                                 microsecond=0)
        start_date = make_aware(datetime.datetime(today.year, today.month, today.day, 0, 0, 0))
        end_date = make_aware(datetime.datetime(today.year, today.month, today.day, 23, 59, 59))

        # Filtrage des données pour la journée actuelle
        all_data2 = Ray2.objects.filter(DateRay__gte=one_day_ago)
        all_wsd = wsd.objects.filter(Time_Stamp__gte=one_day_ago)

    # Collecte des labels et des données pour les graphiques (pour chaque classe)
    for data in all_data2:
        labels_data2.append(data.DateRay.strftime("%Y-%m-%d %H:%M:%S"))
        # Remplacement de None par 0
        data_data2.append(data.Ray if data.Ray is not None else 0)

    for data in all_wsd:
        labels_wsd.append(data.Time_Stamp.strftime("%Y-%m-%d %H:%M:%S"))
        # Remplacement de None par 0
        data_wsd.append(data.illumination if data.illumination is not None else 0)

    # Derniers objets de chaque modèle
    lst_data2 = Ray2.objects.last()
    lst_wsd = wsd.objects.last()
    zipped_data2 = zip(labels_data2, data_data2)
    print("zipped : ",zipped_data2)
    zipped_datawsd = zip(labels_wsd, data_wsd)
    print("zipped : ",zipped_datawsd)
    # Création du contexte pour passer les données à la vue
    context = {
        'all_data2': all_data2,
        'all_wsd': all_wsd,
        'lst_data2': lst_data2,
        'lst_wsd': lst_wsd,
        'labels_data2': labels_data2,
        'labels_wsd': labels_wsd,
        'data_data2': data_data2,
        'data_wsd': data_wsd,
        'start_date': start_date.strftime("%Y-%m-%d"),
        'end_date': end_date.strftime("%Y-%m-%d"),
        'zipped_data2': list(zipped_data2),
        'zipped_datawsd': list(zipped_datawsd),
    }

    return render(request, "enviro/temp3.html", context)
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

dev_eui_1 ="ab7554dc00001075"
dev_eui_van2 ="1e4554dc00001057"
dev_eui_van3 ="2e3554dc00001057"
def debit_data(request):

    lasted = debitcap.objects.last()
    context={'lasted':lasted, 'vannes': {
            'vanne 1': "ce7554dc00001057",
            'vanne 2': "2e3554dc00001057",
            'vanne 3': "1e4554dc00001057",
        }}
    irrigation_time = None
    milliseconds = None
    hex_milliseconds = None
    # Appeler la fonction pour envoyer le downlink

    if request.method == 'POST':
        action = request.POST.get('action')
        irrigation_time = request.POST.get('irrigation_time')
        selected_vanne = request.POST.get('vanne')  # van1, van2, etc.
        dev_eui_map = context['vannes']
        dev_eui = dev_eui_map.get(selected_vanne)
        milliseconds = request.POST.get('milliseconds')

        if action == 'set_time' and irrigation_time:
            # Traiter l'heure d'irrigation ici
            print(f"Heure d'irrigation : {irrigation_time}")
        if action == 'on':
            milliseconds_on_off = request.POST.get('milliseconds_on_off')
            print("on relay : ", milliseconds_on_off)
            send_downlink_1(api_token, dev_eui_1, server, etat=1)
            # Faire quelque chose pour ouvrir avec durée milliseconds_on_off
        if action == 'off':
            milliseconds_on_off = request.POST.get('milliseconds_on_off')
            print("off relay : ",milliseconds_on_off)
            send_downlink_1(api_token, dev_eui_1, server, etat=0)
        if action == 'send_time' and milliseconds:
            # Traiter le temps en ms ici
            print(f"Temps d'irrigation : {milliseconds}")
            # Convertir le temps en millisecondes et limiter à 6 bits
            downlink_id = send_downlink(api_token, dev_eui, server, milliseconds)

            if downlink_id:
                print(f"Downlink envoyé avec succès, ID : {downlink_id}")
            else:
                print("Erreur lors de l'envoi du downlink.")

        return redirect('debit')  # 👈 rediriger vers la page 'home' pour éviter re-post

    return render(request,"debitControl.html",context)
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
