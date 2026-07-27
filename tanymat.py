from gevent import monkey
monkey.patch_all()

from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Estado inicial de ambos en la ciudad (coordenadas de ejemplo y datos por defecto)
# Puedes cambiar las coordenadas base al centro de tu ciudad
usuarios = {
    "El": {"lat": -31.3833, "lon": -57.9667, "texto": "Hola amor ❤️", "estado": "😊 Feliz", "rol": "El"},
    "Ella": {"lat": -31.3850, "lon": -57.9650, "texto": "Holaaa ✨", "estado": "💖 Te extraño", "rol": "Ella"}
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Nuestro GPS Privado 🗺️</title>
    <!-- Leaflet CSS para el mapa -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { margin: 0; padding: 0; font-family: sans-serif; background: #121212; color: white; display: flex; flex-direction: column; height: 100vh; }
        #map { flex-grow: 1; width: 100%; z-index: 1; }
        .panel { background: #1e1e1e; padding: 12px; display: flex; flex-direction: column; gap: 8px; z-index: 10; box-shadow: 0 -4px 10px rgba(0,0,0,0.5); }
        .controls { display: flex; gap: 5px; overflow-x: auto; padding-bottom: 5px; }
        button { background: #333; color: white; border: 1px solid #555; padding: 8px 12px; border-radius: 8px; font-size: 14px; white-space: nowrap; cursor: pointer; }
        button:active { background: #ff0055; }
        .input-group { display: flex; gap: 8px; }
        input[type="text"] { flex-grow: 1; padding: 10px; border-radius: 8px; border: 1px solid #555; background: #2a2a2a; color: white; font-size: 16px; }
        .selector-rol { display: flex; justify-content: center; gap: 10px; margin-bottom: 5px; }
        .selector-rol button { background: #444; font-weight: bold; }
        .selector-rol button.activo { background: #00ffcc; color: black; }
    </style>
</head>
<body>

    <div class="panel">
        <div class="selector-rol">
            <span style="align-self: center; font-size: 14px;">¿Quién eres?:</span>
            <button id="btnEl" onclick="cambiarRol('El')">Él 👦</button>
            <button id="btnElla" onclick="cambiarRol('Ella')">Ella 👧</button>
        </div>

        <div class="input-group">
            <input type="text" id="mensajeInput" placeholder="Escribe lo que estás haciendo...">
            <button onclick="enviarTexto()" style="background: #00cc66; font-weight: bold;">Enviar</button>
        </div>

        <div class="controls">
            <button onclick="enviarEstado('❤️ Enamorado/a')">❤️ Enamorado/a</button>
            <button onclick="enviarEstado('☕ Tomando café')">☕ Café</button>
            <button onclick="enviarEstado('🍕 Comiendo')">🍕 Comiendo</button>
            <button onclick="enviarEstado('🥱 Cansado/a')">🥱 Cansado</button>
            <button onclick="enviarEstado('🚀 A las corridas')">🚀 Corriendo</button>
        </div>
    </div>

    <div id="map"></div>

    <!-- Leaflet JS -->
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.5.4/socket.io.min.js"></script>
    <script>
        const socket = io({
            transports: ['polling']
        });
        let miRol = "El"; // Por defecto

        function cambiarRol(rol) {
            miRol = rol;
            document.getElementById("btnEl").classList.toggle("activo", rol === "El");
            document.getElementById("btnElla").classList.toggle("activo", rol === "Ella");
        }
        cambiarRol("El");

        // Inicializar mapa centrado
        const map = L.map('map').setView([-31.3833, -57.9667], 14);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
        }).addTo(map);

        let marcadores = {};

        socket.on('actualizar_mapa', function(data) {
            for (let id in data) {
                let usr = data[id];
                let contenidoPopup = `<b>${usr.rol}</b><br>Estado: ${usr.estado}<br>💬 "${usr.texto}"`;

                if (marcadores[id]) {
                    marcadores[id].setLatLng([usr.lat, usr.lon]);
                    marcadores[id].getPopup().setContent(contenidoPopup);
                } else {
                    let marker = L.marker([usr.lat, usr.lon]).addTo(map)
                        .bindPopup(contenidoPopup);
                    marcadores[id] = marker;
                }
            }
        });

        function enviarTexto() {
            let txt = document.getElementById("mensajeInput").value;
            if(!txt) return;
            socket.emit('actualizar_datos', { rol: miRol, tipo: 'texto', valor: txt });
            document.getElementById("mensajeInput").value = "";
        }

        function enviarEstado(est) {
            socket.emit('actualizar_datos', { rol: miRol, tipo: 'estado', valor: est });
        }

        // Permitir mover el marcador propio haciendo click en el mapa para simular GPS
        map.on('click', function(e) {
            socket.emit('actualizar_datos', { rol: miRol, tipo: 'ubicacion', lat: e.latlng.lat, lon: e.latlng.lng });
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@socketio.on('actualizar_datos')
def handle_data(data):
    rol = data['rol']
    if rol in usuarios:
        if data['tipo'] == 'texto':
            usuarios[rol]['texto'] = data['valor']
        elif data['tipo'] == 'estado':
            usuarios[rol]['estado'] = data['valor']
        elif data['tipo'] == 'ubicacion':
            usuarios[rol]['lat'] = data['lat']
            usuarios[rol]['lon'] = data['lon']
        
        # Transmitir a ambos teléfonos al instante
        emit('actualizar_mapa', usuarios, broadcast=True)

if __name__ == '__main__':
    # Escucha en la red local para que ambos se conecten por IP
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
