# Main.py
import customtkinter as ctk
from settings import SettingsFrame
import tkinter as tk

from deteccion import TriangulationScanner
from dash_board import DashboardFrame
import matplotlib.pyplot as pylt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class PerformanceApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        # ... (código existente)
        self.title("Performance Dashboard")
        self.geometry("1200x800")
        
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        
        self.sidebar_label = ctk.CTkLabel(self.sidebar, text="Menú", font=("Arial", 20))
        self.sidebar_label.pack(pady=20, padx=10)
        
        # Botones del sidebar
        self.pie_chart_btn = ctk.CTkButton(self.sidebar, text="Grafico de deteccion", command=self.show_deteccion)
        self.pie_chart_btn.pack(pady=10, padx=20, fill="x")
        
        self.dashboard_btn = ctk.CTkButton(
            self.sidebar, 
            text="Panel de Control", 
            command=self.show_dashboard
        )
        self.dashboard_btn.pack(pady=10, padx=20, fill="x")

        self.settings_btn = ctk.CTkButton(self.sidebar, text="Configuraciones", command=self.show_settings)
        self.settings_btn.pack(pady=10, padx=20, fill="x")
        
        
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.pack(side="right", fill="both", expand=True)
        
        # Inicializar frames
        self.sensor_triangulation = TriangulationScanner(self.main_frame)
        self.dashboard_frame = DashboardFrame(self.main_frame,self.sensor_triangulation)
        self.settings_frame = SettingsFrame(self.main_frame)
        # Inicializar el frame del dashboard

        self.show_deteccion()

    def show_deteccion(self):
        self.hide_all_frames()
        self.sensor_triangulation.pack(fill="both", expand=True)
        self.sensor_triangulation.run_continuous_scanning()  # Iniciar escaneo
    def show_settings(self):
        self.hide_all_frames()
        self.settings_frame.pack(fill="both", expand=True)
    def show_dashboard(self):
        self.hide_all_frames()
        self.dashboard_frame.pack(fill="both", expand=True)
        
    def hide_all_frames(self):
        # Añadir el dashboard a los frames a ocultar
        self.sensor_triangulation.pack_forget()
        self.settings_frame.pack_forget()
        self.dashboard_frame.pack_forget()
    # Al cerrar la aplicación:
    def on_closing(self):
        self.sensor_triangulation.stop_scanning()
        super().destroy()
# ... (resto del código existente)
if __name__ == "__main__":
    app = PerformanceApp()
    app.mainloop()