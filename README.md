# Aquaculture Sensor Monitoring System

A wireless IoT-based monitoring system designed to monitor environmental and water conditions across multiple aquaculture sensor boxes.

The system consists of **4 Arduino-based sensor nodes** that collect sensor data and transmit it wirelessly using **NRF24L01** to a **Raspberry Pi 3B+**. The Raspberry Pi acts as the central receiver, logger, dashboard, and server client.

## System Overview

```text
┌──────────────┐
│   Box 1      │
│ Arduino +    │
│ Sensors      │
└──────┬───────┘
       │
┌──────────────┐
│   Box 2      │
│ Arduino +    │
│ Sensors      │
└──────┬───────┘
       │
       │       NRF24L01
       │    Wireless Communication
       │
┌──────┴───────┐
│ Raspberry Pi │
│    3B+       │
│              │
│ Receiver     │
│ Dashboard    │
│ Data Logger  │
└──────┬───────┘
       │
       │ HTTP POST
       ▼
┌──────────────┐
│ Web Server   │
│ PHP + MySQL  │
└──────────────┘
```

## Features

* Monitor up to **4 sensor boxes**
* Wireless communication using **NRF24L01**
* Salinity monitoring
* Water temperature monitoring
* Air temperature monitoring
* Humidity monitoring
* Water level monitoring
* Raspberry Pi central receiver
* Real-time monitoring dashboard
* Online / Offline device status
* CSV data logging
* Hourly log file organization
* Automatic storage management
* HTTP POST data transmission to a web server
* MySQL database integration

## Hardware

### Sensor Node

Each sensor box uses an Arduino-based system with:

* Arduino
* NRF24L01
* DS18B20
* DHT22
* Water level sensor
* Salinity sensor
* DC-DC converter
* Battery power supply

### Central Receiver

* Raspberry Pi 3B+
* NRF24L01
* Touch Display

## Sensors

| Sensor             | Measurement                |
| ------------------ | -------------------------- |
| Salinity Sensor    | Water salinity             |
| DS18B20            | Water temperature          |
| DHT22              | Air temperature & humidity |
| Water Level Sensor | Water level                |

## Wireless Communication

The sensor nodes communicate with the Raspberry Pi using the **NRF24L01 2.4 GHz wireless transceiver**.

Each Arduino periodically collects sensor readings and sends the data packet to the Raspberry Pi.

Example payload:

```text
Water Temperature
Air Temperature
Humidity
Water Level
Salinity
```

The communication address used by the current implementation is:

```text
TUNL1
```

## Raspberry Pi Software

The Raspberry Pi is responsible for receiving, processing, displaying, and storing the sensor data.

The project is organized into several Python modules:

```text
box_monitor/
│
├── main.py
├── receiver.py
├── logger.py
├── server.py
├── config.py
│
└── data/
    └── YYYY-MM-DD_HH.csv
```

### `main.py`

Main application entry point.

Responsibilities:

* Start the monitoring application
* Display the dashboard
* Display sensor box status
* Handle user interaction
* Open sensor detail pages

### `receiver.py`

Handles NRF24L01 communication.

Responsibilities:

* Listen for incoming packets
* Receive sensor data
* Process received packets
* Pass data to other components

The receiver is designed so that wireless communication does not block the graphical interface.

### `logger.py`

Handles local data storage.

Sensor readings are stored as CSV files and organized by hour.

Example:

```text
data/
├── 2026-09-28_10.csv
├── 2026-09-28_11.csv
└── 2026-09-28_12.csv
```

The logger also flushes records to storage and manages disk usage.

### `server.py`

Handles communication between the Raspberry Pi and the remote server.

Received sensor data can be sent to the server using an HTTP `POST` request.

Example
