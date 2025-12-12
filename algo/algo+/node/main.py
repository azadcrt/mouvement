import em
from em import *
import comm
from comm import *
import horloge
from horloge import *
import algo
from algo import *

import machine
import struct
import time
import xbee

imu = ICM20948()

imu.set_gyro_sample_rate(1125)
imu.set_gyro_full_scale(2000)
imu.set_gyro_low_pass(True,7)
imu.set_accelerometer_sample_rate(1125)
imu.set_accelerometer_full_scale(16)
imu.set_accelerometer_low_pass(True,7)
user_led = machine.Pin('D9', machine.Pin.OUT)
user_button_pin = machine.Pin('D4', machine.Pin.IN, machine.Pin.PULL_UP)
xbee.atcmd('PL', 0)
rand = id(object())%100
direct = False
lid = 0
PowerLimit = 100
Srssi = 100

def waitu():
    while True:
        message = xbee.receive()
        if message is not None:
            try:
                payload = message['payload'].decode()
                payload = clean_payload(payload)
                if float(payload) == 1.0:
                    break
            finally:
                print("")


i = 0
gx_offset = 0
gy_offset = 0
gz_offset = 0
ax_offset = 0
ay_offset = 0
az_offset = 0

waitu()

while i < 100:
    ax, ay, az, gx, gy, gz = imu.read_accelerometer_gyro_data()
    gx_offset = gx_offset +gx
    gy_offset = gy_offset +gy
    gz_offset = gz_offset +gz
    ax_offset = ax_offset +ax
    ay_offset = ay_offset +ay
    az_offset = az_offset + az-1 
    i = i + 1

gx_offset = gx_offset/i
gy_offset = gy_offset/i
gz_offset = gz_offset/i 
ax_offset = ax_offset/i
ay_offset = ay_offset/i
az_offset = az_offset/i 

mag = imu.read_magnetometer_data()
ax, ay, az, gx, gy, gz = imu.read_accelerometer_gyro_data()
gx, gy, gz = gx-gx_offset,gy-gy_offset,gz-gz_offset
ax, ay, az = ax-ax_offset,ay-ay_offset,az-az_offset
accel = [ax, ay, az]
gyro = [gx, gy, gz]
start = time.ticks_us()
t = time.ticks_diff(time.ticks_us(), start)

ltt = time.ticks_ms()
retry_count = 0
m = 0
decalage = 0
horloge= 1

user_led.value(1)
decalage = main_horloge()

waitu()
idA = 0
see = []

while idA < 6:
    rssi_db = xbee.atcmd("DB")
    if rssi_db < PowerLimit:
        try:
            idA,jmpA,rssiA = algo.received_message()
            print(idA,jmpA,rssiA)
        except Exception as ex:
            ex = ""
    if idA not in see:
        see.append(idA)
        try:
            algo.resend(idA,jmpA,rssiA)
        except Exception as ex:
            print(ex)
        
bol,Vrssi = algo.decision(lid)

Srssi=algo.get_Srssi()       

remote = b'\x00\x13\xa2\x00\x42\x1b\xd0\xe6'
while True:
    if user_button_pin.value() == 0:
        user()

    ax, ay, az, gx, gy, gz = imu.read_accelerometer_gyro_data()
    gx, gy, gz = gx-gx_offset,gy-gy_offset,gz-gz_offset
    ax, ay, az = ax-ax_offset,ay-ay_offset,az-az_offset
    x, y, z = imu.read_magnetometer_data()
    rssi_db = xbee.atcmd("DB")  # 'DB' = dBm, sans le signe
    if rssi_db is not None:
        if rssi_db < PowerLimit:
            if direct:
                comm.receive_messages_direct()
            else:
                comm.receive_messages(Srssi)
        else:
            # Juste vider le buffer sans traitement
            xbee.receive()

    if ax != 0:
        if time.ticks_diff(time.ticks_ms(), ltt) >= 300:
            payload = "{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{}".format( ax, ay, az, gx, gy, gz, x, y, z, time.ticks_ms()-decalage)

            try:
                if direct:
                    print("here")
                    xbee.transmit(remote,payload)
                else:
                    print("ici")
                    comm.send_broadcast(payload.encode('utf-8'),Srssi)

                ltt = time.ticks_sms()
                retry_count = 0
                m = m + 1
            except Exception as ex:
                print(ex)
                retry_count += 1
                ltt = time.ticks_ms()