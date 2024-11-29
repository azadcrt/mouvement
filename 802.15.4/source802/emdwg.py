import machine
import struct
import time
import xbee
import os
import json

i2c = machine.I2C(1)

message_id = 0
received_messages = {}
log = {}
pi = 3.141592653589793
local_eui64 = xbee.atcmd("SL")

is_micropython = hasattr(time, 'ticks_diff')

def write(reg, value):
    val = bytes([value])
    i2c.writeto_mem(0x69, reg, val, addrsize=8)
    time.sleep(0.0001)

def read(reg, length=1):
    data = i2c.readfrom_mem(0x69, reg, length, addrsize=8)
    return int.from_bytes(data, 'little')

def tmio():
    user = read(0x03)
    write(0x03, user | 0x20)
    time.sleep(0.005)
    write(0x03, user)

def mw(reg, value):
    i2c.writeto_mem(0x69, 0x7F, b'\x30')
    write(0x03, 0x0c)
    write(0x04, reg)
    write(0x06, value)
    i2c.writeto_mem(0x69, 0x7F, b'\x00')
    tmio()

def mr(reg):
    i2c.writeto_mem(0x69, 0x7F, b'\x30')
    write(0x69, 0x7F | 0x80)
    write(0x03, reg)
    write(0x04, 0xff)
    write(0x05, 0x80 | 1)
    i2c.writeto_mem(0x69, 0x7F, b'\x00')
    tmio()
    return read(0x3B)

def rmd():
    mw(0x31, 0x01)
    time.sleep(0.0001)
    i2c.writeto_mem(0x69, 0x7F, b'\x30')
    write(0x05, 0x80 | 0x08 | 6)
    write(0x03, 0x0c | 0x80)
    write(0x04, 0x11)
    write(0x06, 0xff)
    i2c.writeto_mem(0x69, 0x7F, b'\x00')
    tmio()
    data = i2c.readfrom_mem(0x69, 0x3B, 6, addrsize=8)
    x, y, z = struct.unpack("<hhh", bytearray(data))
    return x * 0.15, -y * 0.15, -z * 0.15

def ragd():
    i2c.writeto_mem(0x69, 0x7F, b'\x00')
    data = i2c.readfrom_mem(0x69, 0x2D, 12, addrsize=8)
    ax, ay, az, gx, gy, gz = struct.unpack(">hhhhhh", bytearray(data))
    i2c.writeto_mem(0x69, 0x7F, b'\x20')
    gs = 2048.0
    ax /= gs
    ay /= gs
    az /= gs
    dps = 16.4
    gx /= dps
    gy /= dps
    gz /= dps
    return ax, ay, az, gx, gy, gz
    
def set_accelerometer_full_scale(scale=16):
    i2c.writeto_mem(0x69, 0x7F, b'\x20')
    value = read(0x14) & 0b11111001
    value |= {2: 0b00, 4: 0b01, 8: 0b10, 16: 0b11}[scale] << 1
    write(0x14, value)
        
def set_accelerometer_sample_rate(rate=125):
    ICM20948_ACCEL_SMPLRT_DIV_1 = 0x10
    ICM20948_ACCEL_SMPLRT_DIV_2 = 0x11
    i2c.writeto_mem(0x69, 0x7F, b'\x20')
    # 125Hz - 1.125 kHz / (1 + rate)
    rate = int((1125.0 / rate) - 1)
    write(ICM20948_ACCEL_SMPLRT_DIV_1, (rate >> 8) & 0xff)
    write(ICM20948_ACCEL_SMPLRT_DIV_2, rate & 0xff)

def set_accelerometer_low_pass(enabled=True, mode=5):
    i2c.writeto_mem(0x69, 0x7F, b'\x20')
    value = read(0x14) & 0b10001110
    if enabled:
        value |= 0b1
    value |= (mode & 0x07) << 4
    write(0x14, value)
        
def set_gyro_sample_rate(rate=125):
    ICM20948_GYRO_SMPLRT_DIV = 0x00
    i2c.writeto_mem(0x69, 0x7F, b'\x20')
    rate = int((1125.0 / rate) - 1)
    write(ICM20948_GYRO_SMPLRT_DIV, rate)

def set_gyro_full_scale(scale=250):
    i2c.writeto_mem(0x69, 0x7F, b'\x20')
    value = read(0x01) & 0b11111001
    value |= {250: 0b00, 500: 0b01, 1000: 0b10, 2000: 0b11}[scale] << 1
    write(0x01, value)

def set_gyro_low_pass(enabled=True, mode=5):
    i2c.writeto_mem(0x69, 0x7F, b'\x20')
    value = read(0x01) & 0b10001110
    if enabled:
        value |= 0b1
    value |= (mode & 0x07) << 4
    write(0x01, value)

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
        print("Erreur lors de la sauvegarde du log : {e}")
        

def create_message(message, message_id, path):
    path_str = ",".join(path)
    full_message = "%s:%s:%s" % (message_id, path_str, message)
    return full_message

def send_try_broadcast(message):
    global message_id
    full_message = create_message(message, message_id, [local_eui64.hex()])#ici
    try:
        xbee.transmit(xbee.ADDR_BROADCAST, full_message.encode())
        print("Message broadcast envoyé avec succès: {full_message}")
        message_id += 1
        ecrire_log(local_eui64.hex(), 1)
        return 0
    except Exception as e:
        print("Erreur lors de l'envoi du message:", e)
        return 1
        #ecrire_log(local_eui64.hex(), 0)

def send_broadcast(message):
    global message_id
    full_message = create_message(message, message_id, [''.join('{:02x}'.format(b) for b in local_eui64)])#ici
    try:
        xbee.transmit(xbee.ADDR_BROADCAST, full_message.encode())
        print("Message broadcast envoyé avec succès: {full_message}")
        message_id += 1
        ecrire_log(''.join('{:02x}'.format(b) for b in local_eui64), 1)
    except Exception as e:
        print("Erreur lors de l'envoi du message:", e)
        ecrire_log(''.join('{:02x}'.format(b) for b in local_eui64), 0)

def handle_received_message(data, sender):
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
            ecrire_log(sender, 1)
            print("Message retransmit avec succès: {full_message}")
    except Exception as e:
        print("Erreur lors de la gestion du message reçu de: {e}")
        ecrire_log(sender, 0)

def receive_messages():
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
                handle_received_message(pay, sender)
            return 1
        else:
            return 0
                
    
    except Exception as e:
        print("Erreur lors de la réception du message: {e}")


