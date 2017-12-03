import time
import binascii
import socket
import config
import devices
import machine
from devices import Devices
from network import LoRa


class LoraWorker:

    def __init__(self, devices):
        self.devices = devices
        self.lora = LoRa(mode=LoRa.LORAWAN)
        self.s = None

    def join(self):
        if self.s:
            self.s.close()
            self.s = None

        app_eui = binascii.unhexlify(config.LORA_APP_EUI)
        app_key = binascii.unhexlify(config.LORA_APP_KEY)

        print("Joining LoRaWAN network")

        self.lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key), timeout=0)
        count = 0
        connection_failed = False
        while not self.lora.has_joined():
            time.sleep(2.5)
            count += 3
            machine.wdt_feed()
            print('Not joined yet...')

            if count > config.LORA_JOIN_TIMEOUT_SEC:
                print("LoRaWAN join timeout")
                connection_failed = True
                break

        if connection_failed:
            raise Exception("LoRaWAN join failed")
        else:
            print("LoRaWAN join succeeded!")

    def _send(self, data):
        if self.lora.has_joined():
            if not self.s:
                self.s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
                self.s.setsockopt(socket.SOL_LORA, socket.SO_DR, config.LORA_DR)
                self.s.setsockopt(socket.SOL_LORA, socket.SO_CONFIRMED, False)
                self.s.setblocking(True)
            self.s.send(data)

    def remove_timeout(self):
        to_remove = []
        count = 0

        for info in self.devices.macs:
            if info['mac'] != devices.EMPTY_MAC:
                diff = int(time.time()) - info['ts']
                if info['type'] == Devices.BLUETOOTH:
                    timeout = config.BLUETOOTH_DEVICE_TIMEOUT_SEC
                else:
                    timeout = config.WIFI_DEVICE_TIMEOUT_SEC

                if diff > timeout:
                    if info['sent'] > 0:
                        to_remove.append(info)
                        count += 1
                        if count >= config.NBR_MACS_PER_LORA_PACKET:
                            break
                    else:
                        print("\n\nERROR: Trying to remove before being added!!!\n\n")

        machine.wdt_feed()
        if len(to_remove) > 0:
            self.__remove_macs(to_remove)

    def detect_new_mac(self):
        send_joins = []
        count = 0

        for info in self.devices.macs:
            if info['mac'] != devices.EMPTY_MAC and info['sent'] == 0:
                send_joins.append(info)
                count += 1
                if count >= config.NBR_MACS_PER_LORA_PACKET:
                    break

        machine.wdt_feed()
        if len(send_joins) > 0:
            try:
                self.__send_package(send_joins, 'in', True)
                for info in send_joins:
                    info['sent'] = time.time()
            except OSError:
                pass

    def __remove_macs(self, _list):
        try:
            self.__send_package(_list, 'out', False)
            for info in _list:
                diff = int(time.time()) - info['sent']
                print("Removing for inactivity: " + info['mac'] + " after " + str(diff) + " seconds")
                self.devices.remove_mac(info['mac'])
        except OSError:
            pass

    def __send_package(self, _list, action, skip):
        if not skip:
            payload = self.__build_payload(_list, action)
            self._send(payload)
            print("LoRaWAN sent!", action)
        else:
            time.sleep(0.25)

    def __build_payload(self, _list, action):
        data = bytearray()
        for info in _list:
            # 1 byte: A=WiFi, B=Bluetooth
            data += bytearray("A" if info['type'] == Devices.WIFI else "B")

            # 1 byte: 1=IN, 0=OUT
            action_byte = bytearray(1)
            if action == "in":
                action_byte[0] = 1

            data += action_byte

            # 6 bytes: mac address
            data += bytearray(binascii.unhexlify(info['mac']))

            device_type = "WiFi" if info['type'] == Devices.WIFI else "Bluetooth"
            print("Sending LoRa " + device_type + " " + action.upper() + " message for " + info['mac'] + "...")

        return data
