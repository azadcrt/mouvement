import em
from em import *
import xbeEm
from xbeEm import *
import horloge
from horloge import *

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
xbee.atcmd('PL', 4)
rand = id(object())%100

def waitu():
    while True:
        message = xbee.receive()
        if message is not None:
            payload = message['payload'].decode()
            payload = clean_payload(payload)
            if float(payload) == 1.0:
                break


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

while True:
    if user_button_pin.value() == 0:
        user()

    ax, ay, az, gx, gy, gz = imu.read_accelerometer_gyro_data()
    gx, gy, gz = gx-gx_offset,gy-gy_offset,gz-gz_offset
    ax, ay, az = ax-ax_offset,ay-ay_offset,az-az_offset
    x, y, z = imu.read_magnetometer_data()
    rssi_db = xbee.atcmd("DB")  # 'DB' = dBm, sans le signe
    if rssi_db is not None:
        if rssi_db < 50:  # -70 dBm ou mieux
            receive_messages()
        else:
            # Juste vider le buffer sans traitement
            xbee.receive()  # on consomme le message

    if ax != 0:
        if time.ticks_diff(time.ticks_ms(), ltt) >= 300:
            payload = "{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{}".format( ax, ay, az, gx, gy, gz, x, y, z, time.ticks_ms()-decalage)

            try:
                send_broadcast(payload.encode('utf-8'))
                ltt = time.ticks_ms()
                retry_count = 0
                m = m + 1
            except Exception as ex:
                retry_count += 1
                ltt = time.ticks_ms()