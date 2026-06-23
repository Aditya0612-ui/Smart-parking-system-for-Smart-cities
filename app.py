from flask import Flask, render_template, request, redirect, url_for
import time
import random
import threading
import os
import wiotp.sdk.device

app = Flask(__name__)

# Core Shared Data State Simulating IoT Parking Sensors
TOTAL_SPOTS = 12
PARKING_SPOTS = {i: {"status": "Available", "car_no": None, "entry_time": None} for i in range(1, TOTAL_SPOTS + 1)}

# Populate initial random traffic data simulation
for i in range(1, 6):
    PARKING_SPOTS[i] = {
        "status": "Occupied",
        "car_no": f"MH-12-AB-{random.randint(1000, 9999)}",
        "entry_time": time.time() - random.randint(600, 3600)
    }

# IBM Watson IoT Platform Integration
CONFIG_FILE = "device.yaml"
iot_client = None
offline_mode = True

def get_stats():
    occupied = sum(1 for spot in PARKING_SPOTS.values() if spot["status"] == "Occupied")
    available = TOTAL_SPOTS - occupied
    return occupied, available

def publish_state_to_iot():
    global iot_client, offline_mode
    if offline_mode or not iot_client:
        return
    try:
        occupied, available = get_stats()
        # Convert keys to string for standard JSON structure
        spots_str_keys = {str(k): v for k, v in PARKING_SPOTS.items()}
        payload = {
            "total_spots": TOTAL_SPOTS,
            "occupied_spots": occupied,
            "available_spots": available,
            "spots": spots_str_keys
        }
        iot_client.publishEvent(eventId="status", msgFormat="json", data=payload, qos=1)
        print("[IoT Platform] Published updated status event successfully.")
    except Exception as e:
        print(f"[IoT Platform] Error publishing update: {e}")

def iot_command_callback(cmd):
    print(f"\n[IoT Command Received] ID: '{cmd.commandId}', payload: {cmd.data}")
    try:
        data = cmd.data
        if cmd.commandId == "book":
            slot_id = int(data.get("slot_id", 0))
            car_no = data.get("car_no", "UNKNOWN").strip().upper()
            if slot_id in PARKING_SPOTS:
                if PARKING_SPOTS[slot_id]["status"] == "Available":
                    PARKING_SPOTS[slot_id] = {
                        "status": "Occupied",
                        "car_no": car_no,
                        "entry_time": time.time()
                    }
                    print(f"→ Booked slot {slot_id} for vehicle {car_no} via IoT Command.")
                    publish_state_to_iot()
                else:
                    print(f"→ Failed: Slot {slot_id} already occupied.")
            else:
                print(f"→ Failed: Invalid slot ID {slot_id}.")
        elif cmd.commandId == "cancel":
            slot_id = int(data.get("slot_id", 0))
            if slot_id in PARKING_SPOTS:
                if PARKING_SPOTS[slot_id]["status"] == "Occupied":
                    car_no = PARKING_SPOTS[slot_id]["car_no"]
                    PARKING_SPOTS[slot_id] = {
                        "status": "Available",
                        "car_no": None,
                        "entry_time": None
                    }
                    print(f"→ Vacated slot {slot_id} (Vehicle: {car_no}) via IoT Command.")
                    publish_state_to_iot()
                else:
                    print(f"→ Failed: Slot {slot_id} is already vacant.")
            else:
                print(f"→ Failed: Invalid slot ID {slot_id}.")
    except Exception as e:
        print(f"Error executing IoT command callback: {e}")

def init_iot_client():
    global iot_client, offline_mode
    if not os.path.exists(CONFIG_FILE):
        print(f"[IoT Setup] Configuration file {CONFIG_FILE} not found. Running in Offline Local Mode.")
        return

    try:
        with open(CONFIG_FILE, "r") as f:
            content = f.read()
        if "your_org_id" in content or "your_device_id" in content:
            print("[IoT Setup] Default credentials detected in device.yaml. Running in Offline Local Mode.")
            return

        print("[IoT Setup] Loading configuration from device.yaml...")
        config = wiotp.sdk.device.parseConfigFile(CONFIG_FILE)
        iot_client = wiotp.sdk.device.DeviceClient(config=config)
        iot_client.commandCallback = iot_command_callback
        
        print("[IoT Setup] Connecting to IBM Watson IoT Platform...")
        iot_client.connect()
        offline_mode = False
        print("[IoT Setup] Connected successfully!")
        
        # Publish initial state
        publish_state_to_iot()
    except Exception as e:
        print(f"[IoT Setup] Connection failed: {e}. Running in Offline Local Mode.")
        offline_mode = True

# Start IoT client thread if we are in the main reloader thread
if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
    iot_thread = threading.Thread(target=init_iot_client, daemon=True)
    iot_thread.start()

@app.route('/')
def dashboard():
    occ = sum(1 for spot in PARKING_SPOTS.values() if spot["status"] == "Occupied")
    avail = TOTAL_SPOTS - occ
    msg = request.args.get('msg', '')
    return render_template('index.html', spots=PARKING_SPOTS, occ=occ, avail=avail, msg=msg)

@app.route('/park', methods=['POST'])
def park_vehicle():
    car_no = request.form.get('car_no', '').strip().upper()
    allocated_spot = None
    
    for spot_id, data in PARKING_SPOTS.items():
        if data["status"] == "Available":
            allocated_spot = spot_id
            break

    if allocated_spot:
        PARKING_SPOTS[allocated_spot] = {"status": "Occupied", "car_no": car_no, "entry_time": time.time()}
        publish_state_to_iot()
        return redirect(url_for('dashboard', msg=f"Success: Vehicle checked into Bay {allocated_spot:02d}"))
    return redirect(url_for('dashboard', msg="Error: Parking structure is completely full!"))

@app.route('/checkout', methods=['POST'])
def checkout_vehicle():
    spot_id = int(request.form.get('spot_id', 0))
    if spot_id in PARKING_SPOTS and PARKING_SPOTS[spot_id]["status"] == "Occupied":
        spot_data = PARKING_SPOTS[spot_id]
        duration = int(time.time() - spot_data["entry_time"])
        fare = 10.00 + (duration * 0.05)
        
        # Clear out structural memory data back to the empty state pool
        PARKING_SPOTS[spot_id] = {"status": "Available", "car_no": None, "entry_time": None}
        publish_state_to_iot()
        return redirect(url_for('dashboard', msg=f"Invoice generated for {spot_data['car_no']}: Duration: {duration} mins, Total Bill: ${fare:.2f}. Bay {spot_id:02d} is now vacant."))
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)

