import time
import binascii

EMPTY_MAC = '000000000000'

class Devices:
    # types
    BLUETOOTH = 1
    WIFI = 2

    def __init__(self):
        self.macs = [{'type': 1, 'ts': 0, 'sent': 0, 'mac': EMPTY_MAC} for i in range(500)]
        self.count = 0

    def add_mac(self, mac, _type):
        mac = str(binascii.hexlify(mac), "utf-8")

        for m in self.macs:
            if m['mac'] == mac:
                m['ts'] = int(time.time())
                return

        # mac not found
        for m in self.macs:
            if m['mac'] == EMPTY_MAC:
                m['type'] = _type
                m['mac'] = mac
                m['ts'] = int(time.time())
                m['sent'] = 0
                self.count += 1
                print("MAC added, now at " + str(self.count))
                return
        print('Out of space')


    def remove_mac(self, mac):
        for m in self.macs:
            if m['mac'] == mac:
                m['mac'] = EMPTY_MAC
                self.count -= 1
                print("Mac removed, now " + str(self.count))
                break
