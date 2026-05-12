# esp32_mic_inmp441


# 🎙️ Sistema de Captura y Transmisión de Audio Wi-Fi (ESP32 + INMP441)

Este proyecto consiste en un sistema de hardware y software diseñado para la adquisición, transmisión en tiempo real e identificación de eventos acústicos (como disparos). Utiliza el **ESP32** como microcontrolador principal para capturar sonido digital de alta calidad y transmitirlo a través de una red Wi-Fi.

El diseño es completamente autónomo energéticamente, operando con una batería de litio recargable.

## 🚀 Características Principales

* **Transmisión Inalámbrica:** Envío de datos de audio en tiempo real a través de Wi-Fi.
* **Audio Digital de Alta Precisión:** Utiliza el protocolo **I2S (Inter-IC Sound)** mediante un micrófono digital INMP441, eliminando la necesidad de circuitos analógicos complejos.
* **Identificación de Eventos:** El sistema está pensado para el monitoreo e identificación de patrones acústicos específicos.
* **Gestión de Energía Integrada:** Alimentado por una batería 18650, con un módulo TP4056 encargado de proteger y gestionar la carga de la misma.
* **Optimización de Recursos:** La captura y transmisión de datos solo se inician al establecerse una conexión válida (DCP) con el servidor, ahorrando batería y permitiendo la escalabilidad a múltiples nodos sincronizados.

---

## ⚙️ Configuración del Sistema (Software)

El firmware del ESP32 está diseñado para actuar como **maestro y receptor** en el bus I2S. Esto le permite generar sus propias señales de sincronización y tener un control preciso sobre el muestreo de datos del micrófono.

**Lógica de Operación:**
1. El microcontrolador inicia y monitorea la conexión a la red Wi-Fi y al servidor destino.
2. Mientras no haya conexión, el micrófono permanece en reposo.
3. Al establecer una conexión válida, el ESP32 activa la lectura I2S y comienza la transmisión continua de los paquetes de audio.

---

## 🔌 Hardware y Esquema de Conexiones
<img width="386" height="250" alt="Imagen1" src="https://github.com/user-attachments/assets/0a8a0544-afa9-4508-92e5-83a9a5c84f95" />

El sistema se compone de tres módulos principales: el ESP32, el micrófono INMP441 y el cargador/protector de batería TP4056. 

A continuación, se detalla la tabla de conexiones (Pinout) para la replicación del prototipo:

| Dispositivo | Pin / Conexión | Conectado a | Descripción |
| :--- | :--- | :--- | :--- |
| **ESP32** | `GPIO14` | `SCK/BCLK` (INMP441) | Señal de reloj de bits para sincronización |
| | `GPIO15` | `WS/LRCLK` (INMP441) | Selección de canal (Izquierdo/Derecho) |
| | `GPIO32` | `SD/DATA` (INMP441) | Entrada de datos de audio digital |
| **INMP441** | `SCK/BCLK` | `GPIO14` (ESP32) | Entrada de reloj de bits |
| | `WS/LRCLK` | `GND` | Configurado a tierra para operar en **modo monoaural** |
| | `SD/DATA` | `GPIO32` (ESP32) | Salida de datos digitales de audio |
| | `VDD` | `3.3V` (ESP32) | Alimentación del micrófono |
| | `GND` | `GND` (General) | Referencia de tierra |
| **TP4056** | `B+` | Batería `+` | Entrada positiva de la celda 18650 |
| | `B-` | Batería `-` | Entrada negativa de la celda 18650 |
| | `OUT+` | ESP32 `VCC/5V` | Salida positiva regulada para alimentar el sistema |
| | `OUT-` | ESP32 `GND` | Salida negativa (Tierra común) |

> **Nota sobre el INMP441:** El pin `WS/LRCLK` del micrófono se conecta a `GND` para forzar la salida de datos por el canal izquierdo (modo mono), mientras que el ESP32 genera la señal Word Select desde el pin `GPIO15`.
