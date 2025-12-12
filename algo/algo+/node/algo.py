import xbee
import time
import machine


#---------------------
#CONFIGURATION
#---------------------
RSSI_DEFAULT = 100
#---------------------
#Variable
#---------------------
RSSI_min = {}
NjumpB = {}
Current_rssi = 0
L_RSSI = 0
direct = False
id_last = 0 

#---------------------
#CLEAN_UNKNOW_CHAR
#---------------------
def clean_line(line):
    cleaned = ''.join(c for c in line if 32 <= ord(c) <= 126)
    return cleaned[1:]

#---------------------
#MESSAGE_GESTION
#---------------------
def handle_message(payload):
    global id_last, RSSI_min, NjumpB
    # split + nettoyage
    splitload = payload.split(",")
    splitload = [int(x.strip().replace(')', '')) for x in splitload]

    ID = splitload[0]
    rssi = splitload[1]
    jmp  = splitload[2]

    id_last = ID
    # Si l'ID n'existe pas encore, initialise avec la valeur reçue
    if ID not in RSSI_min:

        #pas le bon rssi on ajoute pas celui en cours
        RSSI_min[ID] = rssi

        NjumpB[ID] = jmp
    else:
        # si nouveau RSSI est meilleur (plus petit), on met à jour
        if rssi < RSSI_min[ID]:
            RSSI_min[ID] = rssi
            NjumpB[ID] = jmp
    return ID, jmp, rssi

def received_message():
    global L_RSSI
    packet = xbee.receive()
    if packet:
        L_RSSI = xbee.atcmd("DB")
        payload = packet.get('payload').decode()
        return handle_message(clean_line(payload))

def resend(ID,jmp,rssi):
    global L_RSSI
    jmp = jmp + 1
    rssi = rssi + L_RSSI
    payload = "{},{},{}".format(ID, jmp, rssi)
    xbee.transmit(xbee.ADDR_BROADCAST, payload)


#---------------------
#Decision
#---------------------

def decision(ID):
    global RSSI_DEFAULT, direct
    LastBestRSSI = RSSI_min[ID]
    if NjumpB[ID] == 1:
        direct = True
    else:
        direct = False
    total = 0
    for id in RSSI_min:
        total = total + RSSI_min[id]
    RSSI_DEFAULT = total / len(RSSI_min)
    return direct,RSSI_DEFAULT
#---------------------
#Get
#---------------------
def get_Srssi():
    Brssi = 100
    for rssi in RSSI_min:
        if rssi < Brssi:
          Brssi =   rssi
    return Brssi

def get_id():
    return id_last