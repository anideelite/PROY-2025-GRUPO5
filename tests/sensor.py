from machine import Pin, I2C
import time

MAX30100_ADDRESS = 0x57
REG_FIFO_DATA = 0x05

i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=400000)

def read_fifo():
    data = i2c.readfrom_mem(MAX30100_ADDRESS, REG_FIFO_DATA, 4)
    ir = (data[0] << 8) | data[1]
    red = (data[2] << 8) | data[3]
    return ir, red

threshold = 13000
min_interval = 0.6
max_buffer_size = 100
alpha = 0.2
bpm_avg = None
bpm_list = []

ir_buffer = []
timestamps = []

print("Coloca tu dedo sobre el sensor y manténlo quieto...")

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
                            if bpm_avg is None:
                                bpm_avg = bpm
                            else:
                                bpm_avg = alpha * bpm + (1 - alpha) * bpm_avg

                            print(f"💓 BPM filtrado: {bpm_avg:.1f}")

                            if len(bpm_list) >= 10:
                                promedio = sum(bpm_list[-10:]) / 10
                                print(f"📊 BPM promedio (últimos 10): {promedio:.1f}")
                        else:
                            print(f"(Descartado BPM fuera de rango: {bpm:.1f})")
                    else:
                        print("✔ Primer latido detectado...")
        time.sleep(0.03)
    except Exception as e:
        print("Error:", e)
        time.sleep(1)