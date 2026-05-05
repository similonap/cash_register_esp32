"""
wifi.py — WiFi connection helper
"""

import network
import time
from config import WIFI_TIMEOUT_S


def connect(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        print("Already connected:", wlan.ifconfig()[0])
        return wlan

    print("Connecting to '{}' ".format(ssid), end="")
    wlan.connect(ssid, password)

    deadline = time.time() + WIFI_TIMEOUT_S
    while not wlan.isconnected():
        if time.time() > deadline:
            raise RuntimeError("WiFi connection timed out")
        print(".", end="")
        time.sleep(1)

    ip, _, gw, _ = wlan.ifconfig()
    print("\nConnected  IP={}  GW={}".format(ip, gw))
    return wlan
