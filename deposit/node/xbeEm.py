import machine
import struct
import time
import xbee
import os
import json

message_id = 0
received_messages = {}
log = {}
pi = 3.141592653589793
local_eui64 = xbee.atcmd("SL")

is_micropython = hasattr(time, 'ticks_diff')

def ecrire_log(sender, etat,time):
    global log
    
    print("login", sender)
    if sender not in log:
        
        log[sender] = (0, 0)
        print("ft",sender)
    try:  
        log[sender] = (log[sender][0] + etat, log[sender][1] + 1,time)
    except Exception as e:
        print(e)
    

def user():
    global log
    try:
        with open('/flash/test.txt', 'w') as file:
            json.dump(log, file)
        print("Log sauvegardé avec succès.")
    except Exception as e:
        print("Erreur lors de la sauvegarde du log : {e}")
        

def create_message(message, message_id, path):
    path_str = ",".join(path)
    full_message = "%s:%s:%s" % (message_id, path_str, message)
    return full_message

def send_try_broadcast(message,time):
    global message_id
    full_message = create_message(message, message_id, [local_eui64.hex()])#ici
    try:
        xbee.transmit(xbee.ADDR_BROADCAST, full_message.encode())
        print("Message broadcast envoyé avec succès: {full_message}")
        message_id += 1
        ecrire_log(local_eui64.hex(), 1,time)
        return 0
    except Exception as e:
        print("Erreur lors de l'envoi du message:", e)
        return 1
        #ecrire_log(local_eui64.hex(), 0,time)

def send_broadcast(message,time):
    global message_id
    full_message = create_message(message, message_id, [''.join('{:02x}'.format(b) for b in local_eui64)])#ici
    try:
        xbee.transmit(xbee.ADDR_BROADCAST, full_message.encode())
        print("Message broadcast envoyé avec succès: {full_message}")
        message_id += 1
        ecrire_log(''.join('{:02x}'.format(b) for b in local_eui64), 1,time)
    except Exception as e:
        print("Erreur lors de l'envoi du message:", e)
        ecrire_log(''.join('{:02x}'.format(b) for b in local_eui64), 0,time)

def handle_received_message(data, sender,time):
    global received_messages
    print("je viens de: ", sender)
    print("avec comme data: ", data)
    try:
        message_str = data.strip()
        parts = message_str.split(":")
        message_id_str = parts[0]
        
        path = parts[1].split(",")
        message = ":".join(parts[2:])
        
        if sender in received_messages:
            last_message_id = int(received_messages[sender])
        else:
            last_message_id = -1
            
        message_id = int(message_id_str)
        
        if message_id > last_message_id:
            received_messages[sender] = message_id_str
            
            rssi = xbee.atcmd("DB")
            
            path.append("%s:%d" % (''.join('{:02x}'.format(b) for b in local_eui64), rssi))
            full_message = create_message(message, message_id_str, path)
            xbee.transmit(xbee.ADDR_BROADCAST, full_message.encode())
            ecrire_log(sender, 1,time)
            print("Message retransmit avec succès: {full_message}")
    except Exception as e:
        print("Erreur lors de la gestion du message reçu de: {e}")
        ecrire_log(sender, 0,time)

def receive_messages(time):
    try:
        data = xbee.receive()
        if data:
            dat = data['payload']
            pay = dat[6:].decode().strip()
            
            parts = pay.split(":")
            path = parts[1].split(",")
            sender = path[0]

            # Comparaison du sender avec local_eui64 en format hexadécimal
            if sender != ''.join('{:02x}'.format(b) for b in local_eui64):#ici
                handle_received_message(pay, sender,time)
            return 1
        else:
            return 0
                
    
    except Exception as e:
        print("Erreur lors de la réception du message: {e}")


