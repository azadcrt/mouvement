import em
from em import *
import machine
import struct
import time
import xbee

i2c = machine.I2C(1)

fuse = Fusion()
Calibrate = True
Timing = True

i2c.writeto_mem(0x69, 0x7F, b'\x00')
write(0x06, 0x80)
time.sleep(0.01)
write(0x06, 0x01)
write(0x07, 0x00)

set_accelerometer_full_scale(16)
set_accelerometer_sample_rate(256)
set_accelerometer_low_pass(True, 5)
set_gyro_sample_rate(256)
set_gyro_low_pass(True, 5)
set_gyro_full_scale(2000)

i2c.writeto_mem(0x69, 0x7F, b'\x00')
write(0x0F, 0x30)

i2c.writeto_mem(0x69, 0x7F, b'\x30')
write(0x01, 0x4D)
write(0x02, 0x01)

mw(0x32, 0x01)
while mr(0x32) == 0x01:
    time.sleep(0.0001)

#xbee.atcmd('PL', 0)
    
def getmagne():
    z,y,z = rmd()
    return z,y,z

if Calibrate:
    print("debut")   
    fuse.calibrate(getmagne)
    print("calibration fini")

if Timing:
    mag = rmd()
    ax, ay, az, gx, gy, gz = ragd()
    accel = [ax, ay, az]
    gyro = [gx, gy, gz]
    start = time.ticks_us()
    fuse.update(accel, gyro, mag)
    t = time.ticks_diff(time.ticks_us(), start)

ltt = time.ticks_ms()
while True:

    receive_messages()
    ax, ay, az, gx, gy, gz = ragd()
    x, y, z = rmd()
    if ax != 0:
        fuse.update([ax, ay, az], [gx, gy, gz], [x, y, z])
        if time.ticks_diff(time.ticks_ms(), ltt) >= 5000:
            payload = str(fuse.q[0]) + ',' + str(fuse.q[1]) + ',' + str(fuse.q[2]) + ',' + str(fuse.q[3])
            #print(payload)
            #print(time.ticks_ms()/1000)
            try:
                send_broadcast(payload)
                ltt = time.ticks_ms()
            except Exception as ex:
                print(ex)

