# dashboard_integrado.py
import customtkinter as ctk
import threading
import queue
import time
import datetime
import socket
import numpy as np
import librosa
from tensorflow.keras.models import load_model
import pyaudio
import noisereduce as nr
import scipy.signal as signal
import os

class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent, triangulation_scanner=None):
        super().__init__(parent)
        self.triangulation_scanner = triangulation_scanner
        self.configure(fg_color="#2b2b2b")
        self.cola_datos = queue.Queue()
        self.ejecutando = True
        self.max_historial = 10
        self.modo_simulacion = False
        
        self.colores = ["#4CAF50", "#9C27B0", "#2196F3"]
        self.color_conectado = "#00BFA5"
        self.color_desconectado = "#F44336"
        self.color_fondo = "#2b2b2b"
        self.color_marco = "#333333"
        self.color_marco_claro = "#383851"
        self.color_texto_claro = "#E0E0E0"
        self.color_texto_secundario = "#B0B0B0"
        self.color_acento = "#5D87FF"
        self.color_fondo_oscuro = "#1a1a1a"
        
        self.SAMPLE_RATE = 22050
        self.CHUNK_SIZE = 256
        self.DURATION = 4
        self.BUFFER_SIZE = int(self.SAMPLE_RATE * self.DURATION)
        
        self.ESP32_DEVICES = [
            {'ip': '192.168.1.101', 'port': 8081, 'name': 'ESP32_1', 'id': 0},
            {'ip': '192.168.1.102', 'port': 8082, 'name': 'ESP32_2', 'id': 1},
            {'ip': '192.168.1.103', 'port': 8083, 'name': 'ESP32_3', 'id': 2}
        ]
        self.device_warning_count = {device['name']: 0 for device in self.ESP32_DEVICES}
        self.device_max_warnings = 10  # Límite de advertencias antes de desactivar
        self.device_auto_disabled = {device['name']: False for device in self.ESP32_DEVICES}  # Nuevo atributo
    
        self.cargar_modelo()
        
        self.device_queues = {device['name']: queue.Queue() for device in self.ESP32_DEVICES}
        self.device_buffers = {device['name']: [] for device in self.ESP32_DEVICES}
        self.device_status = {device['name']: False for device in self.ESP32_DEVICES}
        self.device_warning_count = {device['name']: 0 for device in self.ESP32_DEVICES}
        self.device_threads = {device['name']: None for device in self.ESP32_DEVICES}
        self.processing_threads = {device['name']: None for device in self.ESP32_DEVICES}
        
        self.sensores_activos = [1, 1, 1]
        self.inicializar_interfaz()
        self.iniciar_hilos()

    def cargar_modelo(self):
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(script_dir, 'GunshotIaModel_v9_old.h5')
            self.model = load_model(model_path)
            print("[MODELO] Modelo cargado exitosamente")
        except Exception as e:
            print(f"[MODELO] Error al cargar modelo: {e}")
            self.model = None
            self.modo_simulacion = True

    def inicializar_interfaz(self):
        self.marcos_sensores = []
        self.indicadores_conexion = []
        self.etiquetas_estado = []
        self.etiquetas_tiempo_real = []
        self.etiquetas_ultima_recepcion = []
        self.tiempo_ultima_recepcion = [None, None, None]
        self.historial_datos = [[], [], []]
        self.cajas_texto = []

        self.crear_encabezado()
        
        self.marco_sensores = ctk.CTkFrame(self, fg_color="transparent")
        self.marco_sensores.pack(fill="both", expand=True, padx=10, pady=10)
        self.marco_sensores.grid_rowconfigure(0, weight=1)

        for i in range(3):
            self.marco_sensores.grid_columnconfigure(i, weight=1)
            self.crear_seccion_sensor(i)

    def crear_encabezado(self):
        marco_encabezado = ctk.CTkFrame(self, fg_color=self.color_marco)
        marco_encabezado.pack(fill="x", pady=(0,0), padx=0)
        
        contenedor_interno = ctk.CTkFrame(marco_encabezado, fg_color="transparent")
        contenedor_interno.pack(fill="x", padx=20, pady=15)

        titulo = ctk.CTkLabel(
            contenedor_interno, 
            text="SISTEMA DE MONITOREO Y ALERTA DE DISPAROS",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=self.color_acento
        )
        titulo.pack(pady=(0, 5))
        
        modo_texto = "Modo: SIMULACIÓN" if self.modo_simulacion else "Modo: ESP32 REAL"
        self.boton_modo = ctk.CTkButton(
            contenedor_interno,
            text=modo_texto,
            command=self.cambiar_modo,
            fg_color=self.color_acento
        )
        self.boton_modo.pack(pady=(0, 5))
        
        fecha_actual = datetime.datetime.now().strftime("%d/%m/%Y")
        ctk.CTkLabel(
            contenedor_interno,
            text=f"Fecha: {fecha_actual}",
            font=ctk.CTkFont(size=12),
            text_color=self.color_texto_secundario
        ).pack()

    def crear_seccion_sensor(self, indice):
        marco_sensor = ctk.CTkFrame(
            self.marco_sensores,
            corner_radius=15,
            border_width=2,
            fg_color=self.color_fondo_oscuro,
            border_color=self.colores[indice]
        )
        marco_sensor.grid(row=0, column=indice, padx=10, pady=10, sticky="nsew")
        self.marcos_sensores.append(marco_sensor)
        
        marco_sensor.grid_rowconfigure(2, weight=1)
        marco_sensor.grid_columnconfigure(0, weight=1)
        
        marco_cabecera = ctk.CTkFrame(marco_sensor, fg_color=self.color_marco_claro, corner_radius=10)
        marco_cabecera.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        ctk.CTkLabel(
            marco_cabecera, 
            text=f"SENSOR {indice + 1}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colores[indice]
        ).pack(pady=5)
        
        marco_tiempo = ctk.CTkFrame(marco_cabecera, fg_color=self.color_marco, corner_radius=8)
        marco_tiempo.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(
            marco_tiempo,
            text="TIEMPO:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.color_texto_secundario
        ).pack(side="left", padx=10, pady=5)
        
        etiqueta_tiempo = ctk.CTkLabel(
            marco_tiempo,
            text="00:00:00",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colores[indice]
        )
        etiqueta_tiempo.pack(side="right", padx=10, pady=5)
        self.etiquetas_tiempo_real.append(etiqueta_tiempo)
        
        marco_estado = ctk.CTkFrame(marco_sensor, fg_color=self.color_marco_claro, corner_radius=10)
        marco_estado.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        
        fila_estado = ctk.CTkFrame(marco_estado, fg_color="transparent")
        fila_estado.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            fila_estado, 
            text="ESTADO:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.color_texto_secundario
        ).pack(side="left", padx=10, pady=5)
        
        indicador = ctk.CTkFrame(
            fila_estado,
            width=20,
            height=20,
            corner_radius=10,
            fg_color=self.color_desconectado
        )
        indicador.pack(side="left", padx=5)
        self.indicadores_conexion.append(indicador)
        
        etiqueta_estado = ctk.CTkLabel(
            fila_estado, 
            text="Desconectado",
            font=ctk.CTkFont(size=14),
            text_color=self.color_texto_claro
        )
        etiqueta_estado.pack(side="left", padx=5)
        self.etiquetas_estado.append(etiqueta_estado)
        
        fila_recepcion = ctk.CTkFrame(marco_estado, fg_color="transparent")
        fila_recepcion.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            fila_recepcion, 
            text="ÚLTIMA RECEPCIÓN:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.color_texto_secundario
        ).pack(side="left", padx=10, pady=5)
        
        etiqueta_recepcion = ctk.CTkLabel(
            fila_recepcion, 
            text="--:--:--",
            font=ctk.CTkFont(size=14),
            text_color=self.colores[indice]
        )
        etiqueta_recepcion.pack(side="left", padx=5)
        self.etiquetas_ultima_recepcion.append(etiqueta_recepcion)
        
        marco_historial = ctk.CTkFrame(marco_sensor, fg_color=self.color_marco_claro, corner_radius=10)
        marco_historial.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        
        marco_historial.grid_rowconfigure(0, weight=1)
        marco_historial.grid_columnconfigure(0, weight=1)
        
        caja_texto = ctk.CTkTextbox(
            marco_historial,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#1a1a1a",
            text_color=self.color_texto_claro
        )
        caja_texto.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.cajas_texto.append(caja_texto)
        caja_texto.insert("1.0", "Esperando datos...\n")

    def cambiar_modo(self):
        self.modo_simulacion = not self.modo_simulacion
        modo_texto = "Modo: SIMULACIÓN" if self.modo_simulacion else "Modo: ESP32 REAL"
        self.boton_modo.configure(text=modo_texto)
        
        self.detener_conexiones_esp32()
        for device_name in self.device_auto_disabled:
            self.device_auto_disabled[device_name] = False
        
        for device_name in self.device_warning_count:
            self.device_warning_count[device_name] = 0

        for i in range(3):
            self.historial_datos[i].clear()
            self.cajas_texto[i].delete("1.0", "end")
        
        if not self.modo_simulacion:
            print("[MODO] Cambiando a modo ESP32 REAL")
            for i in range(3):
                self.indicadores_conexion[i].configure(fg_color=self.color_desconectado)
                self.etiquetas_estado[i].configure(text="Conectando...")
                self.etiquetas_ultima_recepcion[i].configure(text="--:--:--")
                self.cajas_texto[i].insert("1.0", "Intentando conectar...\n")
            
            threading.Thread(target=self.iniciar_conexiones_esp32, daemon=True).start()
            
            if not hasattr(self, 'hilo_monitoreo') or not self.hilo_monitoreo.is_alive():
                self.hilo_monitoreo = threading.Thread(target=self.monitorear_conexiones_esp32, daemon=True)
                self.hilo_monitoreo.start()
        else:
            print("[MODO] Cambiando a modo SIMULACIÓN")
            for i in range(3):
                self.indicadores_conexion[i].configure(fg_color=self.color_acento)
                self.etiquetas_estado[i].configure(text="Simulando")
                self.cajas_texto[i].insert("1.0", "Iniciando simulación...\n")
            
            if not hasattr(self, 'hilo_simulacion') or not self.hilo_simulacion.is_alive():
                self.hilo_simulacion = threading.Thread(target=self.generar_datos_simulados, daemon=True)
                self.hilo_simulacion.start()

    def monitorear_conexiones_esp32(self):
        while self.ejecutando and not self.modo_simulacion:
            try:
                for i, device in enumerate(self.ESP32_DEVICES):
                    device_name = device['name']
                    
                    if self.device_status[device_name]:
                        self.indicadores_conexion[i].configure(fg_color=self.color_conectado)
                        self.etiquetas_estado[i].configure(text="Conectado")
                        
                        if self.triangulation_scanner:
                            self.triangulation_scanner.set_sensor_status_from_code(i, 1)
                    else:
                        self.indicadores_conexion[i].configure(fg_color=self.color_desconectado)
                        self.etiquetas_estado[i].configure(text="Desconectado")
                        
                        if self.triangulation_scanner:
                            self.triangulation_scanner.set_sensor_status_from_code(i, 0)
                
                time.sleep(1)
                
            except Exception as e:
                print(f"[MONITOREO] Error: {e}")
                time.sleep(1)

    def iniciar_hilos(self):
        self.hilo_actualizacion = threading.Thread(target=self.actualizar_datos, daemon=True)
        self.hilo_actualizacion.start()
        
        self.hilo_tiempo = threading.Thread(target=self.actualizar_tiempo_real, daemon=True)
        self.hilo_tiempo.start()
        
        if self.modo_simulacion:
            self.hilo_simulacion = threading.Thread(target=self.generar_datos_simulados, daemon=True)
            self.hilo_simulacion.start()

    def iniciar_conexiones_esp32(self):
        print("[CONEXIONES] Iniciando conexiones ESP32...")
        
        for device_name in self.device_status:
            self.device_status[device_name] = False
            self.device_warning_count[device_name] = 0
        
        for device_name in self.device_queues:
            while not self.device_queues[device_name].empty():
                try:
                    self.device_queues[device_name].get_nowait()
                except queue.Empty:
                    break
        
        for device_name in self.device_buffers:
            self.device_buffers[device_name].clear()
        
        for device in self.ESP32_DEVICES:
            device_name = device['name']
            
            capture_thread = threading.Thread(
                target=self.record_audio_from_wifi,
                args=(device['ip'], device['port'], device_name),
                daemon=True
            )
            self.device_threads[device_name] = capture_thread
            capture_thread.start()
            
            processing_thread = threading.Thread(
                target=self.process_audio,
                args=(device_name,),
                daemon=True
            )
            self.processing_threads[device_name] = processing_thread
            processing_thread.start()
            
            time.sleep(0.2)

    def detener_conexiones_esp32(self):
        print("[CONEXIONES] Deteniendo conexiones ESP32...")
        
        for device_name in self.device_status:
            self.device_status[device_name] = False
            
        for device_name in self.device_queues:
            while not self.device_queues[device_name].empty():
                try:
                    self.device_queues[device_name].get_nowait()
                except queue.Empty:
                    break
                    
        for device_name in self.device_buffers:
            self.device_buffers[device_name].clear()
        
        time.sleep(0.5)

    def record_audio_from_wifi(self, esp32_ip, port, device_name):
        print(f"[CAPTURA][{device_name}] Conectando a {esp32_ip}:{port}...")
        
        while self.ejecutando and not self.modo_simulacion and not self.device_auto_disabled[device_name]:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(10)
            
            try:
                client_socket.connect((esp32_ip, port))
                print(f"[CAPTURA][{device_name}] Conexión exitosa.")
                self.device_status[device_name] = True
                self.device_warning_count[device_name] = 0
                
                client_socket.settimeout(None)
                
                while (self.ejecutando and not self.modo_simulacion and 
                    self.device_status[device_name] and not self.device_auto_disabled[device_name]):
                    try:
                        raw_data = client_socket.recv(self.CHUNK_SIZE * 2)
                        if raw_data:
                            chunk = np.frombuffer(raw_data, dtype=np.int16)
                            self.device_queues[device_name].put(chunk)
                        else:
                            print(f"[CAPTURA][{device_name}] Conexión cerrada por el servidor.")
                            break
                    except socket.timeout:
                        print(f"[CAPTURA][{device_name}] Timeout en recepción.")
                        break
                    except Exception as e:
                        print(f"[CAPTURA][{device_name}] Error en recepción: {e}")
                        break
                        
            except Exception as e:
                print(f"[CAPTURA][{device_name}] Error de conexión: {e}")
            finally:
                client_socket.close()
                self.device_status[device_name] = False
                
            if self.ejecutando and not self.modo_simulacion and not self.device_auto_disabled[device_name]:
                print(f"[CAPTURA][{device_name}] Reintentando en 5 segundos...")
                time.sleep(5)

    def noise_reduction(self, audio, sample_rate, prop_decrease=0.9):
        try:
            noise_clip = audio[:int(0.5 * sample_rate)]
            reduced_noise = nr.reduce_noise(
                y=audio,
                sr=sample_rate,
                y_noise=noise_clip,
                prop_decrease=prop_decrease
            )
            return reduced_noise
        except:
            return audio

    def filter_weiner(self, y, sr):
        try:
            longitud_ventana = int(2 * sr)
            solapamiento = int(longitud_ventana / 50)
            señal_procesada = np.zeros_like(y)
            paso = longitud_ventana - solapamiento

            for i in range(0, len(y) - longitud_ventana + 1, paso):
                segmento = y[i:i + longitud_ventana]
                segmento_limpio = signal.wiener(segmento, mysize=8000)
                ventana = np.hanning(longitud_ventana)
                segmento_limpio = segmento_limpio * ventana
                señal_procesada[i:i + longitud_ventana] += segmento_limpio

            y_wiener = señal_procesada / np.max(np.abs(señal_procesada))
            sos = signal.butter(10, [2, 7500], btype='bandpass', fs=sr, output='sos')
            y_wiener_filtered = signal.sosfilt(sos, y_wiener)
            return y_wiener_filtered
        except:
            return y

    def process_audio(self, device_name):
        print(f"[PROCESAMIENTO][{device_name}] Iniciando...")
        c = 0
        
        while self.ejecutando and not self.modo_simulacion:
            try:
                if not self.device_status[device_name] or self.device_auto_disabled[device_name]:
                    time.sleep(1)
                    continue
                    
                chunk = self.device_queues[device_name].get(timeout=2)
                self.device_buffers[device_name].extend(chunk)
                self.device_warning_count[device_name] = 0
                
                if len(self.device_buffers[device_name]) >= self.BUFFER_SIZE:
                    audio_segment = np.array(self.device_buffers[device_name][:self.BUFFER_SIZE], dtype=np.float32)
                    self.device_buffers[device_name] = self.device_buffers[device_name][self.BUFFER_SIZE:]
                    
                    if np.max(np.abs(audio_segment)) > 0:
                        audio_segment /= np.max(np.abs(audio_segment))
                    
                    c += 1
                    if c >= 5:
                        audio_segment = self.noise_reduction(audio_segment, self.SAMPLE_RATE)
                        audio_segment = self.filter_weiner(audio_segment, self.SAMPLE_RATE)
                        c = 0
                    
                    if self.model:
                        spectrogram = self.generate_spectrogram(audio_segment)
                        prob = self.predict_gunshot(spectrogram)
                        
                        sensor_id = None
                        for device in self.ESP32_DEVICES:
                            if device['name'] == device_name:
                                sensor_id = device['id']
                                break
                        
                        if sensor_id is not None:
                            self.cola_datos.put({
                                "id_sensor": sensor_id,
                                "probabilidad_disparo": prob,
                                "fuente": "ESP32",
                                "nivel_audio": np.max(np.abs(audio_segment)),
                                "datos_recibidos": len(chunk)
                            })
                            
                        print(f"[PROCESAMIENTO][{device_name}] Probabilidad: {prob:.2f}, Nivel: {np.max(np.abs(audio_segment)):.3f}")
                        if prob > 0.5:
                            print(f"[PROCESAMIENTO][{device_name}] ¡Disparo detectado!")
                    else:
                        sensor_id = None
                        for device in self.ESP32_DEVICES:
                            if device['name'] == device_name:
                                sensor_id = device['id']
                                break
                        
                        if sensor_id is not None:
                            self.cola_datos.put({
                                "id_sensor": sensor_id,
                                "probabilidad_disparo": 0.0,
                                "fuente": "ESP32",
                                "nivel_audio": np.max(np.abs(audio_segment)),
                                "datos_recibidos": len(chunk),
                                "sin_modelo": True
                            })
                            
            except queue.Empty:
                self.device_warning_count[device_name] += 1
                
                if self.device_warning_count[device_name] >= self.device_max_warnings:
                    print(f"[PROCESAMIENTO][{device_name}] Máximo de advertencias alcanzado. Desactivando sensor.")
                    self.device_auto_disabled[device_name] = True
                    self.device_status[device_name] = False
                    
                    # Actualizar la interfaz para mostrar el estado desactivado
                    sensor_id = None
                    for i, device in enumerate(self.ESP32_DEVICES):
                        if device['name'] == device_name:
                            sensor_id = i
                            break
                    
                    if sensor_id is not None:
                        self.sensores_activos[sensor_id] = 0
                        # Programar actualización de la interfaz en el hilo principal
                        self.after(0, lambda: self.actualizar_interfaz_sensor_desactivado(sensor_id))
                    
                    break  # Salir del bucle de procesamiento
                else:
                    print(f"[PROCESAMIENTO][{device_name}] Sin datos - verificando conexión... ({self.device_warning_count[device_name]}/{self.device_max_warnings})")
                continue
            except Exception as e:
                print(f"[PROCESAMIENTO][{device_name}] Error: {e}")
                time.sleep(1)

    def generate_spectrogram(self, audio):
        try:
            spect = librosa.stft(audio)
            spect_db = librosa.amplitude_to_db(np.abs(spect), ref=np.max)
            return np.expand_dims(spect_db, axis=-1)
        except:
            return np.zeros((1025, 345, 1))

    def predict_gunshot(self, spectrogram):
        try:
            spectrogram = np.expand_dims(spectrogram, axis=0)
            return self.model.predict(spectrogram)[0][0]
        except:
            return 0.0

    def actualizar_tiempo_real(self):
        while self.ejecutando:
            tiempo_str = datetime.datetime.now().strftime("%H:%M:%S")
            for etiqueta in self.etiquetas_tiempo_real:
                etiqueta.configure(text=tiempo_str)
            time.sleep(1)

    def generar_datos_simulados(self):
        import random
        while self.ejecutando and self.modo_simulacion:
            sensor_id = random.randint(0, 2)
            probabilidad = random.uniform(0, 1)
            self.cola_datos.put({
                "id_sensor": sensor_id,
                "probabilidad_disparo": probabilidad,
                "fuente": "SIMULACIÓN"
            })
            time.sleep(random.uniform(0.5, 2))

    def actualizar_datos(self):
        while self.ejecutando:
            try:
                if not self.cola_datos.empty():
                    datos = self.cola_datos.get()
                    sensor_id = datos["id_sensor"]
                    
                    if self.sensores_activos[sensor_id]:
                        if self.modo_simulacion:
                            self.indicadores_conexion[sensor_id].configure(fg_color=self.color_acento)
                            self.etiquetas_estado[sensor_id].configure(text="Simulando")
                        
                        if self.triangulation_scanner:
                            probabilidad = datos["probabilidad_disparo"]
                            if probabilidad > 0.7:
                                self.triangulation_scanner.set_sensor_status_from_code(sensor_id, 2)
                            else:
                                self.triangulation_scanner.set_sensor_status_from_code(sensor_id, 1)
                        
                        tiempo_str = datetime.datetime.now().strftime("%H:%M:%S")
                        self.etiquetas_ultima_recepcion[sensor_id].configure(text=tiempo_str)
                        
                        mensaje = self.generar_mensaje_historial(datos, tiempo_str)
                        self.actualizar_historial(sensor_id, mensaje)
                    else:
                        if self.triangulation_scanner:
                            self.triangulation_scanner.set_sensor_status_from_code(sensor_id, 0)
                    
                time.sleep(0.1)
            except Exception as e:
                print(f"[DASHBOARD] Error: {e}")

    def generar_mensaje_historial(self, datos, tiempo):
        probabilidad = datos["probabilidad_disparo"]
        fuente = datos.get("fuente", "DESCONOCIDO")
        nivel_audio = datos.get("nivel_audio", 0.0)
        datos_recibidos = datos.get("datos_recibidos", 0)
        sin_modelo = datos.get("sin_modelo", False)
        
        if sin_modelo:
            return f"[{tiempo}] 📡 Datos [{fuente}]: Nivel: {nivel_audio:.3f}, Bytes: {datos_recibidos} - Sin modelo\n"
        elif probabilidad > 0.7:
            return f"[{tiempo}] ‼️ ALERTA [{fuente}]: Prob: {probabilidad:.2f}, Nivel: {nivel_audio:.3f} - Disparo: SÍ\n"
        else:
            return f"[{tiempo}] ✓ Normal [{fuente}]: Prob: {probabilidad:.2f}, Nivel: {nivel_audio:.3f} - Disparo: NO\n"

    def actualizar_historial(self, sensor_id, mensaje):
        self.historial_datos[sensor_id].insert(0, mensaje)
        if len(self.historial_datos[sensor_id]) > self.max_historial:
            self.historial_datos[sensor_id].pop()
        
        self.cajas_texto[sensor_id].delete("1.0", "end")
        self.cajas_texto[sensor_id].insert("end", "\n".join(self.historial_datos[sensor_id]))

    # Nueva función para actualizar la interfaz cuando un sensor se desactiva
    def actualizar_interfaz_sensor_desactivado(self, sensor_id):
        """Actualiza la interfaz cuando un sensor se desactiva automáticamente"""
        self.indicadores_conexion[sensor_id].configure(fg_color="#FF6B6B")  # Color rojo especial
        self.etiquetas_estado[sensor_id].configure(text="Desactivado (Auto)")
        
        # Actualizar historial
        tiempo_str = datetime.datetime.now().strftime("%H:%M:%S")
        mensaje = f"[{tiempo_str}] ⚠️ SENSOR DESACTIVADO: Demasiados fallos de conexión\n"
        self.actualizar_historial(sensor_id, mensaje)
        
        # Notificar al triangulation_scanner si existe
        if self.triangulation_scanner:
            self.triangulation_scanner.set_sensor_status_from_code(sensor_id, 0)

    # Función monitorear_conexiones_esp32 modificada
    def monitorear_conexiones_esp32(self):
        while self.ejecutando and not self.modo_simulacion:
            try:
                for i, device in enumerate(self.ESP32_DEVICES):
                    device_name = device['name']
                    
                    if self.device_auto_disabled[device_name]:
                        # Sensor desactivado automáticamente
                        self.indicadores_conexion[i].configure(fg_color="#FF6B6B")
                        self.etiquetas_estado[i].configure(text="Desactivado (Auto)")
                        
                        if self.triangulation_scanner:
                            self.triangulation_scanner.set_sensor_status_from_code(i, 0)
                            
                    elif self.device_status[device_name]:
                        self.indicadores_conexion[i].configure(fg_color=self.color_conectado)
                        self.etiquetas_estado[i].configure(text="Conectado")
                        
                        if self.triangulation_scanner:
                            self.triangulation_scanner.set_sensor_status_from_code(i, 1)
                    else:
                        self.indicadores_conexion[i].configure(fg_color=self.color_desconectado)
                        self.etiquetas_estado[i].configure(text="Desconectado")
                        
                        if self.triangulation_scanner:
                            self.triangulation_scanner.set_sensor_status_from_code(i, 0)
                
                time.sleep(1)
                
            except Exception as e:
                print(f"[MONITOREO] Error: {e}")
                time.sleep(1)
   
    def cerrar_dashboard(self):
        self.ejecutando = False
        self.detener_conexiones_esp32()
        self.destroy()