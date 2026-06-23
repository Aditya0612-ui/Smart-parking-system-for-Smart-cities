import time
import random
import os
import json
import wiotp.sdk.device

# Configuration path
CONFIG_FILE = "device.yaml"

# Simulating 12 parking spots
TOTAL_SPOTS = 12
PARKING_SPOTS = {str(i): {"status": "Available", "car_no": None} for i in range(1, TOTAL_SPOTS + 1)}

# Pre-populate 5 random occupied spots
for i in range(1, 6):
    PARKING_SPOTS[str(i)] = {
        "status": "Occupied",
        "car_no": f"MH-12-AB-{random.randint(1000, 9999)}"
    }

offline_mode = False
client = None

def get_stats():
    occupied = sum(1 for spot in PARKING_SPOTS.values() if spot["status"] == "Occupied")
    available = TOTAL_SPOTS - occupied
    return occupied, available

def publish_status():
    occupied, available = get_stats()
    payload = {
        "total_spots": TOTAL_SPOTS,
        "occupied_spots": occupied,
        "available_spots": available,
        "spots": PARKING_SPOTS
    }
    
    if offline_mode:
        print(f"\n[OFFLINE SIMULATION] Publishing event 'status':")
        print(json.dumps(payload, indent=2))
    else:
        try:
            print(f"\n[IoT Platform] Publishing status event...")
            # Publish event status
            client.publishEvent(eventId="status", msgFormat="json", data=payload, qos=1)
            print("→ Published successfully!")
        except Exception as e:
            print(f"Error publishing to IBM IoT Platform: {e}")

def myCommandCallback(cmd):
    print(f"\n[IoT Command Received] ID: '{cmd.commandId}', format: '{cmd.format}'")
    try:
        data = cmd.data
        print(f"Payload: {data}")
        
        if cmd.commandId == "book":
            slot_id = str(data.get("slot_id"))
            car_no = data.get("car_no", "UNKNOWN").strip().upper()
            
            if slot_id in PARKING_SPOTS:
                if PARKING_SPOTS[slot_id]["status"] == "Available":
                    PARKING_SPOTS[slot_id] = {"status": "Occupied", "car_no": car_no}
                    print(f"→ Successfully booked slot {slot_id} for vehicle {car_no}.")
                    publish_status()
                else:
                    print(f"→ Failed: Slot {slot_id} is already occupied.")
            else:
                print(f"→ Failed: Invalid slot ID {slot_id}.")
                
        elif cmd.commandId == "cancel":
            slot_id = str(data.get("slot_id"))
            
            if slot_id in PARKING_SPOTS:
                if PARKING_SPOTS[slot_id]["status"] == "Occupied":
                    car_no = PARKING_SPOTS[slot_id]["car_no"]
                    PARKING_SPOTS[slot_id] = {"status": "Available", "car_no": None}
                    print(f"→ Successfully cancelled booking for slot {slot_id} (Vehicle: {car_no}).")
                    publish_status()
                else:
                    print(f"→ Failed: Slot {slot_id} is already vacant.")
            else:
                print(f"→ Failed: Invalid slot ID {slot_id}.")
        else:
            print(f"→ Warning: Unknown command '{cmd.commandId}'")
            
    except Exception as e:
        print(f"Error processing command: {e}")

def main():
    global offline_mode, client
    
    print("====================================================")
    print("Smart City Parking - IBM Watson IoT Publisher Script")
    print("====================================================")
    
    # Check config file existence
    if not os.path.exists(CONFIG_FILE):
        print(f"Warning: Configuration file {CONFIG_FILE} not found!")
        print("Falling back to Offline Simulation Mode...")
        offline_mode = True
    else:
        try:
            # Check if config has default placeholders
            with open(CONFIG_FILE, "r") as f:
                content = f.read()
            if "your_org_id" in content or "your_device_id" in content:
                print("Default placeholders detected in device.yaml.")
                print("To connect to IBM Cloud, edit device.yaml with your actual credentials.")
                print("Running in Offline Simulation Mode...\n")
                offline_mode = True
            else:
                print(f"Loading configuration from {CONFIG_FILE}...")
                config = wiotp.sdk.device.parseConfigFile(CONFIG_FILE)
                client = wiotp.sdk.device.DeviceClient(config=config)
                
                # Set command callback
                client.commandCallback = myCommandCallback
                
                print("Connecting to IBM Watson IoT Platform...")
                client.connect()
                print("Connected successfully!")
        except Exception as e:
            print(f"Failed to connect to IBM Watson IoT Platform: {e}")
            print("Please check your device.yaml configuration.")
            print("Falling back to Offline Simulation Mode...\n")
            offline_mode = True

    print("Starting simulation loop. Press Ctrl+C to stop.")
    
    try:
        # If online, we run a background loop thread from the client to receive commands
        # and publish status periodically
        if not offline_mode:
            # Send initial state
            publish_status()
            while True:
                time.sleep(10)
                publish_status()
        else:
            # Offline simulation loop
            while True:
                publish_status()
                print("\n[Simulation Menu] Choose an option to simulate local dashboard updates:")
                print("1. Simulate Check-In (Book a slot)")
                print("2. Simulate Checkout (Cancel a slot)")
                print("3. Wait 10 seconds")
                print("4. Exit")
                
                choice = input("Enter choice (1-4): ").strip()
                if choice == '1':
                    car_no = input("Enter vehicle number: ").strip().upper()
                    if not car_no:
                        car_no = f"MH-12-AB-{random.randint(1000, 9999)}"
                    # Find first free slot
                    allocated = None
                    for sid, spot in PARKING_SPOTS.items():
                        if spot["status"] == "Available":
                            allocated = sid
                            break
                    if allocated:
                        PARKING_SPOTS[allocated] = {"status": "Occupied", "car_no": car_no}
                        print(f"Allocated Slot {allocated} for vehicle {car_no}")
                    else:
                        print("Error: Parking structure is full!")
                elif choice == '2':
                    occupied_slots = [sid for sid, spot in PARKING_SPOTS.items() if spot["status"] == "Occupied"]
                    if not occupied_slots:
                        print("No slots are currently occupied.")
                    else:
                        print(f"Occupied slots: {', '.join(occupied_slots)}")
                        sid = input("Enter slot ID to vacate: ").strip()
                        if sid in PARKING_SPOTS and PARKING_SPOTS[sid]["status"] == "Occupied":
                            PARKING_SPOTS[sid] = {"status": "Available", "car_no": None}
                            print(f"Vacated slot {sid}")
                        else:
                            print("Invalid occupied slot ID.")
                elif choice == '3':
                    print("Waiting...")
                    time.sleep(2)
                elif choice == '4':
                    print("Exiting...")
                    break
                else:
                    print("Invalid choice, waiting...")
                    time.sleep(2)
                    
    except KeyboardInterrupt:
        print("\nExiting simulation.")
    finally:
        if not offline_mode and client:
            client.disconnect()
            print("Disconnected from IBM Watson IoT Platform.")

if __name__ == "__main__":
    main()
