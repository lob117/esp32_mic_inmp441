import customtkinter as ctk
import tkinter as tk
import threading
import time
import datetime

class TriangulationScanner(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.configure(fg_color="transparent")  # Fondo transparente para integrarse con el tema
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.color_texto_claro = "#E0E0E0"  # Texto claro para contraste
        self.color_acento = "#5D87FF"  # Color de acento
        self.color_marco = "#333333"  # Marco oscuro
        self.color_texto_secundario = "#B0B0B0"  # Texto secundario
        self.sensor_status = [0, 0, 0]  # 0=inactivo, 1=activo, 2=disparo
        self.scanning = False
        self.scan_thread = None
        self.crear_encabezado()
        # Configuración de la grilla
        self.grid_spacing = 40  # Espacio entre líneas de la grilla
        self.grid_color = "#333333"  # Color de la grilla
        
        # Main frame container
        self.frame = ctk.CTkFrame(self)
        self.frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Canvas para dibujo
        self.canvas = tk.Canvas(self.frame, bg="#1a1a1a", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Panel de control (ya no necesario para las entradas de texto)
        # self.control_frame = ctk.CTkFrame(self.frame)
        # self.control_frame.pack(fill="x", padx=10, pady=10)
        
        # Configuración inicial de los sensores
        self.sensors = [
            {
                "x": 0, "y": 0, "color": "#ffffff", 
                "active_color": "#00ff00", "fire_color": "#ff0000",
                "name": "Sensor 1", "status": 0, "radius": 0, 
                "max_radius": 180, "speed": 3
            },
            {
                "x": 0, "y": 0, "color": "#ffffff", 
                "active_color": "#ff00ff", "fire_color": "#ff0000",
                "name": "Sensor 2", "status": 0, "radius": 0, 
                "max_radius": 180, "speed": 3
            },
            {
                "x": 0, "y": 0, "color": "#ffffff", 
                "active_color": "#0080ff", "fire_color": "#ff0000",
                "name": "Sensor 3", "status": 0, "radius": 0, 
                "max_radius": 180, "speed": 3
            }
        ]
        
        # Punto central
        self.center = {"x": 0, "y": 0}
        
        # Eliminado: Las entradas de estado ya no se crean
        # self.status_entries = []
        # for i, sensor in enumerate(self.sensors):
        #     label = ctk.CTkLabel(self.control_frame, text=f"{sensor['name']} Status:")
        #     label.pack(side="left", padx=(20 if i > 0 else 10), pady=10)
        #     
        #     entry = ctk.CTkEntry(self.control_frame, width=40, justify="center")
        #     entry.insert(0, "0")
        #     entry.bind("<Return>", lambda event, idx=i: self.update_sensor_status(idx))
        #     entry.pack(side="left", padx=5, pady=10)
        #     self.status_entries.append(entry)
        
        # Evento de redimensionamiento
        self.bind("<Configure>", self.update_layout)
        
        # Dibujar layout inicial
        self.after(100, self.update_layout)  # Pequeño retraso para asegurar que el canvas esté listo

    def update_layout(self, event=None):
        """Actualizar el layout al cambiar el tamaño"""
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width < 1300 and canvas_width > 1200:    
            canvas_width = 1700
            canvas_height= 900
        else:
            canvas_width = 1250
            canvas_height= 700        
        # Calcular el centro del canvas
        self.center = {"x": canvas_width // 2, "y": canvas_height // 2}

        # Ajustar el centro a la intersección de la grilla más cercana
        grid_x = round(self.center["x"] / self.grid_spacing) * self.grid_spacing
        grid_y = round(self.center["y"] / self.grid_spacing) * self.grid_spacing
        self.center = {"x": grid_x, "y": grid_y}

        # Calcular el radio para la disposición de los sensores
        radius = min(canvas_width, canvas_height) * 0.2

        # Ajustar el radio para que sea múltiplo del espaciado de la grilla
        radius = round(radius / self.grid_spacing) * self.grid_spacing
        if radius < self.grid_spacing:
            radius = self.grid_spacing * 2

        # Posiciones de los sensores en triángulo (alineados a la grilla)
        # Sensor 1 (arriba)
        self.sensors[0]["x"] = self.center["x"]
        self.sensors[0]["y"] = self.center["y"] - (radius+20)
        self._snap_to_grid(0)  # Ajustar a la grilla

        radius= radius*1.2
        # Sensor 2 (abajo-izquierda)
        self.sensors[1]["x"] = self.center["x"] - radius * 0.866
        self.sensors[1]["y"] = self.center["y"] + radius * 0.5
        self._snap_to_grid(1)  # Ajustar a la grilla
        
        # Sensor 3 (abajo-derecha)
        self.sensors[2]["x"] = self.center["x"] + radius * 0.866
        self.sensors[2]["y"] = self.center["y"] + radius * 0.5
        self._snap_to_grid(2)  # Ajustar a la grilla
        
        # Actualizar radio máximo
        max_radius = min(canvas_width, canvas_height) * 0.3
        for sensor in self.sensors:
            sensor["max_radius"] = max_radius
        
        # Redibujar todos los elementos
        self.draw_grid()
        self.draw_center()
        self.draw_sensors()
        self.draw_scan_circles()

    def _snap_to_grid(self, sensor_index):
        """Ajustar la posición del sensor a la intersección de la grilla más cercana"""
        sensor = self.sensors[sensor_index]
        sensor["x"] = round(sensor["x"] / self.grid_spacing) * self.grid_spacing
        sensor["y"] = round(sensor["y"] / self.grid_spacing) * self.grid_spacing

    def draw_grid(self):
        """Dibujar la grilla de fondo"""
        self.canvas.delete("grid")
        
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        # Líneas verticales
        for x in range(0, width + self.grid_spacing, self.grid_spacing):
            self.canvas.create_line(
                x, 0, x, height, 
                fill=self.grid_color, width=1, tags="grid"
            )
        
        # Líneas horizontales
        for y in range(0, height + self.grid_spacing, self.grid_spacing):
            self.canvas.create_line(
                0, y, width, y, 
                fill=self.grid_color, width=1, tags="grid"
            )

    def draw_center(self):
        """Dibujar el punto central"""
        self.canvas.delete("center")
        self.canvas.create_oval(
            self.center["x"] - 5, self.center["y"] - 5,
            self.center["x"] + 5, self.center["y"] + 5,
            fill="#ffffff", outline="#cccccc", width=1, tags="center"
        )
        
        # Líneas al centro
        for sensor in self.sensors:
            # Determinar el color de la línea según el estado
            if sensor["status"] == 2:  # Disparo detectado
                line_color = sensor["fire_color"]
            elif sensor["status"] == 1:  # Activo
                line_color = sensor["active_color"]
            else:  # Inactivo
                line_color = "#555555"
                
            self.canvas.create_line(
                self.center["x"], self.center["y"],
                sensor["x"], sensor["y"],
                fill=line_color, width=1, dash=(3, 3), tags="center"
            )

    def draw_sensors(self):
        """Dibujar los sensores"""
        self.canvas.delete("sensors")
        for sensor in self.sensors:
            # Determinar color y estado del sensor
            if sensor["status"] == 2:  # Disparo detectado
                sensor_color = sensor["fire_color"]
                status_text = "FIRE DETECTED"
                status_color = sensor["fire_color"]
            elif sensor["status"] == 1:  # Activo
                sensor_color = sensor["active_color"]
                status_text = "ACTIVE"
                status_color = sensor["active_color"]
            else:  # Inactivo
                sensor_color = "#777777"
                status_text = "INACTIVE"
                status_color = "#aaaaaa"
            
            # Punto del sensor
            self.canvas.create_oval(
                sensor["x"] - 8, sensor["y"] - 8,
                sensor["x"] + 8, sensor["y"] + 8,
                fill=sensor_color, outline="white", width=1, tags="sensors"
            )
            
            # Etiquetas
            self.canvas.create_text(
                sensor["x"], sensor["y"] + 20,
                text=sensor["name"], fill="white", tags="sensors"
            )
            
            # Estado
            self.canvas.create_text(
                sensor["x"], sensor["y"] - 20,
                text=status_text, fill=status_color,
                tags="sensors"
            )
            
            # Coordenadas
            self.canvas.create_text(
                sensor["x"], sensor["y"] + 35,
                text=f"({sensor['x']},{sensor['y']})", fill="#888888", font=("Arial", 8),
                tags="sensors"
            )

    def draw_scan_circles(self):
        """Dibujar círculos de escaneo"""
        self.canvas.delete("circles")
        for sensor in self.sensors:
            if sensor["status"] > 0:  # Activo o disparo
                # Color según el estado
                circle_color = sensor["fire_color"] if sensor["status"] == 2 else sensor["active_color"]
                
                self.canvas.create_oval(
                    sensor["x"] - sensor["radius"], sensor["y"] - sensor["radius"],
                    sensor["x"] + sensor["radius"], sensor["y"] + sensor["radius"],
                    outline=circle_color, width=2, dash=(5, 5), tags="circles"
                )

    # Método eliminado: update_sensor_status ya no es necesario
    # def update_sensor_status(self, sensor_index):
    #     """Actualizar estado desde la interfaz"""
    #     try:
    #         status = int(self.status_entries[sensor_index].get())
    #         if status in [0, 1, 2]:
    #             # Actualizar el estado del sensor
    #             self.sensors[sensor_index]["status"] = status
    #             self.sensor_status[sensor_index] = status
    #             
    #             # Resetear el radio si se activa
    #             if status > 0 and self.sensors[sensor_index]["radius"] == 0:
    #                 self.sensors[sensor_index]["radius"] = 0
    #                 
    #             self.update_display()
    #         else:
    #             self._reset_entry(sensor_index)
    #     except ValueError:
    #         self._reset_entry(sensor_index)

    # Método eliminado: _reset_entry ya no es necesario
    # def _reset_entry(self, sensor_index):
    #     """Restablecer entrada a valor actual"""
    #     current = str(self.sensors[sensor_index]["status"])
    #     self.status_entries[sensor_index].delete(0, tk.END)
    #     self.status_entries[sensor_index].insert(0, current)

    def set_sensor_status_from_code(self, sensor_index, status):
        """Modificar estado programáticamente - Acepta 0, 1 o 2"""
        if 0 <= sensor_index < len(self.sensors) and status in [0, 1, 2]:
            self.sensors[sensor_index]["status"] = status
            self.sensor_status[sensor_index] = status
            
            # Resetear el radio si se activa
            if status > 0:
                self.sensors[sensor_index]["radius"] = 0
                
            self.update_display()

    def run_continuous_scanning(self):
        """Iniciar el escaneo continuo"""
        if not self.scanning:
            self.scanning = True
            self.scan_thread = threading.Thread(target=self._scan_loop, daemon=True)
            self.scan_thread.start()

    def _scan_loop(self):
        """Bucle principal de escaneo"""
        while self.scanning:
            for sensor in self.sensors:
                if sensor["status"] > 0 and self.scanning:  # Activo o disparo
                    sensor["radius"] += sensor["speed"]
                    if sensor["radius"] > sensor["max_radius"]:
                        sensor["radius"] = 0
            self.update_display()
            time.sleep(0.05)

    def update_display(self):
        """Actualizar la interfaz"""
        self.after_idle(lambda: [
            self.draw_grid(),  # Dibujar la grilla primero para que esté en el fondo
            self.draw_center(),
            self.draw_sensors(),
            self.draw_scan_circles()
        ])

    def stop_scanning(self):
        """Detener el escaneo"""
        self.scanning = False
        if self.scan_thread and self.scan_thread.is_alive():
            self.scan_thread.join(0.5)

    def crear_encabezado(self):
        """Crea el encabezado de la aplicación"""
        marco_encabezado = ctk.CTkFrame(self, fg_color=self.color_marco)
        marco_encabezado.pack(fill="x", pady=(0,0), padx=0)  # Eliminar padding
        
        contenedor_interno = ctk.CTkFrame(marco_encabezado, fg_color="transparent")
        contenedor_interno.pack(fill="x", padx=20, pady=15)

        # Título principal
        titulo = ctk.CTkLabel(
            contenedor_interno, 
            text="SISTEMA DE MONITOREO Y ALERTA DE DISPAROS",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=self.color_acento
        )
        titulo.pack(pady=(0, 5))
        
        # Subtítulo
        ctk.CTkLabel(
            contenedor_interno, 
            text="Graficos de los Disparos en Tiempo Real",
            font=ctk.CTkFont(size=14),
            text_color=self.color_texto_claro
        ).pack(pady=(0, 5))

        fecha_actual = datetime.datetime.now().strftime("%d/%m/%Y")
        ctk.CTkLabel(
            contenedor_interno,
            text=f"Fecha: {fecha_actual}",
            font=ctk.CTkFont(size=12),
            text_color=self.color_texto_secundario
        ).pack()