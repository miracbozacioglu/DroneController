import rclpy
from rclpy.node import Node
from mavsdk import System
import asyncio
import threading

class DroneController(Node):
    def __init__(self):
        super().__init__('drone_controller')
        self.drone = System()

    async def run_mission(self):
        # --- BAĞLANTI ---
        self.get_logger().info("UDP üzerinden MAVLink bağlantısı bekleniyor...")
        await self.drone.connect(system_address="udp://:14540")
        
        async for state in self.drone.core.connection_state():
            if state.is_connected:
                self.get_logger().info("Bağlantı sağlandı!")
                break

        # --- GPS VE HOME KONTROLÜ ---
        self.get_logger().info("GPS ve Home pozisyonu kontrol ediliyor...")
        async for health in self.drone.telemetry.health():
            if health.is_global_position_ok and health.is_home_position_ok:
                self.get_logger().info("GPS ve Home konumu hazır.")
                break

        # --- KALKIŞ (50 METRE) ---
        hedef_irtifa = 50.0
        self.get_logger().info(f"Kalkış yapılıyor ({hedef_irtifa}m)...")
        await self.drone.action.set_takeoff_altitude(hedef_irtifa)
        await self.drone.action.arm()
        await self.drone.action.takeoff()

        # --- İRTİFA KONTROLÜ ---
        self.get_logger().info("Hedef irtifaya tırmanılıyor...")
        async for position in self.drone.telemetry.position():
            mevcut_irtifa = position.relative_altitude_m
            # Tolerans payı bırakarak döngüden çıkıyoruz
            if mevcut_irtifa >= (hedef_irtifa - 2.0): 
                self.get_logger().info(f"Hedef irtifaya ulaşıldı: {mevcut_irtifa:.1f}m")
                break
            # Not: İçeride sleep kullanmıyoruz, veriyi geldiği hızda tüketiyoruz.

        # --- BEKLEME ---
        self.get_logger().info("Havada 5 saniye bekleniyor...")
        await asyncio.sleep(5)

        # --- İNİŞ ---
        self.get_logger().info("Görev tamamlandı, inişe geçiliyor...")
        await self.drone.action.land()

        # --- GÜVENLİ KAPANIŞ (DISARM KONTROLÜ) ---
        self.get_logger().info("Yere inmesi ve motorların kapanması bekleniyor...")
        async for is_armed in self.drone.telemetry.armed():
            # Drone yere inip motorları kapattığında is_armed değeri False olur
            if not is_armed:
                self.get_logger().info("Drone başarıyla yere indi ve motorlar kapandı (Disarmed).")
                break

# ROS 2 Spin döngüsünü arka planda tutacak yardımcı fonksiyon
def ros_spin_thread(node):
    rclpy.spin(node)

async def main_async(args=None):
    rclpy.init(args=args)
    node = DroneController()

    spin_thread = threading.Thread(target=ros_spin_thread, args=(node,))
    spin_thread.start()

    try:
        await node.run_mission()
    except KeyboardInterrupt:
        node.get_logger().info("Kullanıcı tarafından görev iptal edildi.")
    finally:
        node.destroy_node()
        rclpy.shutdown()
        spin_thread.join()

def main(args=None):
    asyncio.run(main_async(args))

if __name__ == '__main__':
    main()