import time
import board
import adafruit_dht
from PIL import Image, ImageDraw, ImageFont
import Adafruit_SSD1306
import spidev
import RPi.GPIO as GPIO
import sqlite3

db = sqlite3.connect("smart_greenhouse.db")
cursor = db.cursor()

# OLED konfiguracija
RST = None
disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST, i2c_address=0x3C)
disp.begin()
disp.clear()
disp.display()

width = disp.width
height = disp.height
image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)

# Font za prikaz
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 8)
except IOError:
    font = ImageFont.load_default()

# DHT11 konfiguracija
dhtDevice = adafruit_dht.DHT11(board.D17)

# Relej za pumpu
RELAY_PIN = 16
GPIO.setup(RELAY_PIN, GPIO.OUT)

# Ventilator
FAN_PIN = 23  # GPIO23 upravlja tranzistorom za ventilator
GPIO.setup(FAN_PIN, GPIO.OUT)
GPIO.output(FAN_PIN, GPIO.LOW)

# Konfiguracija senzora razine vode
WATER_SENSOR_PIN = 26
GPIO.setup(WATER_SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Konfiguracija ADC (MCP3008 za vlagu tla)
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1000000

CS_ADC = 22
GPIO.setup(CS_ADC, GPIO.OUT)

def ReadChannel3008(channel):
    GPIO.output(CS_ADC, GPIO.LOW)
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    GPIO.output(CS_ADC, GPIO.HIGH)
    return data

LOW_MOISTURE = 200
HIGH_MOISTURE = 500
TEMP_THRESHOLD = 22  # Temperatura iznad koje se ventilator pali

# Zadnje poznate vrednosti temperature i vlage
last_temperature_c = 20
last_humidity = 50
fan_running = False  # Status ventilatora
pump_running = False  # Status pumpe

try:
    while True:
        if GPIO.input(WATER_SENSOR_PIN) == GPIO.LOW:  
            draw.rectangle((0, 0, width, height), outline=0, fill=0)
            draw.text((0, 12), "Nema vode!", font=font, fill=255)
            GPIO.output(RELAY_PIN, GPIO.LOW)
            pump_running = False
            disp.image(image)
            disp.display()
            print("Nema vode")
        else:
            moisture = ReadChannel3008(0)

            if moisture < LOW_MOISTURE:  
                GPIO.output(RELAY_PIN, GPIO.HIGH)
                pump_running = True
                print("✅ Pumpa ukljucena")

                # Pumpa radi 8 sekundi bez blokiranja
                start_time = time.time()
                while time.time() - start_time < 8:
                    draw.rectangle((0, 0, width, height), outline=0, fill=0)
                    draw.text((0, 0), "Pumpa: UKLJUCENA", font=font, fill=255)
                    disp.image(image)
                    disp.display()
                    time.sleep(1)  

                GPIO.output(RELAY_PIN, GPIO.LOW)
                pump_running = False
                print("⏹️ Pumpa iskljucena")

            try:
                temperature_c = dhtDevice.temperature
                humidity = dhtDevice.humidity

                if temperature_c is not None:
                    last_temperature_c = temperature_c  

                if humidity is not None:
                    last_humidity = humidity  

                temp_hum_status = "Temp: {:.1f}C, Hum: {}%".format(last_temperature_c, last_humidity)
            except RuntimeError:
                temp_hum_status = "Temp: {:.1f}C, Hum: {}%".format(last_temperature_c, last_humidity)

            # **Ventilator kontrola**
            if last_temperature_c > TEMP_THRESHOLD and not fan_running:
                GPIO.output(FAN_PIN, GPIO.HIGH)
                fan_running = True
                fan_start_time = time.time()
                print("🌀 Ventilator uključen!")

            if fan_running and (time.time() - fan_start_time > 20):
                GPIO.output(FAN_PIN, GPIO.LOW)
                fan_running = False
                print("🛑 Ventilator isključen!")

            # **Formatiranje statusa ventilatora i pumpe u jednom redu**
            fan_status_text = "ON" if fan_running else "OFF"
            pump_status_text = "ON" if pump_running else "OFF"
            status_line = "Fan: {}  Pumpa: {}".format(fan_status_text, pump_status_text)

            # **Ažuriranje OLED ekrana**
            draw.rectangle((0, 0, width, height), outline=0, fill=0)
            draw.text((0, 0), temp_hum_status, font=font, fill=255)
            draw.text((0, 10), "Vlaga tla: {}".format(moisture), font=font, fill=255)
            draw.text((0, 20), status_line, font=font, fill=255)  # Ventilator i pumpa u istom redu

            disp.image(image)
            disp.display()

            # **Upisivanje podataka u bazu**
            sql = "INSERT INTO sensor_readings (moisture, temperature, humidity, water_level, timestamp) VALUES (?, ?, ?, ?, datetime('now'))"
            values = (moisture, last_temperature_c, last_humidity, 1 if GPIO.input(WATER_SENSOR_PIN) == GPIO.HIGH else 0)

            try:
                cursor.execute(sql, values)
                db.commit()
                print("✅ Podaci upisani u bazu:", values)
            except sqlite3.Error as e:
                print("❌ Greška pri upisu u bazu:", e)

        time.sleep(2)

except KeyboardInterrupt:
    print("\n⏹️ Prekid programa! Zatvaram bazu i oslobađam GPIO pinove...")
    db.close()
    GPIO.cleanup()
    spi.close()
    print("✅ Resursi oslobođeni. Program završen.")
