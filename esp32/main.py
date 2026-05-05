"""
main.py — nfc_reader_demo entry point

LCD   : I2C (scl=14, sda=13) — same wiring as hanna_light
NFC   : MFRC522 over SPI (sck=18, mosi=23, miso=19, cs=5, rst=2)
BUZZER: passive buzzer on GPIO 27 (PWM)
"""

import urequests
import wifi
from config import SSID, PASSWORD
from machine import SoftSPI, I2C, Pin, PWM
from time import sleep_ms
from mfrc522 import MFRC522
from I2C_LCD import I2cLcd

# brief LED test — 100 ms only, then off
green_led = Pin(22, Pin.OUT)
red_led = Pin(4, Pin.OUT)

i2c = I2C(0, scl=Pin(14), sda=Pin(13), freq=400000)
devices = i2c.scan()
if len(devices) == 0:
    print("No i2c device !")
else:
    for device in devices:
        print("I2C addr: "+hex(device))
        lcd = I2cLcd(i2c, device, 2, 16)

# --- NFC reader ---
spi = SoftSPI(baudrate=1000000, polarity=0, phase=0,
              sck=Pin(18), mosi=Pin(23), miso=Pin(19))
cs  = Pin(5, Pin.OUT)
rst = Pin(2, Pin.OUT)
rdr = MFRC522(spi, cs, rst)

buzzer = PWM(Pin(27), freq=1000, duty=0)

def beep(freq=2000, duration_ms=150):
    buzzer.freq(freq)
    buzzer.duty(512)
    sleep_ms(duration_ms)
    buzzer.duty(0)

def beep_success():
    beep(2000, 150)
    sleep_ms(100)
    for _ in range(3):
        beep(2500, 80)
        sleep_ms(80)

def beep_denied():
    beep(800, 150)
    sleep_ms(50)
    beep(400, 300)

def play_mario():
    E, Q = 150, 300  # eighth, quarter at ~200 BPM
    notes = [
        (659,E),(0,E),(659,E),(0,E),(659,E),(0,E),(523,E),(659,Q),(784,Q),(0,Q),(392,Q),
    ]
    for freq, dur in notes:
        if freq:
            beep(freq, dur)
        else:
            sleep_ms(dur)
        sleep_ms(10)

def connect_wifi():
    lcd.clear()
    lcd.putstr("Connecting WiFi")
    wifi.connect(SSID, PASSWORD)
    lcd.clear()
    lcd.putstr("WiFi OK")
    sleep_ms(1000)

def get_balance(card_uid_hex):
    try:
        res = urequests.get("https://cash-register.slimmii.workers.dev/" + card_uid_hex, timeout=5)
        data = res.json()
        res.close()
        return data
    except Exception as e:
        print("Balance error:", e)
        return None

def checkout(card_uid_hex, product_ids):
    lcd.clear()
    lcd.putstr("Processing...")
    try:
        url = "https://cash-register.slimmii.workers.dev/sales"
        payload = {"card_id": card_uid_hex, "product_ids": product_ids}
        res = urequests.post(url, json=payload, timeout=5)
        data = res.json()
        res.close()
        return data
    except Exception as e:
        print("Checkout error:", e)
        return None

def load_data(silent=False):
    # Products: {uid_int: (label, price)} — tuple value cheaper than nested dict
    if not silent:
        lcd.clear()
        lcd.putstr("Loading prods")
    products = {}
    try:
        res = urequests.get("https://cash-register.slimmii.workers.dev/products", timeout=10)
        for p in res.json():
            label = p.get("label", p["product_id"]).upper()
            products[int(p["product_id"], 16)] = (label, p["price"])
        res.close()
    except Exception as e:
        print("Products error:", e)

    # Cards: set of ints — membership-only, no value needed
    if not silent:
        lcd.move_to(0, 1)
        lcd.putstr("Loading cards ")
    cards = set()
    try:
        res = urequests.get("https://cash-register.slimmii.workers.dev/cards", timeout=10)
        for c in res.json():
            cards.add(int(c, 16))
        res.close()
    except Exception as e:
        print("Cards error:", e)

    # Admin cards: unlock/lock the register
    admin_cards = set()
    try:
        res = urequests.get("https://cash-register.slimmii.workers.dev/cards?admin=1", timeout=10)
        for c in res.json():
            admin_cards.add(int(c, 16))
        res.close()
    except Exception as e:
        print("Admin cards error:", e)

    print("Products:", len(products), "Cards:", len(cards), "Admins:", len(admin_cards))
    return products, cards, admin_cards

play_mario()
connect_wifi()
PRODUCTS, CARDS, ADMIN_CARDS = load_data()

basket_total = 0
basket_products = []
locked = True

lcd.clear()
lcd.putstr("** LOCKED **")

while True:
    (stat, tag_type) = rdr.request(rdr.REQIDL)
    if stat == rdr.OK:
        (stat, raw_uid) = rdr.anticoll()
        if stat == rdr.OK:
            uid_hex = "%02x%02x%02x%02x" % (raw_uid[0], raw_uid[1], raw_uid[2], raw_uid[3])
            uid_int = (raw_uid[0] << 24) | (raw_uid[1] << 16) | (raw_uid[2] << 8) | raw_uid[3]
            print("UID:", uid_hex)

            if uid_int in ADMIN_CARDS:
                beep()
                if locked:
                    locked = False
                    lcd.clear()
                    lcd.putstr("** UNLOCKED **")
                    lcd.move_to(0, 1)
                    lcd.putstr("TOTAL: 0")
                    for _ in range(3):
                        green_led.value(1)
                        sleep_ms(100)
                        green_led.value(0)
                        sleep_ms(100)
                else:
                    locked = True
                    basket_total = 0
                    basket_products = []
                    lcd.clear()
                    lcd.putstr("** LOCKED **")
                sleep_ms(1500)
            elif locked:
                for _ in range(3):
                    red_led.value(1)
                    sleep_ms(100)
                    red_led.value(0)
                    sleep_ms(100)
                beep_denied()
                PRODUCTS, CARDS, ADMIN_CARDS = load_data(silent=True)
            elif uid_int in CARDS:
                beep()
                if not basket_products:
                    data = get_balance(uid_hex)
                    lcd.clear()
                    if data and data.get("balance") is not None:
                        lcd.putstr(str(data.get("name", ""))[:16])
                        lcd.move_to(0, 1)
                        lcd.putstr(("BAL: " + str(data["balance"]))[:16])
                    else:
                        lcd.putstr("Balance error")
                    sleep_ms(3000)
                    lcd.clear()
                    lcd.putstr("** UNLOCKED **")
                    lcd.move_to(0, 1)
                    lcd.putstr("TOTAL: 0")
                else:
                    data = checkout(uid_hex, basket_products)
                    lcd.clear()
                    if data and "error" in data:
                        lcd.putstr(data["error"][:16])
                        sleep_ms(3000)
                        basket_total = 0
                        basket_products = []
                        lcd.clear()
                        lcd.move_to(0, 1)
                        lcd.putstr("TOTAL: 0")
                    elif data:
                        beep_success()
                        basket_total = 0
                        basket_products = []
                        lcd.putstr(("PAID: " + str(data.get("total", "?")))[:16])
                        bal = get_balance(uid_hex)
                        sleep_ms(2000)
                        lcd.clear()
                        if bal and bal.get("balance") is not None:
                            lcd.putstr(str(bal.get("name", ""))[:16])
                            lcd.move_to(0, 1)
                            lcd.putstr(("BAL: " + str(bal["balance"]))[:16])
                        sleep_ms(3000)
                        lcd.clear()
                        lcd.putstr("** UNLOCKED **")
                        lcd.move_to(0, 1)
                        lcd.putstr("TOTAL: 0")
                    else:
                        basket_total = 0
                        basket_products = []
                        lcd.putstr("Payment failed")
            elif uid_int in PRODUCTS:
                beep()
                label, price = PRODUCTS[uid_int]
                basket_total += price
                basket_products.append(uid_hex)
                lcd.clear()
                lcd.putstr("%-13s%3d" % (label[:13], price))
                lcd.move_to(0, 1)
                lcd.putstr(("TOTAL: " + str(basket_total))[:16])
            else:
                beep()
                lcd.clear()
                lcd.putstr("UNKNOWN")
                lcd.move_to(0, 1)
                lcd.putstr(uid_hex[:16])
    sleep_ms(100)
