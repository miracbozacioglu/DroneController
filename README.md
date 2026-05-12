# ros2_ws / src

Bu repo bir ROS 2 workspace'inin `src/` dizinidir. PX4 SITL üzerinde MAVSDK ile çalışan ROS 2 (Python) paketleri içerir.

## Paketler

- **[`drone_controller/`](drone_controller/)** — MAVSDK tabanlı drone görevleri (bağlantı testi, kalkış/iniş, 8 deseni waypoint görevi).

---

## drone_controller

Her görev kendi node'unu (`DroneController`) ayağa kaldırır, ROS 2 spin döngüsünü ayrı bir thread'de çalıştırır ve drone kontrolünü `asyncio` ile yürütür. Böylece ROS 2 yaşam döngüsü ile MAVSDK'nın async API'si birbirini engellemeden bir arada çalışır.

## İçerik

Paket, dört adet bağımsız çalıştırılabilir görev içerir:

| Komut | Dosya | Ne yapar |
|---|---|---|
| `connect_drone` | `connect_drone.py` | UDP 14540 üzerinden bağlantıyı kurar ve sağlık kontrolü yapar. Sistemi denemek için en hızlı yol. |
| `my_drone` | `my_drone.py` | Arm → 50 m'ye kalkış → 5 sn havada bekleme → iniş → disarm. Uçtan uca temel görev. |
| `sekiz_cizme` | `sekiz_cizme.py` | Mevcut konuma göre hesaplanan waypoint'lerle yatay düzlemde "8" deseni çizer. 20 m irtifada, 40 m yarıçaplı iki halka. Görev sonunda RTL açıktır. |
| `default` | `default.py` | Yeni görevler için iskelet/şablon dosya. `run_mission` boş; üstüne yeni senaryo yazılır. |

## Mimari

Her dosya aynı kalıbı izler:

```
main() → asyncio.run(main_async())
                ├── rclpy.init()
                ├── DroneController(Node) instance
                ├── threading.Thread(target=rclpy.spin)   # ROS 2 arka planda
                └── await node.run_mission()              # MAVSDK işleri ön planda
```

Bu yapı sayesinde:
- ROS 2 callback'leri (publisher/subscriber/service eklendiğinde) bloklanmadan çalışır.
- MAVSDK `async for` döngüleri (`telemetry.position`, `mission_progress` vb.) `asyncio` event loop'unda doğal şekilde tüketilir.
- Görev mantığını değiştirmek için sadece `DroneController.run_mission` metodunu düzenlemek yeterlidir.

## Bağımlılıklar

- ROS 2 (Humble veya üzeri, `rclpy`)
- Python 3.10+
- [`mavsdk`](https://pypi.org/project/mavsdk/) (`python3-mavsdk` ya da `pip install mavsdk`)
- PX4 SITL veya MAVLink üzerinden erişilebilen bir araç

`package.xml` içinde `rclpy`, `std_msgs` ve `python3-mavsdk` bildirilmiştir.

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

> `mavsdk` rosdep tarafından bulunamazsa `pip install mavsdk` yeterlidir.

## Çalıştırma

Ayrı bir terminalde PX4 SITL'i başlatın (örn. `make px4_sitl gz_x500`). Ardından:

```bash
# Bağlantı testi
ros2 run drone_controller connect_drone

# Kalkış / bekle / iniş senaryosu
ros2 run drone_controller my_drone

# 8 deseni
ros2 run drone_controller sekiz_cizme
```

Tüm görevler varsayılan olarak `udp://:14540` veya `udpin://0.0.0.0:14540` adresini dinler. Gerçek bir telemetri kullanılacaksa ilgili dosyadaki `system_address` parametresi `serial:///dev/ttyUSB0:57600` gibi bir değerle değiştirilir.

## Yeni Görev Eklemek

1. `drone_controller/default.py`'i kopyalayın → `drone_controller/<yeni_gorev>.py`.
2. `DroneController.run_mission` içine MAVSDK akışınızı yazın.
3. `setup.py` içindeki `console_scripts` listesine yeni satırı ekleyin:
   ```python
   '<yeni_gorev> = drone_controller.<yeni_gorev>:main',
   ```
4. `colcon build --packages-select drone_controller && source install/setup.bash`.
5. `ros2 run drone_controller <yeni_gorev>` ile çalıştırın.

## Güvenlik Notları

- `my_drone.py` ve `sekiz_cizme.py` **arm** + **takeoff** çağırır. Gerçek bir araçla denemeden önce mutlaka SITL'de doğrulayın.
- `sekiz_cizme.py` görev sonunda `set_return_to_launch_after_mission(True)` ile RTL'i etkinleştirir.
- Görev sırasında `Ctrl+C`, `KeyboardInterrupt` yakalanır ve node temiz şekilde kapatılır; ancak bu **drone'u durdurmaz** — fiziksel güvenlik için RC failsafe veya GCS'den manuel müdahale şarttır.


