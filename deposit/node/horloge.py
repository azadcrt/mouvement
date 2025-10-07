import time
import xbee
import machine

# Paramètres de calibration
RSSI_0 = -46  # RSSI à 1 mètre (à calibrer)
n = 2.5  # Exposant de perte de propagation
C = 3e8  # Vitesse de la lumière (m/s)

def clean_payload(payload):
    """Extrait les chiffres du payload."""
    numeric_part = ''.join(c for c in payload if c.isdigit() or c == '.')
    if numeric_part:
        return float(numeric_part)
    else:
        print("Erreur : données invalides dans le payload")
        return None


def calculate_distance(rssi):
    """Calcule la distance approximative en mètres."""
    return 10 ** ((RSSI_0 - rssi) / (10 * n))


def estimate_propagation_time(distance):
    """Calcule le temps de propagation en secondes."""
    return distance / C


def handle_sync_message(sync_time):
    """Traite un message SYNC."""
    # Lire le RSSI du dernier paquet reçu

    rssi = xbee.atcmd("DB") * -1
    distance = calculate_distance(rssi)
    propagation_time = estimate_propagation_time(distance)
    global_time = sync_time + propagation_time
    global_time = time.ticks_ms() - global_time
    return global_time


def send_sync_message():
    """Envoie un message SYNC."""
    current_time = time.ticks_ms()
    message = str(current_time)
    xbee.transmit(xbee.ADDR_BROADCAST, message)


def receive_message():
    """Écoute les messages entrants."""
    #print("Attente de message...")
    packet = xbee.receive()
    if packet:
        payload = packet.get('payload').decode()
        return handle_sync_message(clean_payload(payload))
        
def main_horloge():
    """Fonction principale."""
    is_puit = xbee.atcmd("NI") == "PUITS"
    adjust = 0
    fadujst = 0
    startT = 0 
    i = 0
    if is_puit:
        send_sync_message()
        i = i + 1
        time.sleep(1)
    else:
        while i < 1:
            adjust = None
            adjust = receive_message()
            
            if adjust is not None:
                return adjust