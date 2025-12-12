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
def ecrire_log(sender, etat):
    global log
    
    print("login", sender)
    if sender not in log:
        
        log[sender] = (0, 0)
        print("ft",sender)
    try:  
        log[sender] = (log[sender][0] + etat, log[sender][1] + 1)
    except Exception as e:
        print(e)
    

def user():
    global log
    try:
        with open('/flash/test.txt', 'w') as file:
            json.dump(log, file)
        print("Log sauvegardé avec succès.")
    except Exception as e:
        print("Erreur lors de la sauvegarde du log ")

def create_message(message, message_id, path,Srssi):
    print()
    path_str = ",".join(path)
    full_message = "{}:{}:{}:{}".format(message_id, path_str, Srssi, message)
    print(full_message)
    return full_message

def send_broadcast(message,Srssi):
    global message_id
    print("dans send")
    full_message = create_message(message, message_id, [''.join('{:02x}'.format(b) for b in local_eui64)],Srssi)#ici
    try:
        xbee.transmit(xbee.ADDR_BROADCAST, full_message.encode())
        print("Message broadcast envoyé avec succès:")
        message_id += 1
        ecrire_log([''.join('{:02x}'.format(b) for b in local_eui64)], 1)
    except Exception as e:
        print("Erreur lors de l'envoi du message:", e)
        ecrire_log([''.join('{:02x}'.format(b) for b in local_eui64)], 0)

def handle_received_message(data, sender, Srssi):
    global received_messages
    print("je viens de: ", sender)
    try:
        message_str = data.strip()
        parts = message_str.split(":")
        message_id_str = parts[0]
        message_rssi_str = parts[2]
        if message_rssi_str > Srssi:
            path = parts[1].split(",")
            message = ":".join(parts[2:])
            
            if sender in received_messages:
                last_message_id = int(received_messages[sender])
            else:
                last_message_id = -1
                
            message_id = int(message_id_str)
            
            if message_id > last_message_id:
                received_messages[sender] = message_id_str
                path.append("{}".format([''.join('{:02x}'.format(b) for b in local_eui64)]))
                full_message = create_message(message, message_id_str, path)
                xbee.transmit(xbee.ADDR_BROADCAST, full_message.encode())
                ecrire_log(sender, 1)
                print("Message retransmit avec succès:")
        else:
            xbee.receive()

    except Exception as e:
        print("Erreur lors de la gestion du message reçu de:")
        ecrire_log(sender, 0)
    

def handle_received_message_direct(data, sender):
    global received_messages
    print("je viens de: ", sender)
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
            path.append("{}".format([''.join('{:02x}'.format(b) for b in local_eui64)]))
            full_message = create_message(message, message_id_str, path)
            remote = b'\x00\x13\xa2\x00\x42\x1b\xd0\xe6'
            xbee.transmit(remote, full_message.encode())
            ecrire_log(sender, 1)
            print("Message retransmit avec succès:")
    except Exception as e:
        print("Erreur lors de la gestion du message reçu de")
        ecrire_log(sender, 0)

def receive_messages(Srssi):
    try:
        data = xbee.receive()
        if data:
            dat = data['payload']
            pay = dat.decode().strip()
            
            parts = pay.split(":")
            path = parts[1].split(",")
            sender = path[0]

            # Comparaison du sender avec local_eui64 en format hexadécimal
            if sender != [''.join('{:02x}'.format(b) for b in local_eui64)]:#ici
                handle_received_message(pay, sender,Srssi)
            return 1
        else:
            return 0
                
    
    except Exception as e:
        print("Erreur lors de la réception du message: ")

def receive_messages_direct():
    try:
        data = xbee.receive()
        if data:
            dat = data['payload']
            pay = dat.decode().strip()
            
            parts = pay.split(":")
            path = parts[1].split(",")
            sender = path[0]

            # Comparaison du sender avec local_eui64 en format hexadécimal
            if sender != [''.join('{:02x}'.format(b) for b in local_eui64)]:#ici
                handle_received_message_direct(pay, sender)
            return 1
        else:
            return 0
                
    
    except Exception as e:
        print("Erreur lors de la réception du message:")
