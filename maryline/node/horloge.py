import time
import xbee

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


def adjust_clock(global_time):
    """Ajuste l'horloge locale."""
    local_time = time.ticks_ms()
    adjustment = global_time - local_time
    return adjustment


def handle_sync_message(sync_time):
    """Traite un message SYNC."""
    # Lire le RSSI du dernier paquet reçu

    rssi = xbee.atcmd("DB") * -1
    distance = calculate_distance(rssi)
    propagation_time = estimate_propagation_time(distance)
    global_time = sync_time + propagation_time
    return global_time


def send_sync_message():
    """Envoie un message SYNC."""
    current_time = time.ticks_ms()
    message = str(current_time)
    xbee.transmit(xbee.ADDR_BROADCAST, message)


def receive_sync_message():
    """Écoute les messages entrants."""
    #print("Attente de message...")
    packet = xbee.receive()
    if packet:
        print("recu")
        payload = packet.get('payload').decode()
        return handle_sync_message(clean_payload(payload))
