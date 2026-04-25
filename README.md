# openwheel_design

Formula Student araç tasarım ve analiz kütüphanesi.

## Kurulum

```bash
pip install openwheel_design
```

## Kullanım

### Python ile

```python
from openwheel_design import chassis, engine, suspension
from openwheel_design.aerodynamics import calculate_downforce
from openwheel_design.tires import check_tire_temperature

# Şasi ağırlık analizi
result = chassis.analyze_weight([(25.4, 1.6, 5000)], material="4130")
print(f"Ağırlık: {result['total_weight']:.2f} kg")

# Motor analizi
from openwheel_design.engine import analyze_performance
result = analyze_performance("Honda CBR600RR", vehicle_weight_kg=200)
print(f"Güç/Ağırlık: {result['power_to_weight']['kW_per_kg']:.3f} kW/kg")

# Downforce hesabı
downforce = calculate_downforce(CL=2.0, area_m2=1.2, speed_kmh=80)
print(f"Downforce: {downforce:.0f} N")
```

### CLI ile

```bash
# Şasi analizi
openwheel chassis analyze --tube-od 25.4 --wall 1.6 --length 5000

# Motor listesi
openwheel engine list --common

# FS uyumluluk kontrolü
openwheel fs-check --weight 200 --length 2000 --width 1150
```

## Modüller

| Modül | Açıklama |
|------|---------|
| chassis | Şasi tasarım, ağırlık, malzeme |
| engine | Motor veritabanı, performans analizi |
| suspension | Süspansiyon geometrisi, camber, Ackermann |
| brakes | Fren sistemi, bias, termal analiz |
| aerodynamics | Downforce, drag, kanat tasarımı |
| tires | Lastik sıcaklık, basınç, slip angle |
| dynamics | Yük transferi, understeer/oversteer |
| transmission | Vites oranları, diferansiyel |
| scoring | FSAE puanlama sistemi |
| fuel | Yakıt tüketimi |
| data_log | Telemetri, CAN parsing |
| lap_sim | Enerji hesabı, lap simülasyonu |
| reporting | Raporlama (MD, text, JSON) |
| ev_system | Elektrikli motor, batarya |

## Dokümantasyon

Detaylı dokümantasyon için: [https://openwheel.design/docs](https://openwheel.design/docs)

## Lisans

MIT License - Detaylı bilgi için LICENSE dosyasına bakınız.

## Katkıda Bulunma

Katkıda bulunmak için lütfen GitHub issues kullanınız.