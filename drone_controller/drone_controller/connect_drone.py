#!/usr/bin/env python3
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
        # Simülasyona bağlan (Varsayılan port 14540)
        # Eğer gerçek bir cihaz ise "serial:///dev/ttyUSB0:57600" gibi bir adres kullanılır
        print("Drone'a bağlanılıyor...")
        await self.drone.connect(system_address="udp://:14540")

        # Bağlantı durumunu kontrol et
        async for state in self.drone.core.connection_state():
            if state.is_connected:
                print(f"Bağlantı Başarılı! Cihaz ID: {state}")
                break # Bağlantı kurulduğu an döngüden çık

        print("İşlem tamamlandı, bağlantı aktif.")

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
