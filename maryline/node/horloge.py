import time
import xbee

# Paramètres de calibration
RSSI_0 = -46  # RSSI à 1 mètre (à calibrer)
n = 2.5  # Exposant de perte de propagation
C = 3e8  # Vitesse de la lumière (m/s)

def is_prime(n):
    if n <= 1:
        return False
    for i in range(2, int(n ** 0.5)+1):
        if n % i == 0:
            return False
    return True

def calcul_charge(limit):
    somme = 0
    for i in range(2,limit):
        if is_prime(i):
            somme += i ** 0.5
    return somme   

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


def receive_message():
    """Écoute les messages entrants."""
    #print("Attente de message...")
    packet = xbee.receive()
    if packet:
        print("recu")
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
        print("send")
        send_sync_message()
        i = i + 1
        time.sleep(1)
    else:
        while i < 1:
            adjust = None
            adjust = receive_message()
            if adjust is not None:
                startT = time.ticks_ms()
                fadujst = adjust
                i = i+1
                return startT + fadujst



#def main():
    """Fonction principale."""
    #is_puit = xbee.atcmd("NI") == "PUITS"
    #adjust = 0
    #fadujst = 0
    #startT = 0 
    #i = 0
    #it = 0
    #if is_puit:
        #print("[Info] Ce nœud est le PUITS")
        #while i < 5:
            #print("send")
            #send_sync_message()
            #i = i + 1
            #time.sleep(2)
        #tpoi = time.ticks_ms()
        #while True:
                #packet = xbee.receive()
                #if packet:
                    #payload = packet.get('payload').decode()
                    #print(clean_payload(payload))
                    #print(time.ticks_ms())

    #else:
        #print("[Info] Ce nœud est un nœud régulier")
        #while i < 1:
            #adjust = None
            #adjust = receive_message()
            #if adjust is not None:
                #startT = time.ticks_ms()
                #fadujst = adjust
                #print("recu")
                #print(fadujst)
                #i = i + 1
            #tpoi = time.ticks_ms()
        #while True:
                 
            #limite = it*10000
            #resultat = calcul_charge(limite)
            #if time.ticks_ms() > tpoi + (30*60000):
                #print(time.ticks_ms()-startT + fadujst)
                #xbee.transmit(xbee.ADDR_BROADCAST, str(time.ticks_ms()-startT + fadujst))
                #tpoi = time.ticks_ms()
            #it=it+1