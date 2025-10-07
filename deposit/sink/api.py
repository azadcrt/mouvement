from digi.xbee.devices import XBeeDevice
import time
import threading
import sys
import os
import csv
import binascii
import serial


port_name = 'COM9'
baud_rate = 9600
#"timestamp_ms", "sender", "accel-x", "accel-y", "accel-z", "gyro-x", "gyro-y", "gyro-z"

send = ""
timeS = ""
ax = ""
ay = ""
az=""
gx = ""
gy = ""
gz = ""



# Fichier CSV
csv_file_path = "log.csv"

device = XBeeDevice(port_name, baud_rate)
device.open()

# --- Flag de contrôle partagé entre threads
stop_flag = threading.Event()

# --- Dossier et fichier CSV
log_folder = "logs"
csv_file_path = os.path.join(log_folder, "reception.csv")
os.makedirs(log_folder, exist_ok=True)

# --- Thread pour surveiller l’entrée clavier
def wait_for_enter():
    input("➡️  Appuie sur Entrée à tout moment pour arrêter.\n")
    stop_flag.set()
def read_api_frame(ser):
    while True:
        # Chercher le délimiteur 0x7E
        if ser.read(1) == b'\x7E':
            break  # Trouvé !

    length_bytes = ser.read(2)
    length = int.from_bytes(length_bytes, byteorder='big')

    frame_data = ser.read(length)
    return frame_data

def process_frame(frame):
    # Convertir en chaîne de caractères lisible si nécessaire
    frame_str = frame.decode('utf-8', errors='ignore')
    frame_str = frame_str.replace('\x02', '\x02 ')
    
    return frame_str
def clean_line(line):
    # Garde uniquement les caractères imprimables ASCII (ou UTF-8 si tu préfères)
    cleaned = ''.join(c for c in line if 32 <= ord(c) <= 126)
    return cleaned[1:]

def mise(line):
    global send,timeS,ax,ay,az,gx,gy,gz
    elem = line.split(":")
    path = elem[1].split(",")
    send = path[0]
    print(send)
    Emsg = line.split("'")
    msg = Emsg[1]
    Pmsg = msg.split(",")
    ax = Pmsg[0]
    ay = Pmsg[1]
    az = Pmsg[2]
    gx = Pmsg[3]
    gy = Pmsg[4]
    gz = Pmsg[5]
    timeS = Pmsg[-1]


    

try:
    print("Appuie sur Entrée pour démarrer l’envoi.")
    input(">> ")
    device.send_data_broadcast("1")
    print("✅ Message '1' envoyé en broadcast.")

    start_time = time.time()
    print("⏱️ Début de l’envoi périodique de SYNC...")

    # Lance le thread de surveillance clavier
    listener_thread = threading.Thread(target=wait_for_enter)
    listener_thread.daemon = True
    listener_thread.start()

    while not stop_flag.is_set():
        elapsed_ms = int((time.time() - start_time) * 1000)
        sync_msg = f"SYNC:{elapsed_ms}"
        device.send_data_broadcast(sync_msg)
        print(f"📡 Broadcast: {sync_msg}")
        time.sleep(1)  # Envoi toutes les secondes

    print("🛑 Envoi SYNC arrêté. Passage à la réception des messages...\n")
    device.send_data_broadcast("1")

    # --- Initialisation du fichier CSV
    if not os.path.exists(csv_file_path):
        with open(csv_file_path, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp_ms", "sender", "accel-x", "accel-y", "accel-z", "gyro-x", "gyro-y", "gyro-z"])

    # --- Boucle infinie de réception + écriture CSV
    device.close()
    serial_port = 'COM9'
    baudrate = 9600
    ser = serial.Serial(serial_port, baudrate, timeout=0.1)

    print("📥 Réception active (Ctrl+C pour quitter).")
    while True:
        line = clean_line(read_api_frame(ser).decode('utf-8', errors='replace'))
        #print(line)
        with open(csv_file_path, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            mise(line)
            writer.writerow([timeS, send, ax, ay, az, gx, gy, gz])
            


except KeyboardInterrupt:
    print("\n🛑 Programme interrompu par l'utilisateur.")

finally:
    print("🔌 Fermeture du périphérique XBee.")
    device.close()
