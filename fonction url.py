from django.urls import path

from application import views, api
from . import views

from .views import (
    # pm101, pm103, pm107, pm1015,
    # pm1, pm3, pm7, pm15,
    # pm251, pm253, pm257, pm2515,
    # co1, co3, co7, co15,
    # tvoc1, tvoc3, tvoc7, tvoc15,
    # no21, no23, no27, no215,
    # tempv1, tempv3, tempv7, tempv15,
    # humv1, humv3, humv7, humv15,
    # batv1, batv3, batv7, batv15,
    # co2v1, co2v3, co2v7, co2v15,
    # ch2ov1, ch2ov3, ch2ov7, ch2ov15,
    # o31, o33, o37, o315,
    data_filter,data_filter_hum, data_filter_ws,data_filter_pl,data_filter_ry,
    data_filter_et0,send_command,compare_sensors,debit_data,capsol_filter,filter_light_intensity,filter_uv_index,et0_view,green_house,batt_vannes,et0_FAO56_view,capteursol_filter,capteursol,makerFabs_ev,pyra_rs485
)

urlpatterns = [
    path('', views.home,name="home"),
    path("send_command/", send_command, name="send_command"),
    path("compare/",compare_sensors,name="compare"),
    # path('Chart/', views.chart,name="chart"),
    # path('Charthum/', views.charthum,name="charthum"),
    path('backfill-et0/', views.backfill_et0, name='backfill_et0'),
    # path('Chartbat/', views.chartbat, name="chartbat"),
    path('data/', views.weatherS,name="data"),
    path('wso/', views.wsopen,name="wso"),
    path('wso1/', views.wsopen1,name="wso1"),
    path('etjob/', views.et0_job,name="etjob"),
    path('etjob1/', views.et0_job1,name="etjob1"),
    path('fwijob/', views.fwijob,name="fwijob"),
    path('env/', views.wsopen1,name="env"),
    path('tab/', views.aqi,name="tab"),
    path('datasc/', views.export_hourly_averages_since_25june_csv, name='datasc'),
    path('datasol/', views.export_capsol2_csv, name='datasol'),
    path('datadr/', views.export_hourly_averages_wsd_et0dr_csv, name='datadr'),
    path('lht65n/',views.lht65,name="lht65n"),
    path('et0_comp/',et0_view,name="et0_comp"),
    path('et0_FAO56/',et0_FAO56_view,name="et0_FAO56"),########
    path('fwi/', views.fwi0, name="fwi"),
    path('download-2025/', views.download_temp_ray_2025, name='download_2025'),
##api
    path('api/list', api.Dlist, name='DHT11List'),

    # genericViews
    path('api/post', api.Dataviews.as_view(), name='WS_post'),
    path('api/post_ws', api.Dataviews2.as_view(), name='WSo_post'),

    path('davis/', views.davis_uplink, name='davis_uplink'),
    path('comparaison/', views.comparaison, name='comparaison'),


    path('api/post1', api.ETviews.as_view(), name='ET_post'),
    path('api/post2', api.FWIviews.as_view(), name='FWI_post'),
    path('api/post_ray', api.Rayviews.as_view(), name='Ray_post'),
    path('api/post4', api.Envdataviews.as_view(), name='Env_post'),
    path('api/post5', api.Cwsiviews.as_view(), name='cwsi_post'),
    path('gprs/', views.gprs_receive, name='gprs_receive'),


    path('cwsi/',views.cwsi_data,name="cwsi"),

    path('tvoc1/', data_filter_ws, name='tvoc1'),
    path('tvoc3/', data_filter_pl, name='tvoc3'),
    path('light/', filter_light_intensity, name='light'),
    path('cap_sol/', capsol_filter, name='tvoc7'),
    path('cap_sol_calibration/', capteursol, name='cap_sol_calibration'),#######
    path('bat-filter/', views.filter_ray_battery, name='bat_filter'),
    # path('pyra-rs485/', views.pyra_rs485, name='pyra_rs485'),
    path('uv/', filter_uv_index, name='uv'),
    path('rayonnement-rs485/', views.data_filter_ry_rs485, name='rayonnement_rs485'),
    path('comparaison-rayonnement/', views.comparaison_rayonnement, name='comparaison_rayonnement'),
    path('sensecap-t1000/', views.sensecap_t1000_view, name='sensecap_t1000'),
    path('tempv1/', data_filter, name='tempv1'),
    path('tempv3/', data_filter_ry, name='tempv3'),

    path('humv1/', data_filter_hum, name='humv1'),

    path('humv15/', data_filter_et0, name='humv15'),

    path('debit/', debit_data, name='debit'),
    path('batterie_EV/', batt_vannes, name='batterie_EV'),
    path('makerfabs/', makerFabs_ev, name='makerfabs'),


    path('greenhouse/', green_house, name='greenhouse'),


    # chirpstack integration
    path('chirpstack/', views.v_chirpstack, name='chirpstack'),
    path('export/greenhouse/', views.export_greenhouse_to_excel, name='export_greenhouse_excel'),

    path('supervision/', views.device_status, name='device_status'),



    # path('no21/', no21, name='no21'),
    # path('no23/', no23, name='no23'),
    # path('no27/', no27, name='no27'),
    # path('no215/', no215, name='no215'),
    # path('Chartsal/', views.chartsal, name="chartsal"), Quand vous modifiez merci de terminer la programmation views puis url puis le fichier html pour ne pas stopper l'application.
    # path('Chartec/', views.chartec, name="chartec"),
    # path('Chartn/', views.chartn, name="chartn"),
    # path('Chartp/', views.chartp, name="chartp"),
    # path('Chartk/', views.chartk, name="chartk"),
    # path('wind-rose-data/', wind_rose_data, name='wind_rose_data'),
    # path('tvoc15/', tvoc15, name='tvoc15'),
    ## path('tempv7/', tempv7, name='tempv7'),
    # path('tempv15/', tempv15, name='tempv15'),
    # path('humv3/', humv3, name='humv3'),
    # path('humv7/', humv7, name='humv7'),
    # path('ntacc/', views.tempv1, name="ntacc"),
    # path('ntacc3/', views.tempv3, name="ntacc3"),
    # path('nbacc1/', views.tempv3, name="nbacc1"),
    # path('nchacc/', views.bsol7, name="nchacc"),
    # path('nc2acc/', views.bsol15, name="nc2acc"),
    # path('n1acc/', views.bsol7, name="n1acc"),
    # path('n25acc/', views.bsol15, name="n25acc"),
    # path('n10acc/', views.bsol7, name="n10acc"),
    # path('nhacc/', views.bsol15, name="nhacc"),
    # # path('n1acc/', views.bsol7, name="n1acc"),
    # # path('n25acc/', views.bsol15, name="n25acc"),

    # path('pm101/', pm101, name='pm101'),
    # path('pm103/', pm103, name='pm103'),
    # path('pm107/', pm107, name='pm107'),
    # path('pm1015/', pm1015, name='pm1015'),
    # path('pm1/', pm1, name='pm1'),
    # path('pm3/', pm3, name='pm3'),
    # path('pm7/', pm7, name='pm7'),
    # path('pm15/', pm15, name='pm15'),
    # path('pm251/', pm251, name='pm251'),
    # path('pm253/', pm253, name='pm253'),
    # path('pm257/', pm257, name='pm257'),
    # path('pm2515/', pm2515, name='pm2515'),
    # path('co1/', co1, name='co1'),
    # path('co3/', co3, name='co3'),
    # path('co7/', co7, name='co7'),
    # path('co15/', co15, name='co15'),
    # path('batv1/', batv1, name='batv1'),
    # path('batv3/', batv3, name='batv3'),
    # path('batv7/', batv7, name='batv7'),
    # path('batv15/', batv15, name='batv15'),
    # path('co2v1/', co2v1, name='co2v1'),
    # path('co2v3/', co2v3, name='co2v3'),
    # path('co2v7/', co2v7, name='co2v7'),
    # path('co2v15/', co2v15, name='co2v15'),
    # path('ch2ov1/', ch2ov1, name='ch2ov1'),
    # path('ch2ov3/', ch2ov3, name='ch2ov3'),
    # path('ch2ov7/', ch2ov7, name='ch2ov7'),
    # path('ch2ov15/', ch2ov15, name='ch2ov15'),
    # path('o31/', o31, name='o31'),
    # path('o33/', o33, name='o33'),
    # path('o37/', o37, name='o37'),
    # path('o315/', o315, name='o315'),
    # path('test0/',views.mych,"test"),
#Temperature charts
    # path('24h/', views.dash,name="acc"),
    # path('3jrs/', views.data3,name="3jracc"),
    # path('7jrs/', views.data7,name="7jracc"),
    # path('15jrs/', views.data15,name="15jracc"),
    # ##humidité
    # path('h24h/', views.hum1,name="hacc"),
    # path('h3jrs/', views.hum3,name="h3jracc"),
    # path('h7jrs/', views.hum7,name="h7jracc"),
    # path('h15jrs/', views.hum15,name="h15jracc"),
    # ##vitesse
    # path('v24h/', views.vit1,name="vacc"),
    # path('v3jrs/', views.vit3,name="v3jracc"),
    # path('v7jrs/', views.vit7,name="v7jracc"),
    # path('v15jrs/', views.vit15,name="v15jracc"),

    # #rayonnement
    # path('r24h/', views.ray1,name="racc"),
    # path('r3jrs/', views.ray3,name="r3jracc"),
    # path('r7jrs/', views.ray7,name="r7jracc"),
    # path('r15jrs/', views.ray15,name="r15jracc"),

    # #pluvieu
    # path('p24h/', views.plu1,name="pacc"),
    # path('p3jrs/', views.plu3,name="p3jracc"),
    # path('p7jrs/', views.plu7,name="p7jracc"),
    # path('p15jrs/', views.plu15,name="p15jracc"),

    # #batterie
    # path('b24h/', views.bat1,name="bacc"),
    # path('b3jrs/', views.bat3,name="b3jracc"),
    # path('b7jrs/', views.bat7,name="b7jracc"),
    # path('b15jrs/', views.bat15,name="b15jracc"),

    # #batterie
    # path('b241h/', views.bat11,name="bacc1"),
    # path('b31jrs/', views.bat31,name="b3jracc1"),
    # path('b71jrs/', views.bat71,name="b7jracc1"),
    # path('b151jrs/', views.bat151,name="b15jracc1"),

    # #et0
    # path('et/', views.et,name="et"),
    # path('et0/', views.et0,name="et0"),

    #fwi


]
