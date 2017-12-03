from devices import Devices
from network import WLAN
import config

class WiFiWorker:

    def __init__(self, devices):
        self.devices = devices
        print("Starting promiscuous mode")
        self.wlan = WLAN(mode=WLAN.PROMISCUOUS, channel=config.WIFI_SCAN_CHANNEL, antenna=config.WIFI_ANTENNA)

    def get_probe(self):
        while True:
            _mac = self.wlan.probe_mac()
            if _mac:
                self.devices.add_mac(_mac, Devices.WIFI)
            else:
                break
