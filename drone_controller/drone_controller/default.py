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
        pass
        # Buraya yukarıdaki drone görev kodunu ekleyin (bağlantı, kalkış, irtifa kontrolü, bekleme, iniş, güvenli kapanış)

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