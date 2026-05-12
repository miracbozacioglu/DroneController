<div align="center">

# DroneController

**ROS 2 + MAVSDK + PX4 SITL** üzerinde çalışan modüler bir drone görev paketi.

<br>

![ROS 2](https://img.shields.io/badge/ROS_2-Humble%2B-22314E?style=for-the-badge&logo=ros&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![MAVSDK](https://img.shields.io/badge/MAVSDK-Async-FF6F00?style=for-the-badge)
![PX4](https://img.shields.io/badge/PX4-SITL-00B4F1?style=for-the-badge)
![License](https://img.shields.io/badge/License-TBD-lightgrey?style=for-the-badge)

</div>

---

## Genel Bakış

**DroneController**, her görevi ayrı bir ROS 2 node'u (`DroneController`) altında çalıştıran; ROS 2 spin döngüsünü ayrı bir thread'de tutarken drone kontrolünü `asyncio` ile yürüten bir pakettir. Bu sayede ROS 2 yaşam döngüsü ve MAVSDK'nın async API'si birbirini engellemeden uyum içinde çalışır.

> İlk dakikadan itibaren çalışan **SITL üzerinde test edilebilir** bir iskelet sunar — yeni görev eklemek için tek bir dosya kopyalamak yeterlidir.

---

## Görevler

<table>
<thead>
<tr>
<th align="left">Komut</th>
<th align="left">Dosya</th>
<th align="left">Açıklama</th>
</tr>
</thead>
<tbody>
<tr>
<td><code>connect_drone</code></td>
<td><a href="drone_controller/drone_controller/connect_drone.py"><code>connect_drone.py</code></a></td>
<td>UDP 14540 üzerinden bağlantıyı kurar ve sağlık kontrolü yapar. Sistemi denemek için en hızlı yol.</td>
</tr>
<tr>
<td><code>my_drone</code></td>
<td><a href="drone_controller/drone_controller/my_drone.py"><code>my_drone.py</code></a></td>
<td>Arm → <b>50 m</b>'ye kalkış → 5 sn havada bekleme → iniş → disarm. Uçtan uca temel görev.</td>
</tr>
<tr>
<td><code>sekiz_cizme</code></td>
<td><a href="drone_controller/drone_controller/sekiz_cizme.py"><code>sekiz_cizme.py</code></a></td>
<td>Yatay düzlemde <b>"8" deseni</b> çizer. 20 m irtifa, 40 m yarıçap, iki halka. Sonunda RTL etkin.</td>
</tr>
<tr>
<td><code>default</code></td>
<td><a href="drone_controller/drone_controller/default.py"><code>default.py</code></a></td>
<td>Yeni görevler için <b>iskelet/şablon</b>. <code>run_mission</code> boştur; üstüne yeni senaryo yazılır.</td>
</tr>
</tbody>
</table>

---

## Mimari

Her görev dosyası birebir aynı yapıyı izler:

```text
main()
  └── asyncio.run( main_async() )
        ├── rclpy.init()
        ├── DroneController(Node)                ← ROS 2 node
        ├── threading.Thread( rclpy.spin )       ← ROS 2 callback'leri arka planda
        └── await node.run_mission()             ← MAVSDK görev mantığı ön planda
```

| Avantaj | Nasıl? |
|---|---|
| **Bloklanmayan ROS 2** | `rclpy.spin` ayrı bir thread'de döner; publisher/subscriber/service eklemek güvenli. |
| **Doğal async tüketim** | `telemetry.position`, `mission_progress` gibi `async for` akışları `asyncio` döngüsünde tüketilir. |
| **Düşük yazma maliyeti** | Yeni görev = sadece `run_mission` metodunu değiştirmek. |

---

## Bağımlılıklar

| Bileşen | Sürüm / Not |
|---|---|
| ROS 2 | Humble veya üzeri (`rclpy`) |
| Python | 3.10+ |
| [`mavsdk`](https://pypi.org/project/mavsdk/) | `python3-mavsdk` ya da `pip install mavsdk` |
| PX4 SITL | veya MAVLink üzerinden erişilebilen bir araç |

> `package.xml` içinde `rclpy`, `std_msgs` ve `python3-mavsdk` bağımlılıkları bildirilmiştir.

---

## Kurulum

Repo doğrudan workspace'in `src/` dizini olarak klonlanır:

```bash
mkdir -p ~/ros2_ws
cd ~/ros2_ws
git clone <repo-url> src

rosdep install --from-paths src --ignore-src -r -y
colcon build --packages-select drone_controller
source install/setup.bash
```

> **İpucu:** `mavsdk` rosdep tarafından bulunamazsa `pip install mavsdk` yeterlidir.

---

## Çalıştırma

Önce ayrı bir terminalde PX4 SITL'i başlatın:

```bash
make px4_sitl gz_x500
```

Ardından paketteki görevlerden birini çalıştırın:

```bash
# Bağlantı testi
ros2 run drone_controller connect_drone

# Kalkış / bekle / iniş senaryosu
ros2 run drone_controller my_drone

# 8 deseni
ros2 run drone_controller sekiz_cizme
```

> Tüm görevler varsayılan olarak `udp://:14540` veya `udpin://0.0.0.0:14540` adresini dinler.
> Gerçek bir araç kullanılacaksa ilgili dosyadaki `system_address` parametresi `serial:///dev/ttyUSB0:57600` gibi bir değerle değiştirilir.

---

## Yeni Görev Eklemek

<details>
<summary><b>Adım adım rehber</b> (genişletmek için tıkla)</summary>

<br>

**1.** Şablonu kopyalayın:
```bash
cp drone_controller/drone_controller/default.py \
   drone_controller/drone_controller/<yeni_gorev>.py
```

**2.** Yeni dosyadaki `DroneController.run_mission` içine MAVSDK akışınızı yazın.

**3.** `setup.py` içindeki `console_scripts` listesine yeni satırı ekleyin:
```python
'<yeni_gorev> = drone_controller.<yeni_gorev>:main',
```

**4.** Paketi yeniden derleyin:
```bash
colcon build --packages-select drone_controller
source install/setup.bash
```

**5.** Çalıştırın:
```bash
ros2 run drone_controller <yeni_gorev>
```

</details>

---

## Güvenlik Notları

> [!WARNING]
> `my_drone.py` ve `sekiz_cizme.py` **arm + takeoff** çağırır. Gerçek bir araçla denemeden önce mutlaka SITL'de doğrulayın.

> [!IMPORTANT]
> `sekiz_cizme.py` görev sonunda `set_return_to_launch_after_mission(True)` ile **RTL**'i etkinleştirir.

> [!CAUTION]
> Görev sırasında `Ctrl+C`, `KeyboardInterrupt` yakalanır ve node temiz şekilde kapatılır — ancak bu **drone'u durdurmaz**. Fiziksel güvenlik için RC failsafe veya GCS'den manuel müdahale şarttır.

---

## Proje Yapısı

```text
src/
├── .gitignore
├── README.md
└── drone_controller/
    ├── package.xml
    ├── setup.py
    ├── setup.cfg
    ├── resource/
    ├── test/
    └── drone_controller/
        ├── __init__.py
        ├── connect_drone.py    ← bağlantı testi
        ├── default.py          ← şablon
        ├── my_drone.py         ← kalkış / iniş
        └── sekiz_cizme.py      ← 8 deseni
```

---

