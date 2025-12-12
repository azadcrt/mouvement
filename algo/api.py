from digi.xbee.devices import XBeeDevice, XBee64BitAddress, RemoteXBeeDevice

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
BROADCAST_64 = RemoteXBeeDevice(device, XBee64BitAddress.BROADCAST_ADDRESS)
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

rx_count = 0
def handle_rx(msg):
    global rx_count
    rx_count += 1
    try:
        _ = msg.data  # consommer la donnée (pas de travail lourd)
    except Exception:
        pass
    print("RX callback #", rx_count)

def sender_thread():
    ID = 0
    RSSI = 0
    nbj = 0
    IDD = 0
    interval = 1  # secondes
    last_send = time.time()

    while not stop_flag.is_set():
        data = device.read_data()
        if data is None:
    # aucun message reçu → on continue
            pass
        else:
    # ignore les messages
            pass

        current_time = time.time()
        if current_time - last_send >= interval:
            sync_msg = f"({ID},{RSSI},{nbj})"
            try:
                device.send_data_async(BROADCAST_64, sync_msg)
                print("📡 Broadcast:", sync_msg)
            except Exception as e:
                print("Erreur send:", e)
                break

            IDD += 1
            if IDD > 5:
                IDD = 0
                ID += 1
            if ID==6 and IDD==1:
                break
            last_send = current_time  # mettre à jour le dernier envoi

def mise(line):
    print(line)
    global send,timeS,ax,ay,az,gx,gy,gz
    elem = line.split(":")
    try:
        if len(elem) > 1:
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
        else:
            Pmsg = line.split(",")
            ax = Pmsg[0]
            ay = Pmsg[1]
            az = Pmsg[2]
            gx = Pmsg[3]
            gy = Pmsg[4]
            gz = Pmsg[5]
            timeS = Pmsg[-2]
            send = Pmsg[-1]
    finally:
        print("")

    

    

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

    #algo initialisation
    start_time = time.time()
    print("⏱️ Début de l’envoi périodique de algo...")

    # Lance le thread de surveillance clavier
    listener_thread = threading.Thread(target=wait_for_enter)
    listener_thread.daemon = True
    listener_thread.start()
    stop_flag.clear()
    device.add_data_received_callback(handle_rx)
    t = threading.Thread(target=sender_thread)
    t.start()
    t.join()
    print("🛑 Envoi SYNC arrêté. Passage à la réception des messages...\n")
    device.del_data_received_callback(handle_rx)
    #time.sleep(1)
    device.send_data_async(BROADCAST_64, "1")

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
        try:
            with open(csv_file_path, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                mise(line)
                writer.writerow([timeS, send, ax, ay, az, gx, gy, gz])
        except Exception as e:
            print(line)
            


except KeyboardInterrupt:
    print("\n🛑 Programme interrompu par l'utilisateur.")

finally:
    print("🔌 Fermeture du périphérique XBee.")
    device.close()
