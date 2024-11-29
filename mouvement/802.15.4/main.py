import em
from em import *
import mad
from mad import *
import machine
import struct
import time
import xbee


i2c = machine.I2C(1)

fuse = Fusion()
Calibrate = True
Timing = True

user_button_pin = machine.Pin('D4', machine.Pin.IN, machine.Pin.PULL_UP)

i2c.writeto_mem(0x69, 0x7F, b'\x00')
write(0x06, 0x80)
time.sleep(0.01)
write(0x06, 0x01)
write(0x07, 0x00)

set_accelerometer_full_scale(4)
set_accelerometer_sample_rate(100)
set_accelerometer_low_pass(True, 5)
set_gyro_sample_rate(200)
set_gyro_low_pass(True, 5)
set_gyro_full_scale(500)

i2c.writeto_mem(0x69, 0x7F, b'\x00')
write(0x0F, 0x30)
i2c.writeto_mem(0x69, 0x7F, b'\x30')
write(0x01, 0x4D)
write(0x02, 0x01)

mw(0x32, 0x01)
while mr(0x32) == 0x01:
    time.sleep(0.0001)

xbee.atcmd('PL', 0)
    
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
retry_count = 0
m = 0

while True:
    if user_button_pin.value() == 0:
    #if m == 50:
        user()

    ax, ay, az, gx, gy, gz = ragd()
    x, y, z = rmd()
    if ax != 0:
        fuse.update([ax, ay, az], [gx, gy, gz], [x, y, z])
        #receive_messages()
        receive_messages()
        #time.sleep(0.5)

        if time.ticks_diff(time.ticks_ms(), ltt) >= 300:
            payload = "{:.2f},{:.2f},{:.2f},{:.2f}".format(fuse.q[0], fuse.q[1], fuse.q[2], fuse.q[3])

            try:
                send_broadcast(payload.encode('utf-8'))      
                ltt = time.ticks_ms()
                retry_count = 0
                m = m + 1
            except Exception as ex:
                print("Erreur :", ex)
                retry_count += 1
                ltt = time.ticks_ms()  # Réinitialise le temps pour attendre une nouvelle tentative
                if retry_count >= 5:  # Limite le nombre de tentatives rapides
                    time.sleep(1)  # Pause plus longue après plusieurs échecs
                    retry_count = 0
                else:
                    time.sleep_ms(200)  # Pause courte pour donner au buffer le temps de se libérer

           