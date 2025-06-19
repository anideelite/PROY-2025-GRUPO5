import network
import socket
import urequests
import time

ssid = 'smms'
password = '23102006'

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

max_wait = 10
while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    print('waiting for connection...')
    time.sleep(1)
    max_wait -= 1

if wlan.status() != 3:
    raise RuntimeError('network connection failed')
print('connected. IP:', wlan.ifconfig()[0])

def web_page():
    return """<!DOCTYPE html>
<html><head><title>Pulso Manual</title></head>
<body>
<h1>Sensor de Pulso</h1>
<form action="/" method="GET">
<input type="number" name="pulso" placeholder="Pulso (bpm)">
<input type="submit" value="Enviar">
</form>
</body></html>"""

s = socket.socket()
try:
    s.bind(('0.0.0.0', 80))
    s.listen(1)
    s.settimeout(5)

    while True:
        try:
            conn, addr = s.accept()
            conn.settimeout(5)
            print('Cliente desde:', addr)
            request = conn.recv(1024).decode()

            pulso = 0
            if '/?pulso=' in request:
                try:
                    pulso = int(request.split('/?pulso=')[1].split(' ')[0])
                    print("Pulso:", pulso)
                    try:
                        response = urequests.post(
                            "https://musicpicker-server.onrender.com/play",
                            json={"bpm": pulso}
                        )
                        print("Respuesta:", response.text)
                        response.close()
                    except Exception as e:
                        print("Error HTTP:", e)
                except Exception as e:
                    print("Error al parsear pulso:", e)

            response = web_page()
            conn.send('HTTP/1.1 200 OK\nContent-Type: text/html\nConnection: close\n\n')
            conn.sendall(response.encode())
            conn.close()

        except OSError as e:
            print("Timeout o error de conexión:", e)

except Exception as e:
    print("Error en servidor:", e)
finally:
    print("Cerrando socket")
    s.close()