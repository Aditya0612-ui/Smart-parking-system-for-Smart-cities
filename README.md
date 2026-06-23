# Smart City Parking Management System

This project implements a web-based **Smart City Parking Management System** that simulates real-time, automated parking infrastructure. Parking slots are treated as digital IoT nodes that monitor occupancy, automate vehicle check-in/checkout, sync with the **IBM Watson IoT Platform**, and interface with a **Node-RED Web Dashboard**.

---

## 🏙️ System Architecture

The project consists of three main components:

1. **Flask Application (`app.py`)**: Runs the local web server, manages the in-memory parking state (12 slots), renders the HTML dashboard, and syncs updates to the IBM Watson IoT Platform in a background thread.
2. **Standalone IoT Simulator (`publish_iot.py`)**: A command-line script that can run on a separate device to simulate parking sensor changes and send/receive events via the IoT platform.
3. **Node-RED Dashboard (`node_red_flow.json`)**: A cloud-compatible dashboard that visualizes real-time status data and issues booking or cancellation commands back to the Python backend.

```
                  ┌────────────────────────────────────────┐
                  │          IBM Watson IoT Platform       │
                  │              (MQTT Broker)             │
                  └───────────▲──────────────────▲─────────┘
                              │                  │
                Publish Status│      Subscribe   │Publish Commands
            & Receive Commands│      Status Evts │& Subscribe Status
                              │                  │
  ┌───────────────────────────▼───┐    ┌─────────▼──────────────────┐
  │     Local Python Project      │    │     Node-RED Dashboard     │
  │                               │    │                            │
  │   ┌───────────────────────┐   │    │  ┌──────────────────────┐  │
  │   │  app.py (Flask Web)   ◄───┼────┼──► ui_gauge (Free Bays) │  │
  │   └──────────▲────────────┘   │    │  └──────────────────────┘  │
  │              │                │    │  ┌──────────────────────┐  │
  │   ┌──────────▼────────────┐   │    │  │ ui_template (Grid)   │  │
  │   │ index.html (Local UI) │   │    │  └──────────────────────┘  │
  │   └───────────────────────┘   │    │  ┌──────────────────────┐  │
  │                               │    │  │ Booking/Cancel Forms │  │
  └───────────────────────────────┘    │  └──────────────────────┘  │
                                       └────────────────────────────┘
```

---

## 📂 Project Directory Structure

```
├── app.py                     # Flask web server with integrated background IoT client
├── publish_iot.py             # Standalone Python simulator script for Watson IoT
├── device.yaml                # Configuration file containing IBM Watson IoT credentials
├── node_red_flow.json         # Complete Node-RED dashboard flow JSON configuration
├── templates/
│   └── index.html             # Local Web UI template displaying the parking grid
├── Smart City Parking Documentation.docx  # Detailed project report
└── ibm_watson_iot_setup.md    # Detailed guide for setting up IBM Cloud & Node-RED
```

---

## ✨ Features

- **Live Status Feed**: Dynamic monitoring of occupied and available bays.
- **Automated Slot Allocation**: Checks in vehicles using a closest-bay algorithm.
- **Integrated Micro-Billing**: Generates checkout invoices based on duration (Base: \$10.00 + \$0.05 per minute).
- **Two-Way IoT Synchronization**:
  - Check-in/checkout actions on the local Flask interface automatically update the Watson IoT cloud state.
  - Booking/cancellation forms in the Node-RED dashboard trigger real-time updates back to the Flask backend.
- **Offline Fallback Mode**: If IBM Watson credentials are not configured, both `app.py` and `publish_iot.py` default to offline simulation mode so you can run and test the project locally without cloud dependencies.

---

## 🚀 Getting Started

### 1. Prerequisites
Ensure you have Python installed, then install the required dependencies:
```bash
pip install flask wiotp-sdk
```

### 2. Configuration
Open `device.yaml` and configure your credentials from the IBM Watson IoT Platform:
```yaml
identity:
  orgId: "your_org_id"
  typeId: "your_device_type"
  deviceId: "your_device_id"
auth:
  token: "your_auth_token"
```
*(If left unchanged, the applications will run in **Offline Mode**).*

### 3. Running the Flask Web Server
Start the local dashboard by executing:
```bash
python app.py
```
Open your browser and navigate to: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

### 4. Running the Standalone Publisher
To simulate sensor updates from another device:
```bash
python publish_iot.py
```

### 5. Running the Node-RED Dashboard
1. Launch Node-RED locally or on IBM Cloud.
2. Ensure `node-red-dashboard` is installed via **Manage Palette**.
3. Import the flow from `node_red_flow.json` (Go to **Menu > Import > Clipboard**).
4. Update the **IBM Watson IoT Platform** MQTT configuration node with your Org ID and auth tokens, and click **Deploy**.
5. Access the Web Dashboard at: `http://<your-node-red-host>/ui`.

For comprehensive cloud provisioning steps, refer to [ibm_watson_iot_setup.md](file:///C:/Users/Aditya%20Patil/.gemini/antigravity/brain/882818d8-2bf9-4aa9-b71f-a5735bac7123/ibm_watson_iot_setup.md).
