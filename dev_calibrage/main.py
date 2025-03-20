import em
from em import *
import mad
from mad import *
import xbeEm
from xbeEm import *
import horloge
from horloge import *

import machine
import struct
import time
import xbee

imu = ICM20948()
fuse = Fusion()

imu.set_gyro_sample_rate(1125)
imu.set_gyro_full_scale(2000)
imu.set_gyro_low_pass(True,7)
imu.set_accelerometer_sample_rate(1125)
imu.set_accelerometer_full_scale(16)
imu.set_accelerometer_low_pass(True,7)
user_led = machine.Pin('D9', machine.Pin.OUT)
user_button_pin = machine.Pin('D4', machine.Pin.IN, machine.Pin.PULL_UP)
xbee.atcmd('PL', 0)

def reaction(move, aax, aay, aaz, ggx, ggy, ggz, ax, ay, az, gx, gy, gz):
    if move < 3:
        diffs = {
            0: (abs(aax - ax), aax - ax),  
            1: (abs(aay - ay), aay - ay),
            2: (abs(aaz - az), aaz - az)
        }
    else:

        diffs = {
            0: (abs(ggx - gx), ggx - gx),
            1: (abs(ggy - gy), ggy - gy),
            2: (abs(ggz - gz), ggz - gz)
        }
    dominant_axis = max(diffs, key=lambda k: diffs[k][0])
    sign = "+" if diffs[dominant_axis][1] > 0 else "-"

    return dominant_axis, sign

def calibration(move, imu, ax_offset, ay_offset, az_offset, gx_offset, gy_offset, gz_offset):
    ax, ay, az, gx, gy, gz = imu.read_accelerometer_gyro_data()
    gx, gy, gz = gx - gx_offset, gy - gy_offset, gz - gz_offset
    ax, ay, az = ax - ax_offset, ay - ay_offset, az - az_offset

    while True:
        aax, aay, aaz, ggx, ggy, ggz = imu.read_accelerometer_gyro_data()
        ggx, ggy, ggz = ggx - gx_offset, ggy - gy_offset, ggz - gz_offset
        aax, aay, aaz = aax - ax_offset, aay - ay_offset, aaz - az_offset

        if move < 3:
            if abs(aax + aay + aaz - (ax + ay + az)) > 2:
                print(aax,aay,aaz,ax,ay,az)
                break
        else:
            if abs(ggx + ggy + ggz - (gx + gy + gz)) > 60:
                break

    return reaction(move, aax, aay, aaz, ggx, ggy, ggz, ax, ay, az, gx, gy, gz)

def waitu():
    while True:
        message = xbee.receive()
        if message is not None:
            payload = message['payload'].decode()
            payload = clean_payload(payload)
            print(payload)
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

def getmagne():
    x,y,z = imu.read_magnetometer_data()
    return x,y,z

fuse.calibrate(getmagne)

mag = imu.read_magnetometer_data()
ax, ay, az, gx, gy, gz = imu.read_accelerometer_gyro_data()
gx, gy, gz = gx-gx_offset,gy-gy_offset,gz-gz_offset
ax, ay, az = ax-ax_offset,ay-ay_offset,az-az_offset
accel = [ax, ay, az]
gyro = [gx, gy, gz]
start = time.ticks_us()
fuse.update_nomag(accel, gyro)
t = time.ticks_diff(time.ticks_us(), start)

ltt = time.ticks_ms()
retry_count = 0
m = 0
decalage = 0
horloge= 1

user_led.value(1)
decalage = main_horloge()

waitu()
user_led.value(0)
aaxes = [0,1,2]
gaxes = [0,1,2]
saaxes = ["+","+","+"]
sgaxes = ["+","+","+"]
i_move = 0
while i_move < 6:
    print(i_move)
    dom,sign = calibration(i_move, imu, ax_offset, ay_offset, az_offset, gx_offset, gy_offset, gz_offset)
    if i_move <3:
        aaxes[i_move] = dom
        saaxes[i_move] = sign
    else:
        gaxes[i_move%3] = dom
        sgaxes[i_move%3] = sign
    i_move = i_move + 1
    user_led.value(1)
    waitu()
    user_led.value(0)


while True:
    if user_button_pin.value() == 0:
        user()

    ax, ay, az, gx, gy, gz = imu.read_accelerometer_gyro_data()
    gx, gy, gz = gx-gx_offset,gy-gy_offset,gz-gz_offset
    ax, ay, az = ax-ax_offset,ay-ay_offset,az-az_offset
    x, y, z = imu.read_magnetometer_data()
    if ax != 0:
        receive_messages()
        if time.ticks_diff(time.ticks_ms(), ltt) >= 300:
            payload = "{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{}".format( ax, ay, az, gx, gy, gz, x, y, z, time.ticks_ms()+decalage)

            try:
                send_broadcast(payload.encode('utf-8'))  
                print(time.ticks_ms()-decalage)
                print(decalage)
                ltt = time.ticks_ms()
                retry_count = 0
                m = m + 1
            except Exception as ex:
                retry_count += 1
                ltt = time.ticks_ms()