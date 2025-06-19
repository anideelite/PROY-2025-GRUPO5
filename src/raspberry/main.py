from machine import Pin, I2C
import time
import urequests
import network
import gc

ssid = "ssms"            #sujeto a cambio
password = "98765432"    #sujeto a cambio

def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Conectando al WiFi...")
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            time.sleep(0.5)
    print("Conectado a WiFi:", wlan.ifconfig())

conectar_wifi()

MAX30100_ADDRESS = 0x57
REG_MODE_CONFIG = 0x06
REG_SPO2_CONFIG = 0x07
REG_LED_CONFIG = 0x09
REG_FIFO_DATA = 0x05

i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=400000)

def write_register(reg, value):
    i2c.writeto_mem(MAX30100_ADDRESS, reg, bytes([value]))

def read_register(reg, nbytes=1):
    return i2c.readfrom_mem(MAX30100_ADDRESS, reg, nbytes)

def max30100_init():
    write_register(REG_MODE_CONFIG, 0x00)
    write_register(REG_MODE_CONFIG, 0x03)
    write_register(REG_SPO2_CONFIG, 0x27)
    write_register(REG_LED_CONFIG, 0x24)

def read_fifo():
    data = read_register(REG_FIFO_DATA, 4)
    ir = (data[0] << 8) | data[1]
    red = (data[2] << 8) | data[3]
    return ir, red

def enviar_bpm_al_servidor(promedio):
    try:
        url = "https://musicpicker-server.onrender.com/bpm"
        headers = {'Content-Type': 'application/json'}
        data = {'bpm': promedio}

        print("Antes de enviar: Memoria libre:", gc.mem_free())
        response = urequests.post(url, json=data, headers=headers)
        print("✅ BPM enviado al servidor:", response.text)
        response.close()
    except Exception as e:
        print("❌ Error al enviar BPM:", e)
        print("⏳ Reintentando en 3 segundos...")
        time.sleep(3)
        try:
            response = urequests.post(url, json=data, headers=headers)
            print("✅ (Reintento) BPM enviado al servidor:", response.text)
            response.close()
        except Exception as e:
            print("❌ Falló también el reintento:", e)
    finally:
        gc.collect()
        print("Después de enviar: Memoria libre:", gc.mem_free())

max30100_init()

threshold = 13000
min_interval = 0.3
max_buffer_size = 100
timestamps = []
ir_buffer = []
bpm_list = []

print("Sensor funcionando...")

while True:
    try:
        ir, red = read_fifo()
        t = time.ticks_ms() / 1000
        ir_buffer.append((t, ir))

        if len(ir_buffer) > max_buffer_size:
            ir_buffer.pop(0)

        if len(ir_buffer) >= 3:
            t0, ir0 = ir_buffer[-3]
            t1, ir1 = ir_buffer[-2]
            t2, ir2 = ir_buffer[-1]

            if ir1 > ir0 and ir1 > ir2 and ir1 > threshold:
                if not timestamps or (t1 - timestamps[-1]) > min_interval:
                    timestamps.append(t1)

                    if len(timestamps) >= 2:
                        interval = timestamps[-1] - timestamps[-2]
                        bpm = 60 / interval

                        if 40 < bpm < 180:
                            bpm_list.append(bpm)
                            print(f"💓 BPM detectado: {bpm:.1f}")
                            
                        if len(bpm_list) == 10:
                            promedio = sum(bpm_list) / 10
                            print(f"\n📊 BPM promedio (10 muestras): {promedio:.1f}\n")
                            enviar_bpm_al_servidor(promedio)
                            bpm_list = []  

                        else:
                            print(f"(Descartado: {bpm:.1f} fuera de rango)")

        time.sleep(0.02)

    except Exception as e:
        print("⚠️ Error:", e)
        time.sleep(1)