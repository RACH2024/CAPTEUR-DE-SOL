import datetime

from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timedelta
from django.db.models import Avg

# from django.conf.locale.en import formats as en_formats
# en_formats.TIME_FORMATS = ['%H:%M:%S']
# Create your models here
from twilio.rest import Client
TWILIO_ACCOUNT_SID = 'AC93347a234d4f1e30e1abd3366488364d'
TWILIO_AUTH_TOKEN = 'd4d2e44d6960c648538f88bf74b75cc8'
TWILIO_WHATSAPP_NUMBER = 'whatsapp:+14155238886'  # Numéro sandbox WhatsApp de Twilio
TO_WHATSAPP_NUMBER = 'whatsapp:+212668316320'  # Remplacez par le numéro WhatsApp destinataire en format international

EPA_BREAKPOINTS = {
    'pm10': [(0, 54, 0, 50), (55, 154, 51, 100), (155, 254, 101, 150), (255, 354, 151, 200), (355, 424, 201, 300), (425, 504, 301, 400), (505, 604, 401, 500)],
    'pm25': [(0.0, 12.0, 0, 50), (12.1, 35.4, 51, 100), (35.5, 55.4, 101, 150), (55.5, 150.4, 151, 200), (150.5, 250.4, 201, 300), (250.5, 350.4, 301, 400), (350.5, 500.4, 401, 500)],
    'no2': [(0.0, 0.053, 0, 50), (0.054, 0.100, 51, 100), (0.101, 0.360, 101, 150), (0.361, 0.649, 151, 200), (0.650, 1.249, 201, 300), (1.250, 1.649, 301, 400), (1.650, 2.049, 401, 500)],
    'co': [(0.0, 4.4, 0, 50), (4.5, 9.4, 51, 100), (9.5, 12.4, 101, 150), (12.5, 15.4, 151, 200), (15.5, 30.4, 201, 300), (30.5, 40.4, 301, 400), (40.5, 50.4, 401, 500)],
    'o3': [(0.0, 0.054, 0, 50), (0.055, 0.070, 51, 100), (0.071, 0.085, 101, 150), (0.086, 0.105, 151, 200), (0.106, 0.200, 201, 300), (0.201, 0.404, 301, 400), (0.405, 0.504, 401, 500)]
}
class vann(models.Model):
    onoff = models.BooleanField()

    dt=models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return str(self.onoff)

    def save(self, *args, **kwargs):
        msg=self.onoff
        super(vann, self).save(*args, **kwargs)

        # client.publish("vanne", str(msg))

        import paho.mqtt.client as mqtt

        client1 = mqtt.Client()
        client = mqtt.Client()
        client1.disconnect()
        client1.connect("broker.hivemq.com", 1883, 80)
        client.connect("broker.hivemq.com", 1883, 80)
        print("..................")
        print("self :", self.onoff)
        if (self.onoff == False):
            client.publish("test", "0")
            print("off")
        elif (self.onoff == True):
            client1.publish("test1","1")  # publish the message typed by the user# publish the message typed by the user
            print("on")
        #client1.disconnect() #disconnect from server


class batvanne(models.Model):
    bat = models.FloatField( null=True)
    dt = models.DateTimeField(auto_now=True, null=True)


class CapSol(models.Model):
    devId = models.IntegerField()
    Temp = models.FloatField( null=True)
    Hum = models.FloatField( null=True)
    ec = models.FloatField( null=True)
    Sal = models.FloatField( null=True)
    #N = models.FloatField( null=True)
    #P = models.FloatField( null=True)
    #K = models.FloatField( null=True)
    Bat = models.FloatField( null=True)
    time=models.TimeField(auto_now=True)
    dt = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return str(self.dt)
    # def save(self, *args, **kwargs):
    #     now = datetime.datetime.now()
    #     print("created ...... capteur de sol ",now)


class CapSol2(models.Model):
    devId = models.IntegerField()
    Temp = models.FloatField( null=True)
    Hum = models.FloatField( null=True)
    ec = models.FloatField( null=True)
    N = models.FloatField( null=True)
    P = models.FloatField( null=True)
    K = models.FloatField( null=True)
    Sal = models.FloatField( null=True)
    Bat = models.FloatField( null=True)
    time=models.TimeField(auto_now=True)
    dt = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return str(self.dt)+ " Dev_ID : " + str(self.devId)+" Température : " + str(self.Temp)

##################################capteur sol calibré par méthode graviométrie#####################################
class CapSolGraviometrie(models.Model):
    devId = models.IntegerField()
    TempGraviometrie = models.FloatField( null=True)
    HumGraviometrie = models.FloatField( null=True)
    ecGraviometrie = models.FloatField( null=True)
    NGraviometrie = models.FloatField( null=True)
    PGraviometrie = models.FloatField( null=True)
    KGraviometrie = models.FloatField( null=True)
    SalGraviometrie = models.FloatField( null=True)
    BatGraviometrie = models.FloatField( null=True)
    time=models.TimeField(auto_now=True)
    dt = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return str(self.dt)+ " Dev_ID : " + str(self.devId)+" Température : " + str(self.TempGraviometrie)

######################################################################################
class Ws(models.Model):
    Temperature = models.FloatField( null=True)
    Humidity = models.FloatField( null=True)
    Vent = models.FloatField( null=True)
    Rafale = models.FloatField( null=True)
    Pluv = models.FloatField( null=True)
    Ray = models.FloatField( null=True)
    date = models.DateTimeField(null=True)
    dateRay = models.DateTimeField(null=True)
    def __str__(self):
        return str(self.pk )  +  str(self.date)

class Ray(models.Model):
    Ray = models.FloatField(null=True)
    dateRay = models.DateTimeField(null=True)
    def __str__(self):
        return str(self.Ray)

class Ray2(models.Model):
    Ray = models.FloatField(null=True)
    Bat = models.FloatField(null=True)
    DateRay = models.DateTimeField(default=timezone.now)
    def __str__(self):
        return str(self.Ray)

class Data2(models.Model):
    # ID_Device = models.IntegerField()
    Temp = models.FloatField(null=True)
    Hum = models.FloatField(null=True)
    #Ray = models.FloatField(null=True)

    Wind_Speed = models.FloatField(null=True)
    Light_Intensity = models.FloatField(null=True)
    UV_Index = models.FloatField(null=True)
    Rain = models.FloatField(null=True)
    Rain_acc = models.FloatField(null=True)
    Rain_act = models.FloatField(null=True)
    # alt = models.FloatField(null=True)
    Pr = models.FloatField(null=True)
    # d = models.FloatField(null=True)
    Time_Stamp = models.DateTimeField(default=timezone.now)
    #i = models.IntegerField(null=True)
    # Bat = models.FloatField(null=True)
    def __str__(self):
        return "rain_actuel : " + str(self.Rain_act) + "\t rain_acc : "  + str(self.Rain_acc) + "\t rain : "  + str(self.Rain) +"\t Time : " + str(self.Time_Stamp)

class ET0ExecutionLog(models.Model):
    date = models.DateField(unique=True)  # Stocke la date d'exécution

class Data(models.Model):
    ID_Device = models.IntegerField()
    Temp = models.FloatField(null=True)
    Hum = models.FloatField(null=True)
    Ray = models.FloatField(null=True)
    Wind_Speed = models.FloatField(null=True)
    Rain = models.FloatField(null=True)
    Bat = models.FloatField(null=True)
    alt = models.FloatField(null=True)
    pr = models.FloatField(null=True)
    d = models.FloatField(null=True)
    Time_Stamp = models.DateTimeField(default=timezone.now)
    i = models.IntegerField(null=True)
    def __str__(self):
        return str(self.d) + str(self.Time_Stamp)
    #
    # def save(self, *args, **kwargs):
    #     now = datetime.datetime.now()
    #     x=now.time.strftime("%H:%M:%S")
    #     if not Data.objects.filter(Time_Stamp__date= now.date,Time_Stamp__time=x).exists():
    #         print("not exist ....")
    #
    #     else:
    #         print("data exist ")
    # def save(self, *args, **kwargs):
    #     now = datetime.datetime.now()
    #     print("created ......Weather station ",now)


class ET0(models.Model):
    value = models.FloatField(null=True)
    WSavg = models.FloatField(null=True)
    Tmax = models.FloatField(null=True)
    Tmin = models.FloatField(null=True)
    Hmax = models.FloatField(null=True)
    Hmin = models.FloatField(null=True)
    Raym = models.FloatField(null=True)
    U2 = models.FloatField(null=True)
    Delta = models.FloatField(null=True)
    Time_Stamp = models.DateTimeField(auto_now_add=True)
    i = models.IntegerField(null=True)

    def __str__(self):
        return "ET0: "+str(self.value)+" "+ str( self.Time_Stamp)

class DataFwi(models.Model):
    ffmc = models.FloatField()
    dmc = models.FloatField()
    dc = models.FloatField()
    isi = models.FloatField()
    bui = models.FloatField()
    fwi = models.FloatField()
    Time_Stamp = models.DateTimeField(auto_now_add=True,null=True)

    def __str__(self):
        return "FWI = "+str(self.fwi)+" @ "+str(self.Time_Stamp)


class DataFwiO(models.Model):
    ffmc = models.FloatField()
    dmc = models.FloatField()
    dc = models.FloatField()
    isi = models.FloatField()
    bui = models.FloatField()
    fwi = models.FloatField()
    i=models.IntegerField(null=True)
    Time_Stamp = models.DateTimeField(auto_now_add=True,null=True)

    def __str__(self):
        return "FWI = "+str(self.fwi)+" @ "+str(self.Time_Stamp)

class Envdata(models.Model):
    devId = models.CharField(max_length=10,null=True)
    pm10 = models.FloatField()
    pm25 = models.FloatField()
    pm = models.FloatField()
    co2 = models.FloatField()
    ch2o = models.FloatField()
    o3 = models.FloatField()
    co = models.FloatField()
    tvoc = models.FloatField()
    no2 = models.FloatField()
    temp = models.FloatField()
    hum = models.FloatField()
    bat = models.FloatField()
    #i=models.IntegerField(null=True)
    Time_Stamp = models.DateTimeField(auto_now_add=True,null=True)
    # Champs pour stocker le dernier calcul d'IAQ pour chaque capteur
    last_calculation_S1 = models.DateTimeField(null=True, blank=True)
    last_calculation_S2 = models.DateTimeField(null=True, blank=True)
    last_calculation_S3 = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Device {self.devId} - CO2: {self.co2} ppm @ {self.Time_Stamp}"

    def save(self, *args, **kwargs):
        # Récupérer l'heure actuelle
        current_time = (datetime.datetime.now() - datetime.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        print("current time save : ",current_time)
        # Charger les dernières valeurs de calcul depuis le dernier enregistrement
        latest_entry = Envdata.objects.filter(devId=self.devId).order_by('-Time_Stamp').first()
        print("lastest entry :",latest_entry)
        # Récupérer la dernière heure de calcul depuis l'enregistrement correspondant
        if latest_entry:
            if self.devId == 'S1':
                self.last_calculation_S1 = latest_entry.last_calculation_S1
                print("lastest entry last S1 hour :", self.last_calculation_S1)
            elif self.devId == 'S2':
                self.last_calculation_S2 = latest_entry.last_calculation_S2
                print("lastest entry last S2 hour :", self.last_calculation_S2)
            elif self.devId == 'S3':
                self.last_calculation_S3 = latest_entry.last_calculation_S3
                print("lastest entry last S3 hour :", self.last_calculation_S3)

        # Comparer et calculer l'IAQ pour chaque capteur, puis enregistrer le calcul
        if self.devId == 'S1' and (not self.last_calculation_S1 or self.should_calculate_iaq(current_time, self.last_calculation_S1)):
            print(f"Curent time pour S1 à {current_time}")
            print(f"last_calculation_S1 précédent : {self.last_calculation_S1}")
            self.calculate_hourly_iaq_and_send('S1')
            # Envdata.objects.filter(id=self.id).update(last_calculation_S1=current_time)
            self.last_calculation_S1=current_time
            print(f"last_calculation_S1 actuelle : {self.last_calculation_S1}")
            # self.save(update_fields=['self.last_calculation_S1'])
            print(f"last_calculation_S11 actuelle : {self.last_calculation_S1}")


        elif self.devId == 'S2' and (not self.last_calculation_S2 or self.should_calculate_iaq(current_time, self.last_calculation_S2)):
            print(f"Curent time pour S2 à {current_time}")
            print(f"last_calculation_S2 précédent : {self.last_calculation_S2}")
            self.calculate_hourly_iaq_and_send('S2')
            # Envdata.objects.filter(id=self.id).update(last_calculation_S2=current_time)
            self.last_calculation_S2=current_time
            print(f"last_calculation_S2 actuelle : {self.last_calculation_S2}")
            # self.save(update_fields=['self.last_calculation_S3'])
            print(f"last_calculation_S22 actuelle : {self.last_calculation_S2}")


        elif self.devId == 'S3' and (not self.last_calculation_S3 or self.should_calculate_iaq(current_time, self.last_calculation_S3)):
            print(f"Curent time pour S3 à {current_time}")
            print(f"last_calculation_S3 précédent : {self.last_calculation_S3}")
            self.calculate_hourly_iaq_and_send('S3')
            # Envdata.objects.filter(id=self.id).update(last_calculation_S3=current_time)
            self.last_calculation_S3=current_time
            print(f"last_calculation_S3 actuelle : {self.last_calculation_S3}")
            # self.save(update_fields=['self.last_calculation_S3'])
            print(f"last_calculation_S33 actuelle : {self.last_calculation_S3}")



        # Alerte CO si nécessaire
        if self.co > 50:
            self.send_whatsapp_alert(self.co, critical=True)
        elif self.co > 20:
            self.send_whatsapp_alert(self.co)

        # Appeler la méthode save parente
        super().save(*args, **kwargs)

    def should_calculate_iaq(self, current_time, last_calculation_time):
        """Vérifier si le calcul de l'IAQ doit être effectué pour un capteur donné."""
        # Si le calcul n'a jamais été effectué, le faire
        if not last_calculation_time:
            return True
        print("hour current :", current_time.hour)
        print("hour last :", last_calculation_time.hour)
        # Vérifier si une heure s'est écoulée depuis le dernier calcul
        return current_time.hour != last_calculation_time.hour

    def calculate_hourly_iaq_and_send(self, sensor_id):
        """Calculer l'IAQ pour l'heure passée et envoyer un rapport WhatsApp."""
        one_hour_ago = (datetime.datetime.now() - datetime.timedelta(hours=2)).replace(minute=0, second=0, microsecond=0)
        now = (datetime.datetime.now() - datetime.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)

        data_points = Envdata.objects.filter(devId=sensor_id, Time_Stamp__gte=one_hour_ago, Time_Stamp__lte=now)

        if data_points.exists():
            avg_values = {
                'pm10': data_points.aggregate(Avg('pm10'))['pm10__avg'],
                'pm25': data_points.aggregate(Avg('pm25'))['pm25__avg'],
                'co': data_points.aggregate(Avg('co'))['co__avg'],
                'o3': data_points.aggregate(Avg('o3'))['o3__avg'],
                'no2': data_points.aggregate(Avg('no2'))['no2__avg'],
            }
            print(avg_values)
            indices = {p: self.calculate_aqi(avg_values[p], EPA_BREAKPOINTS[p]) for p in avg_values if avg_values[p]}
            # Créer le message d'alerte avec les informations de l'heure et les indices calculés
            message = f"📊 Rapport de qualité de l'air pour le dispositif {sensor_id}:\n\n"
            message += f"Intervalle de temps: {one_hour_ago.strftime('%H:%M')} - {now.strftime('%H:%M')}\n\n"
            message += "Moyennes horaires des polluants:\n"
            message += "\n".join([f"{p}: {avg_values[p]:.2f}" for p in avg_values if avg_values[p]]) + "\n\n"
            message += "AQI Calculés:\n"
            message += "\n".join([f"{p}: AQI={aqi:.2f}" for p, aqi in indices.items()])

            self.send_iaq_whatsapp_alert(message)

    def calculate_aqi(self, concentration, breakpoints):
        for bp in breakpoints:
            if bp[0] <= concentration <= bp[1]:
                return ((bp[3] - bp[2]) / (bp[1] - bp[0])) * (concentration - bp[0]) + bp[2]
        return 500
    def send_iaq_whatsapp_alert(self, message_body):
        """Envoyer un message WhatsApp avec les indices de qualité de l'air via Twilio."""
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        # Préparer le message avec l'ID du dispositif
        message_body = message_body

        # Envoyer le message WhatsApp via Twilio
        message = client.messages.create(
            body=message_body,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=TO_WHATSAPP_NUMBER
        )
        print(f"Message IAQ WhatsApp envoyé : {message.sid}")
    def send_whatsapp_alert(self, co_value, critical=False):
        """Envoyer un message WhatsApp pour les alertes CO via Twilio."""
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        # Créer le message d'alerte en fonction du niveau de danger
        if critical:
            message_body = (f"🚨 ALERTE CRITIQUE : Niveau de CO extrêmement élevé détecté ! "
                            f"Valeur actuelle : {co_value} ppm. Prenez des mesures immédiates ! "
                            f"Zone : {self.devId}.")
        else:
            message_body = (f"⚠️ Alerte : Niveau de CO élevé détecté ! "
                            f"Valeur actuelle : {co_value} ppm. Veuillez vérifier l'environnement. "
                            f"Zone : {self.devId}.")

        # Envoyer le message WhatsApp via Twilio
        message = client.messages.create(
            body=message_body,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=TO_WHATSAPP_NUMBER
        )
        print(f"Message WhatsApp envoyé : {message.sid}")

    # def send_whatsapp_alert(self, co_value, critical=False):
    #     """Envoyer un message WhatsApp pour les alertes CO via Twilio."""
    #     client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    #     # Créer le message d'alerte en fonction du niveau de danger
    #     if critical:
    #         message_body = (f"🚨 ALERTE CRITIQUE : Niveau de CO extrêmement élevé détecté ! "
    #                         f"Valeur actuelle : {co_value} ppm. Prenez des mesures immédiates ! "
    #                         f"Zone : {self.devId}.")
    #     else:
    #         message_body = (f"⚠️ Alerte : Niveau de CO élevé détecté ! "
    #                         f"Valeur actuelle : {co_value} ppm. Veuillez vérifier l'environnement. "
    #                         f"Zone : {self.devId}.")

    #     # Envoyer le message WhatsApp via Twilio
    #     message = client.messages.create(
    #         body=message_body,
    #         from_=TWILIO_WHATSAPP_NUMBER,
    #         to=TO_WHATSAPP_NUMBER
    #     )
    #     print(f"Message WhatsApp envoyé : {message.sid}")

class cwsi(models.Model):
    Ta = models.FloatField()
    Tc = models.FloatField()
    # cw = models.FloatField(null=True)
    Time_Stamp = models.DateTimeField(auto_now_add=True,null=True)

    def __str__(self):
        return "Tc = "+str(self.Tc)+" @ "+str(self.Time_Stamp)


class cwsiO(models.Model):

    cw = models.FloatField(null=True)
    Time_Stamp = models.DateTimeField(auto_now_add=True,null=True)

    def __str__(self):
        return "cw = "+str(self.cw)+" @ "+str(self.Time_Stamp)

class ET0o(models.Model):
    value = models.FloatField(null=True)
    WSavg = models.FloatField(null=True)
    Tmax = models.FloatField(null=True)
    Tmin = models.FloatField(null=True)
    Tavg = models.FloatField(null=True)
    Hmax = models.FloatField(null=True)
    Hmin = models.FloatField(null=True)
    Raym = models.FloatField(null=True)
    U2 = models.FloatField(null=True)
    Delta = models.FloatField(null=True)
    Time_Stamp = models.DateTimeField(default=timezone.now)
    dt = models.DateField(auto_now_add=True, null=True)
    i = models.IntegerField(null=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['Time_Stamp'],
                name='unique_et0o_timestamp'
            )
        ]
    def __str__(self):
        return "ET0: "+str(self.value)+" "+str(self.Time_Stamp)

    def save(self, *args, **kwargs):
        msg=self.value
        super(ET0o, self).save( *args, **kwargs)
        print("msg" +str(msg))
        # client.publish("vanne", str(msg))

        # import paho.mqtt.client as mqtt
        #
        # client = mqtt.Client()
        #
        # client.connect("broker.hivemq.com", 1883, 80)
        #
        # client.publish("et", msg)  # publish the message typed by the user
        # print(msg)
        # client.disconnect(); #disconnect from server
    # {'wind_direction_angle': 201.2, 'wind_direction': 'E', 'HUM': 16.7, 'rain_gauge': 51.2,
    # 'CO2': 0.0, 'wind_speed': 0.0, 'illumination': 0.0, 'wind_speed_level': 0.0, 'pressure': 48.8, 'TEM': 57.2, 'PM2_5': 0.0, 'PM10': 0.0, 'TSR': 0.0}
class wsd(models.Model):
    # ID_Device = models.IntegerField()
    wind_direction_angle = models.FloatField(null=True)
    wind_direction = models.CharField(max_length=100, null=True, blank=True)
    HUM = models.FloatField(null=True)
    Rg = models.FloatField(null=True)
    rain_gauge = models.FloatField(null=True)
    wind_speed = models.FloatField(null=True)
    illumination = models.FloatField(null=True)
    TEM = models.FloatField(null=True)
    # pr = models.FloatField(null=True)
    # d = models.FloatField(null=True)
    Time_Stamp = models.DateTimeField(default=timezone.now)
    # i = models.IntegerField(null=True)
    # def save(self, *args, **kwargs):
    #     last_record = wsd.objects.exclude(rain_gauge=0).order_by('-Time_Stamp').first()  # Dernier enregistrement non nul
    #     print("last_record databases :", last_record)
    #     if last_record and self.rain_gauge is not None:
    #         last_value = last_record.rain_gauge if last_record.rain_gauge is not None else 0

    #         if self.rain_gauge > last_value:
    #             self.rain_gauge = self.rain_gauge - last_value  # Différence = pluie tombée
    #         else:
    #             self.rain_gauge = 0  # Aucune nouvelle pluie détectée

    #     super(wsd, self).save(*args, **kwargs)  # Enregistrer l'objet

    def __str__(self):
        return f"TEM: {self.TEM}, Rain: {self.rain_gauge} mm, Rain_Acc: {self.Rg} mm, Time: {self.Time_Stamp}"

"""
class wsd(models.Model):
    # ID_Device = models.IntegerField()
    wind_direction_angle = models.FloatField(null=True)
    wind_direction = models.CharField(max_length=100, null=True, blank=True)
    HUM = models.FloatField(null=True)
    rain_gauge = models.FloatField(null=True)
    wind_speed = models.FloatField(null=True)
    illumination = models.FloatField(null=True)
    TEM = models.FloatField(null=True)
    # pr = models.FloatField(null=True)
    # d = models.FloatField(null=True)
    Time_Stamp = models.DateTimeField(default=timezone.now)
    # i = models.IntegerField(null=True)
    def __str__(self):
        return str(self.TEM) + str(self.Time_Stamp)
"""


class ET0DR(models.Model):
    value = models.FloatField()
    WSavg = models.FloatField()
    Tmax = models.FloatField()
    Tmin = models.FloatField()
    Tavg = models.FloatField(null=True)
    Hmax = models.FloatField()
    Hmin = models.FloatField()
    Raym = models.FloatField()
    #Ray_Wm2 = models.FloatField(null=True, blank=True)
    U2 = models.FloatField()
    Delta = models.IntegerField()
    Time_Stamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return "ET0DR: "+str(self.value)+" "+ str( self.Time_Stamp)


class ET0DRv(models.Model):
    value = models.FloatField()
    WSavg = models.FloatField()
    Tmax = models.FloatField()
    Tmin = models.FloatField()
    Tavg = models.FloatField(null=True)
    Hmax = models.FloatField()
    Hmin = models.FloatField()
    Raym = models.FloatField()
    U2 = models.FloatField()
    Delta = models.IntegerField()
    Time_Stamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return "ET0DR: "+str(self.value)+" "+ str( self.Time_Stamp)

############################ET0S FAO56##########################################
class ETOSensCap_FAO56(models.Model):
    value = models.FloatField()
    WSavg = models.FloatField()
    Tmax = models.FloatField()
    Tmin = models.FloatField()
    Tavg = models.FloatField(null=True)
    Hmax = models.FloatField()
    Hmin = models.FloatField()
    Raym = models.FloatField()
    U2 = models.FloatField()
    Delta = models.IntegerField()
    Time_Stamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return "ETOSensCap_FAO56: "+str(self.value)+" "+ str( self.Time_Stamp)
################################################################################

############################ET0DR FAO56#########################################
class ETODR_FAO56(models.Model):
    value = models.FloatField()
    WSavg = models.FloatField()
    Tmax = models.FloatField()
    Tmin = models.FloatField()
    Tavg = models.FloatField(null=True)
    Hmax = models.FloatField()
    Hmin = models.FloatField()
    Raym = models.FloatField()
    U2 = models.FloatField()
    Delta = models.IntegerField()
    Time_Stamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return "ETODR_FAO56: "+str(self.value)+" "+ str( self.Time_Stamp)
################################################################################

############################ET0DR FAO56#########################################
class ETODRV_FAO56(models.Model):
    value = models.FloatField()
    WSavg = models.FloatField()
    Tmax = models.FloatField()
    Tmin = models.FloatField()
    Tavg = models.FloatField(null=True)
    Hmax = models.FloatField()
    Hmin = models.FloatField()
    Raym = models.FloatField()
    U2 = models.FloatField()
    Delta = models.IntegerField()
    Time_Stamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return "ETODRV_FAO56: "+str(self.value)+" "+ str( self.Time_Stamp)
################################################################################

#########################débitmètre#############################################

class debitcap(models.Model):
    #devId = models.IntegerField()
    debit = models.FloatField(null=True)
    pulse = models.FloatField(null=True)
    flag = models.FloatField(null=True)
    #Bat = models.FloatField( null=True)
    Time_Stamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"debit: {self.debit} L, Time: {self.Time_Stamp}"

#########################electrovanne###############################################

class ev_batt(models.Model):
    #devId = models.IntegerField()
    batt = models.FloatField(null=True)
    Time_Stamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"battery: {self.batt} V, Time: {self.Time_Stamp}"
        #############EV2################
class ev_batt2(models.Model):
    #devId = models.IntegerField()
    batt = models.FloatField(null=True)
    Time_Stamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"battery: {self.batt} V, Time: {self.Time_Stamp}"
        ##############EV3##########################
class ev_batt3(models.Model):
    #devId = models.IntegerField()
    batt = models.FloatField(null=True)
    Time_Stamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"battery: {self.batt} V, Time: {self.Time_Stamp}"

#########################temp/hum###############################################

class rs_temp(models.Model):
    #devId = models.IntegerField()
    batt = models.FloatField(null=True)
    temp1 = models.FloatField(null=True)
    hum1 = models.FloatField(null=True)
    temp2 = models.FloatField(null=True)
    hum2 = models.FloatField(null=True)
    Time_Stamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"battery: {self.batt} V, temp1: {self.temp1} °C, hum1: {self.hum1} %, temp2: {self.temp2} °C, hum2: {self.hum2} %, Time: {self.Time_Stamp}"
####################RS_SOL_567############################
class rs_sol(models.Model):
    #devId = models.IntegerField()
    #batt = models.FloatField(null=True)
    #temp1 = models.FloatField(null=True)
    #hum1 = models.FloatField(null=True)
    #temp2 = models.FloatField(null=True)
    #hum2 = models.FloatField(null=True)
    #Time_Stamp = models.DateTimeField(default=timezone.now)

    #def __str__(self):
        #return f"battery: {self.batt} V, temp1: {self.temp1} °C, hum1: {self.hum1} %, temp2: {self.temp2} °C, hum2: {self.hum2} %, Time: {self.Time_Stamp}"
    devId = models.IntegerField()
    Temp = models.FloatField( null=True)
    Hum = models.FloatField( null=True)
    Ec = models.FloatField( null=True)
    Sal = models.FloatField( null=True)
    Bat = models.FloatField( null=True)
    time=models.TimeField(auto_now=True)
    dt = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return str(self.dt)+ " Dev_ID : " + str(self.devId)+" Température : " + str(self.Temp)

class DeviceData(models.Model):
    device_name = models.CharField(max_length=100)
    temp_ds = models.FloatField()         # Température DS
    hum_sht = models.FloatField()         # Humidité SHT
    temp_sht = models.FloatField()        # Température SHT
    battery_voltage = models.FloatField() # Tension Batterie

    timestamp = models.DateTimeField(auto_now_add=True)  # pour garder la date de réception

    def __str__(self):
        return f"{self.device_name} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

###############greenhouse###############
class greenHouse(models.Model):
    Soil_Humidity = models.FloatField(null=True)
    Rain_Drop = models.FloatField(null=True)
    Rain_Drop_Sensor_State = models.CharField(max_length=100, null=True, blank=True)
    Time_Stamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Soil_Humidity: {self.Soil_Humidity} , Rain_Drop: {self.Rain_Drop}, Rain_Drop_Sensor_State: {self.Rain_Drop_Sensor_State},Time: {self.Time_Stamp}"

##############Makerfabs#############
class Makerfabs(models.Model):
    batt = models.FloatField(null=True)
    valve = models.FloatField(null=True)
    Volume = models.FloatField(null=True)
    debit = models.FloatField(null=True)
    durée= models.FloatField(null=True)
    #Rain_Drop_Sensor_State = models.CharField(max_length=100, null=True, blank=True)
    Time_Stamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"batt: {self.batt} , valve: {self.valve}, Volume: {self.Volume}, debit: {self.debit}, durée: {self.durée},Time: {self.Time_Stamp}"

class PyraRS485(models.Model):
    Irradiance  = models.FloatField(null=True, blank=True)   # W/m²
    Batterie    = models.FloatField(null=True, blank=True)   # Volts
    Power_Status = models.IntegerField(null=True, blank=True) # 0 ou 1
    DateRay     = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"RS485 | {self.DateRay} | {self.Irradiance} W/m²"


class SenseCAPT1000(models.Model):
    Battery         = models.FloatField(null=True, blank=True)   # %
    Light           = models.FloatField(null=True, blank=True)   # %
    Temperature     = models.FloatField(null=True, blank=True)   # °C
    Latitude        = models.FloatField(null=True, blank=True)   # degrés
    Longitude       = models.FloatField(null=True, blank=True)   # degrés
    Positing_Status = models.IntegerField(null=True, blank=True) # 0=indoor 1=outdoor
    Indoor_Outdoor  = models.CharField(max_length=10, null=True, blank=True)  # 'Indoor' ou 'Outdoor'
    Time_Stamp      = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.Time_Stamp} | Bat:{self.Battery}% | Light:{self.Light}%"





class SensorData(models.Model):
    temperature = models.FloatField()
    humidity    = models.FloatField()
    timestamp   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Temp={self.temperature}°C | Hum={self.humidity}% | {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

class WeatherData(models.Model):
    wind_speed_ms = models.FloatField()          # vitesse du vent en m/s
    wind_speed_kmh = models.FloatField()         # vitesse du vent en km/h
    wind_dir_deg = models.FloatField()           # direction en degrés
    wind_dir_card = models.CharField(max_length=10)  # direction cardinale (ENE, N, etc.)

    humidity_pct = models.FloatField()           # humidité en %
    temperature_c = models.FloatField()          # température en °C

    rain_mm = models.FloatField()                # pluie en mm
    movement = models.BooleanField()             # mouvement détecté (True/False)

    created_at = models.DateTimeField(auto_now_add=True)  # date d'enregistrement

    def __str__(self):
        return f"WeatherData {self.created_at} - {self.temperature_c}°C"




class Data3(models.Model):
    """Modèle pour la station Davis (payload ChirpStack)"""
    devEui          = models.CharField(max_length=50, default="70b3d58f8000062d")
    temperature_c   = models.FloatField(null=True, blank=True)
    humidity_pct    = models.FloatField(null=True, blank=True)
    wind_speed_ms   = models.FloatField(null=True, blank=True)
    wind_speed_kmh  = models.FloatField(null=True, blank=True)
    wind_dir_deg    = models.FloatField(null=True, blank=True)
    wind_dir_card   = models.CharField(max_length=10, null=True, blank=True)
    rain_mm         = models.FloatField(null=True, blank=True)
    movement        = models.BooleanField(default=False)
    rssi            = models.IntegerField(null=True, blank=True)
    snr             = models.FloatField(null=True, blank=True)
    Time_Stamp      = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-Time_Stamp']

    def __str__(self):
        return (f"Davis | {self.Time_Stamp} | "
                f"T={self.temperature_c}°C H={self.humidity_pct}% "
                f"Wind={self.wind_speed_kmh}km/h Rain={self.rain_mm}mm")


####--Système d'alertes--####

# models.py — Ajouter ce nouveau modèle

from django.utils import timezone
#from datetime import timedelta

class Device(models.Model):
    DEVICE_TYPES = [
        ('lorawan', 'LoRaWAN'),
        ('cellular', 'Cellulaire'),
    ]

    name        = models.CharField(max_length=100)
    devEui      = models.CharField(max_length=50, unique=True)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES, default='lorawan')
    description = models.CharField(max_length=200, null=True, blank=True)
    last_seen   = models.DateTimeField(null=True, blank=True)

    # Seuil en minutes avant de considérer le device comme silencieux
    alert_threshold = models.IntegerField(default=30)

    def status(self):
        """Retourne le statut du device selon last_seen"""
        if not self.last_seen:
            return 'unknown'
        delta = timezone.now() - self.last_seen
        if delta < timedelta(minutes=self.alert_threshold):
            return 'online'       # ✅ Vert
        elif delta < timedelta(minutes=self.alert_threshold * 2):
            return 'warning'      # ⚠️ Orange
        else:
            return 'offline'      # ❌ Rouge

    def status_label(self):
        labels = {
            'online': 'En ligne',
            'warning': 'En retard',
            'offline': 'Hors ligne',
            'unknown': 'Inconnu',
        }
        return labels.get(self.status(), 'Inconnu')

    def __str__(self):
        return f"{self.name} ({self.devEui})"
