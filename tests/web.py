import network
import socket

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

if wlan.isconnected():
    print("IP de la Raspberry Pico W:", wlan.ifconfig()[0])
else:
    print("No está conectada a una red WiFi.")
    
def web_page():
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Pulso Manual</title>
</head>
<body>
    <h1>Sensor de Pulso</h1>
    <form action="/" method="GET">
        <input type="number" name="pulso" placeholder="Pulso (bpm)">
        <input type="submit" value="Enviar">
    </form>
</body>
</html>"""
    return html

addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)

print('Servidor corriendo. Abre esta dirección en tu navegador:')
print('http://' + '192.168.135.195')  

while True:
    conn, addr = s.accept()
    print('Cliente conectado desde:', addr)
    request = conn.recv(1024)
    request = str(request)

    pulso = 0
    if '/?pulso=' in request:
        try:
            pulso = int(request.split('/?pulso=')[1].split(' ')[0])
            print("Pulso recibido:", pulso)

            # Simular acción según el pulso
            if pulso < 60:
                print("Estado: Relajado (bajo)")
            elif 60 <= pulso <= 100:
                print("Estado: Normal")
            else:
                print("Estado: Activo (alto)")
        except:
            print("Error al leer el pulso")

    response = web_page()
    conn.send('HTTP/1.1 200 OK\n')
    conn.send('Content-Type: text/html\n')
    conn.send('Connection: close\n\n')
    conn.sendall(response)
    conn.close()