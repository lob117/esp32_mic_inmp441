
import customtkinter as ctk
import os
from PIL import Image, ImageTk
import json
import tkinter as tk
from tkinter import filedialog

class SettingsFrame(ctk.CTkFrame):
    def __init__(self, parent ):
        super().__init__(parent)
        self.configure(fg_color="#2b2b2b")  # Color de fondo oscuro

        
        # Cargar configuración inicial o usar valores predeterminados
        self.cargar_configuracion()
        
        # Cargar íconos
        self.cargar_iconos()
        
        # Inicializar la interfaz
        self.inicializar_interfaz()

    def cargar_configuracion(self):
        """Carga la configuración desde un archivo o usa valores predeterminados"""
        try:
            with open("config.json", "r") as f:
                self.config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Configuración predeterminada
            self.config = {
                "umbral_probabilidad": 0.7,
                "tiempo_alerta": 30,
                "ruta_modelo": "modelo/default_model",
                "sensores_activos": [True, True, True],
                "mostrar_info_sensible": True,
                "ips_sensores": ["192.168.1.100", "192.168.1.101", "192.168.1.102"],
                "coordenadas_sensores": [
                    {"x": 600, "y": 240},
                    {"x": 640, "y": 520},
                    {"x": 960, "y": 520}
                ]
            }

    def cargar_iconos(self):
        """Carga los íconos utilizados en la interfaz"""
        try:
            # Intentamos cargar los íconos si están disponibles
            folder_icon_path = "assets/folder_icon.png"
            eye_open_path = "assets/eye_open.png"
            eye_closed_path = "assets/eye_closed.png"
            
            if os.path.exists(folder_icon_path):
                self.folder_icon = ctk.CTkImage(
                    light_image=Image.open(folder_icon_path),
                    dark_image=Image.open(folder_icon_path),
                    size=(20, 20)
                )
            else:
                self.folder_icon = None
                
            if os.path.exists(eye_open_path) and os.path.exists(eye_closed_path):
                self.eye_open_icon = ctk.CTkImage(
                    light_image=Image.open(eye_open_path),
                    dark_image=Image.open(eye_open_path),
                    size=(20, 20)
                )
                self.eye_closed_icon = ctk.CTkImage(
                    light_image=Image.open(eye_closed_path),
                    dark_image=Image.open(eye_closed_path),
                    size=(20, 20)
                )
            else:
                self.eye_open_icon = None
                self.eye_closed_icon = None
        except Exception as e:
            print(f"Error al cargar íconos: {e}")
            self.folder_icon = None
            self.eye_open_icon = None
            self.eye_closed_icon = None

    def inicializar_interfaz(self):
        """Inicializa la interfaz de usuario"""
        # Configuración del sistema grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)  # La última sección tendrá más espacio
        
        # Encabezado
        self.crear_encabezado()
        
        # Secciones de configuración
        self.crear_seccion_umbral_deteccion()
        self.crear_seccion_tiempo_alerta()
        self.crear_seccion_modelo()
        self.crear_seccion_control_sensores()
        self.crear_seccion_opciones_privacidad()
        
        # Botones de acción
        self.crear_botones_accion()

    def crear_encabezado(self):
        """Crea el encabezado de la sección de configuración"""
        marco_encabezado = ctk.CTkFrame(self, fg_color="#333333", corner_radius=10)
        marco_encabezado.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        titulo = ctk.CTkLabel(
            marco_encabezado, 
            text="CONFIGURACIÓN DEL SISTEMA",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#5D87FF"  # Color azul
        )
        titulo.pack(pady=15)

    def crear_seccion_umbral_deteccion(self):
        """Crea la sección para configurar el umbral de detección"""
        marco = ctk.CTkFrame(self, fg_color="#333333", corner_radius=10)
        marco.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        # Título de la sección
        ctk.CTkLabel(
            marco,
            text="UMBRAL DE PROBABILIDAD PARA DETECCIÓN DE DISPAROS",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#E0E0E0"
        ).pack(anchor="w", padx=20, pady=(15, 5))
        
        # Descripción
        ctk.CTkLabel(
            marco,
            text="Establece el valor mínimo de probabilidad para considerar como disparo positivo (0.0 - 1.0)",
            font=ctk.CTkFont(size=12),
            text_color="#B0B0B0"
        ).pack(anchor="w", padx=20, pady=(0, 10))
        
        # Contenedor para el control
        contenedor = ctk.CTkFrame(marco, fg_color="transparent")
        contenedor.pack(fill="x", padx=20, pady=(0, 15))
        
        # Etiqueta
        ctk.CTkLabel(
            contenedor,
            text="Umbral:",
            font=ctk.CTkFont(size=14),
            text_color="#E0E0E0"
        ).pack(side="left", padx=(0, 10))
        
        # Entrada de texto
        self.umbral_entry = ctk.CTkEntry(
            contenedor,
            width=100,
            font=ctk.CTkFont(size=14),
            fg_color="#1a1a1a",
            border_color="#5D87FF",
            text_color="#E0E0E0"
        )
        self.umbral_entry.pack(side="left")
        self.umbral_entry.insert(0, str(self.config["umbral_probabilidad"]))
        
        # Validación en tiempo real
        self.umbral_entry.bind("<KeyRelease>", self.validar_umbral)
        
        # Valor actual
        self.umbral_actual_label = ctk.CTkLabel(
            contenedor,
            text=f"Actual: {self.config['umbral_probabilidad']}",
            font=ctk.CTkFont(size=12),
            text_color="#00BFA5"  # Verde para indicar valor actual
        )
        self.umbral_actual_label.pack(side="left", padx=(20, 0))

    def crear_seccion_tiempo_alerta(self):
        """Crea la sección para configurar el tiempo de alerta sin datos"""
        marco = ctk.CTkFrame(self, fg_color="#333333", corner_radius=10)
        marco.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        # Título de la sección
        ctk.CTkLabel(
            marco,
            text="TIEMPO PARA GENERAR ALERTA SIN RECEPCIÓN DE DATOS",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#E0E0E0"
        ).pack(anchor="w", padx=20, pady=(15, 5))
        
        # Descripción
        ctk.CTkLabel(
            marco,
            text="Establece el tiempo en segundos antes de alertar por falta de datos de los sensores",
            font=ctk.CTkFont(size=12),
            text_color="#B0B0B0"
        ).pack(anchor="w", padx=20, pady=(0, 10))
        
        # Contenedor para el control
        contenedor = ctk.CTkFrame(marco, fg_color="transparent")
        contenedor.pack(fill="x", padx=20, pady=(0, 15))
        
        # Etiqueta
        ctk.CTkLabel(
            contenedor,
            text="Tiempo (segundos):",
            font=ctk.CTkFont(size=14),
            text_color="#E0E0E0"
        ).pack(side="left", padx=(0, 10))
        
        # Entrada de texto
        self.tiempo_alerta_entry = ctk.CTkEntry(
            contenedor,
            width=100,
            font=ctk.CTkFont(size=14),
            fg_color="#1a1a1a",
            border_color="#5D87FF",
            text_color="#E0E0E0"
        )
        self.tiempo_alerta_entry.pack(side="left")
        self.tiempo_alerta_entry.insert(0, str(self.config["tiempo_alerta"]))
        
        # Validación en tiempo real
        self.tiempo_alerta_entry.bind("<KeyRelease>", self.validar_tiempo_alerta)
        
        # Valor actual
        self.tiempo_alerta_actual_label = ctk.CTkLabel(
            contenedor,
            text=f"Actual: {self.config['tiempo_alerta']} segundos",
            font=ctk.CTkFont(size=12),
            text_color="#00BFA5"  # Verde para indicar valor actual
        )
        self.tiempo_alerta_actual_label.pack(side="left", padx=(20, 0))

    def crear_seccion_modelo(self):
        """Crea la sección para seleccionar el modelo"""
        marco = ctk.CTkFrame(self, fg_color="#333333", corner_radius=10)
        marco.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        # Título de la sección
        ctk.CTkLabel(
            marco,
            text="CONFIGURACIÓN DEL MODELO DE DETECCIÓN",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#E0E0E0"
        ).pack(anchor="w", padx=20, pady=(15, 5))
        
        # Descripción
        ctk.CTkLabel(
            marco,
            text="Selecciona o establece la ruta del modelo entrenado para la detección de disparos",
            font=ctk.CTkFont(size=12),
            text_color="#B0B0B0"
        ).pack(anchor="w", padx=20, pady=(0, 10))
        
        # Contenedor para el control
        contenedor = ctk.CTkFrame(marco, fg_color="transparent")
        contenedor.pack(fill="x", padx=20, pady=(0, 15))
        
        # Etiqueta
        ctk.CTkLabel(
            contenedor,
            text="Ruta del modelo:",
            font=ctk.CTkFont(size=14),
            text_color="#E0E0E0"
        ).pack(side="left", padx=(0, 10))
        
        # Entrada de texto
        self.modelo_entry = ctk.CTkEntry(
            contenedor,
            width=300,
            font=ctk.CTkFont(size=14),
            fg_color="#1a1a1a",
            border_color="#5D87FF",
            text_color="#E0E0E0"
        )
        self.modelo_entry.pack(side="left", padx=(0, 10))
        self.modelo_entry.insert(0, self.config["ruta_modelo"])
        
        # Botón para examinar
        if self.folder_icon:
            self.examinar_btn = ctk.CTkButton(
                contenedor,
                text="",
                image=self.folder_icon,
                width=30,
                fg_color="#5D87FF",
                hover_color="#4A6CD0",
                command=self.seleccionar_modelo
            )
        else:
            self.examinar_btn = ctk.CTkButton(
                contenedor,
                text="Examinar",
                width=80,
                fg_color="#5D87FF",
                hover_color="#4A6CD0",
                command=self.seleccionar_modelo
            )
        self.examinar_btn.pack(side="left")

    def crear_seccion_control_sensores(self):
        """Crea la sección para controlar los sensores"""
        marco = ctk.CTkFrame(self, fg_color="#333333", corner_radius=10)
        marco.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        
        # Título de la sección
        ctk.CTkLabel(
            marco,
            text="CONTROL DE SENSORES",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#E0E0E0"
        ).pack(anchor="w", padx=20, pady=(15, 5))
        
        # Descripción
        ctk.CTkLabel(
            marco,
            text="Activa o desactiva cada sensor individualmente",
            font=ctk.CTkFont(size=12),
            text_color="#B0B0B0"
        ).pack(anchor="w", padx=20, pady=(0, 10))
        
        # Contenedor para los controles de sensores
        sensores_container = ctk.CTkFrame(marco, fg_color="transparent")
        sensores_container.pack(fill="x", padx=20, pady=(5, 15))
        
        # Configurar grid para los sensores
        sensores_container.columnconfigure((0, 1, 2), weight=1)
        
        # Colores para los sensores (los mismos que en el dashboard)
        colores_sensores = ["#4CAF50", "#9C27B0", "#2196F3"]  # Verde, Morado, Azul
        
        # Variables para almacenar el estado de los switches
        self.var_sensores = []
        self.botones_sensores = []
        
        # Crear controles para cada sensor
        for i in range(3):
            # Frame para el sensor
            sensor_frame = ctk.CTkFrame(sensores_container, fg_color="#1a1a1a", corner_radius=8)
            sensor_frame.grid(row=0, column=i, padx=10, pady=10, sticky="ew")
            
            # Encabezado del sensor
            header_frame = ctk.CTkFrame(sensor_frame, fg_color=colores_sensores[i], corner_radius=6)
            header_frame.pack(fill="x", pady=(0, 10))
            
            ctk.CTkLabel(
                header_frame,
                text=f"SENSOR {i+1}",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color="#1a1a1a"
            ).pack(pady=5)
            
            # Información del sensor
            info_frame1 = ctk.CTkFrame(sensor_frame, fg_color="transparent")
            info_frame1.pack(fill="x", padx=10, pady=5)
            
            ctk.CTkLabel(
                info_frame1,
                text="IP:",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#B0B0B0"
            ).pack(side="left")
            
            # Etiqueta para la IP
            self.ip_label = ctk.CTkLabel(
                info_frame1,
                text=self.config["ips_sensores"][i],
                font=ctk.CTkFont(size=12),
                text_color="#E0E0E0"
            )
            self.ip_label.pack(side="left", padx=5)
            
            # Información de coordenadas
            info_frame2 = ctk.CTkFrame(sensor_frame, fg_color="transparent")
            info_frame2.pack(fill="x", padx=10, pady=5)
            
            ctk.CTkLabel(
                info_frame2,
                text="Coord:",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#B0B0B0"
            ).pack(side="left")
            
            # Etiqueta para las coordenadas
            coord_x = self.config["coordenadas_sensores"][i]["x"]
            coord_y = self.config["coordenadas_sensores"][i]["y"]
            self.coord_label = ctk.CTkLabel(
                info_frame2,
                text=f"({coord_x}, {coord_y})",
                font=ctk.CTkFont(size=12),
                text_color="#E0E0E0"
            )
            self.coord_label.pack(side="left", padx=5)
            
            # Variable para el estado
            var = ctk.BooleanVar(value=self.config["sensores_activos"][i])
            self.var_sensores.append(var)
            
            # Botón de activación
            btn_frame = ctk.CTkFrame(sensor_frame, fg_color="transparent")
            btn_frame.pack(fill="x", padx=10, pady=(10, 5))
            
            estado_texto = "ACTIVADO" if self.config["sensores_activos"][i] else "DESACTIVADO"
            estado_color = "#00BFA5" if self.config["sensores_activos"][i] else "#F44336"
            
            btn = ctk.CTkButton(
                btn_frame,
                text=estado_texto,
                fg_color=estado_color,
                hover_color="#333333",
                command=lambda idx=i: self.toggle_sensor(idx)
            )
            btn.pack(fill="x", padx=10, pady=5)
            self.botones_sensores.append(btn)

    def crear_seccion_opciones_privacidad(self):
        """Crea la sección para opciones de privacidad"""
        marco = ctk.CTkFrame(self, fg_color="#333333", corner_radius=10)
        marco.grid(row=5, column=0, padx=20, pady=10, sticky="ew")
        
        # Título de la sección
        ctk.CTkLabel(
            marco,
            text="OPCIONES DE PRIVACIDAD",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#E0E0E0"
        ).pack(anchor="w", padx=20, pady=(15, 5))
        
        # Contenedor para los controles
        contenedor = ctk.CTkFrame(marco, fg_color="transparent")
        contenedor.pack(fill="x", padx=20, pady=(5, 15))
        
        # Variable para el estado
        self.var_mostrar_info = ctk.BooleanVar(value=self.config["mostrar_info_sensible"])
        
        # Etiqueta
        ctk.CTkLabel(
            contenedor,
            text="Mostrar información sensible (IPs y coordenadas):",
            font=ctk.CTkFont(size=14),
            text_color="#E0E0E0"
        ).pack(side="left", padx=(0, 10))
        
        # Botón para mostrar/ocultar información
        if self.eye_open_icon and self.eye_closed_icon:
            icon = self.eye_open_icon if self.config["mostrar_info_sensible"] else self.eye_closed_icon
            self.info_btn = ctk.CTkButton(
                contenedor,
                text="",
                image=icon,
                width=30,
                fg_color="#5D87FF" if self.config["mostrar_info_sensible"] else "#F44336",
                hover_color="#4A6CD0",
                command=self.toggle_info_sensible
            )
        else:
            texto = "Mostrar" if self.config["mostrar_info_sensible"] else "Ocultar"
            self.info_btn = ctk.CTkButton(
                contenedor,
                text=texto,
                width=80,
                fg_color="#5D87FF" if self.config["mostrar_info_sensible"] else "#F44336",
                hover_color="#4A6CD0",
                command=self.toggle_info_sensible
            )
        self.info_btn.pack(side="left")

    def crear_botones_accion(self):
        """Crea los botones de acción (guardar/cancelar)"""
        marco_botones = ctk.CTkFrame(self, fg_color="transparent")
        marco_botones.grid(row=6, column=0, padx=20, pady=(10, 20), sticky="ew")
        
        # Botón cancelar
        btn_cancelar = ctk.CTkButton(
            marco_botones,
            text="CANCELAR",
            fg_color="#555555",
            hover_color="#444444",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.cancelar_cambios
        )
        btn_cancelar.pack(side="left", padx=(0, 10))
        
        # Botón guardar
        btn_guardar = ctk.CTkButton(
            marco_botones,
            text="GUARDAR CONFIGURACIÓN",
            fg_color="#00BFA5",
            hover_color="#00A090",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.guardar_configuracion
        )
        btn_guardar.pack(side="right")

    def validar_umbral(self, event):
        """Valida que el umbral esté en el rango correcto"""
        try:
            valor = float(self.umbral_entry.get())
            if valor < 0:
                self.umbral_entry.delete(0, "end")
                self.umbral_entry.insert(0, "0.0")
            elif valor > 1:
                self.umbral_entry.delete(0, "end")
                self.umbral_entry.insert(0, "1.0")
        except ValueError:
            # Si no es un número válido, restaurar al valor anterior
            self.umbral_entry.delete(0, "end")
            self.umbral_entry.insert(0, str(self.config["umbral_probabilidad"]))

    def validar_tiempo_alerta(self, event):
        """Valida que el tiempo de alerta sea un número entero positivo"""
        try:
            valor = int(self.tiempo_alerta_entry.get())
            if valor < 1:
                self.tiempo_alerta_entry.delete(0, "end")
                self.tiempo_alerta_entry.insert(0, "1")
        except ValueError:
            # Si no es un número válido, restaurar al valor anterior
            self.tiempo_alerta_entry.delete(0, "end")
            self.tiempo_alerta_entry.insert(0, str(self.config["tiempo_alerta"]))

    def seleccionar_modelo(self):
        """Abre un diálogo para seleccionar la ruta del modelo"""
        ruta = filedialog.askdirectory(title="Seleccionar carpeta del modelo")
        if ruta:
            self.modelo_entry.delete(0, "end")
            self.modelo_entry.insert(0, ruta)

    def toggle_sensor(self, indice):
        """Activa o desactiva un sensor"""
        estado_actual = self.var_sensores[indice].get()
        nuevo_estado = not estado_actual
        self.var_sensores[indice].set(nuevo_estado)
        
        # Actualizar el botón
        estado_texto = "ACTIVADO" if nuevo_estado else "DESACTIVADO"
        estado_color = "#00BFA5" if nuevo_estado else "#F44336"
        self.botones_sensores[indice].configure(
            text=estado_texto,
            fg_color=estado_color
        )

    def toggle_info_sensible(self):
        """Activa o desactiva la visualización de información sensible"""
        nuevo_estado = not self.var_mostrar_info.get()
        self.var_mostrar_info.set(nuevo_estado)
        
        # Actualizar el botón
        if self.eye_open_icon and self.eye_closed_icon:
            icon = self.eye_open_icon if nuevo_estado else self.eye_closed_icon
            self.info_btn.configure(
                image=icon,
                fg_color="#5D87FF" if nuevo_estado else "#F44336"
            )
        else:
            texto = "Mostrar" if nuevo_estado else "Ocultar"
            self.info_btn.configure(
                text=texto,
                fg_color="#5D87FF" if nuevo_estado else "#F44336"
            )

    def guardar_configuracion(self):
        """Guarda la configuración en un archivo"""
        try:
            # Actualizar valores de configuración
            self.config["umbral_probabilidad"] = float(self.umbral_entry.get())
            self.config["tiempo_alerta"] = int(self.tiempo_alerta_entry.get())
            self.config["ruta_modelo"] = self.modelo_entry.get()
            self.config["mostrar_info_sensible"] = self.var_mostrar_info.get()
            
            for i in range(3):
                self.config["sensores_activos"][i] = self.var_sensores[i].get()
            
            # Guardar en archivo JSON
            with open("config.json", "w") as f:
                json.dump(self.config, f, indent=4)
            
            # Notificar al usuario
            self.mostrar_notificacion("Configuración guardada correctamente", True)
            

            
        except Exception as e:
            self.mostrar_notificacion(f"Error al guardar: {e}", False)

    def cancelar_cambios(self):
        """Cancela los cambios y recarga la configuración original"""
        self.cargar_configuracion()
        self.umbral_entry.delete(0, "end")
        self.umbral_entry.insert(0, str(self.config["umbral_probabilidad"]))
        
        self.tiempo_alerta_entry.delete(0, "end")
        self.tiempo_alerta_entry.insert(0, str(self.config["tiempo_alerta"]))
        
        self.modelo_entry.delete(0, "end")
        self.modelo_entry.insert(0, self.config["ruta_modelo"])
        
        self.var_mostrar_info.set(self.config["mostrar_info_sensible"])
        
        for i in range(3):
            self.var_sensores[i].set(self.config["sensores_activos"][i])
            estado_texto = "ACTIVADO" if self.config["sensores_activos"][i] else "DESACTIVADO"
            estado_color = "#00BFA5" if self.config["sensores_activos"][i] else "#F44336"
            self.botones_sensores[i].configure(
                text=estado_texto,
                fg_color=estado_color
            )
        
        self.mostrar_notificacion("Cambios cancelados", True)

    def mostrar_notificacion(self, mensaje, exito=True):
        """Muestra una notificación temporal"""
        # Crear un cuadro de notificación
        color = "#00BFA5" if exito else "#F44336"
        notificacion = ctk.CTkFrame(self, fg_color=color, corner_radius=10)
        notificacion.place(relx=0.5, rely=0.9, anchor="center")
        
        ctk.CTkLabel(
            notificacion,
            text=mensaje,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#FFFFFF"
        ).pack(padx=20, pady=10)
        
        # Eliminar después de 3 segundos
        self.after(3000, notificacion.destroy)