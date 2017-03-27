from network import Bluetooth
from devices import Devices

class BluetoothWorker:

    def __init__(self, devices):
        self.devices = devices
        self.bt = Bluetooth()
        if self.bt.isscanning():
            self.bt.stop_scan()
        self.bt.start_scan(-1)

    def get_adv(self):
        while True:
            adv = self.bt.get_adv()
            if adv:
                self.devices.add_mac(adv.mac, Devices.BLUETOOTH)
            else:
                break
