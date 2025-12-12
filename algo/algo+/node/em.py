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

class DeltaT():
    def __init__(self, timediff):
        if timediff is None:
            self.expect_ts = False
            if is_micropython:
                self.timediff = lambda start, end : time.ticks_diff(start, end)/1000000
            else:
                raise ValueError('You must define a timediff function')
        else:
            self.expect_ts = True
            self.timediff = timediff
        self.start_time = None

    def __call__(self, ts):
        if self.expect_ts:
            if ts is None:
                raise ValueError('Timestamp expected but not supplied.')
        else:
            if is_micropython:
                ts = time.ticks_us()
            else:
                raise RuntimeError('Not MicroPython: provide timestamps and a timediff function')
        if self.start_time is None:
            self.start_time = ts
            return 0.0001

        dt = self.timediff(ts, self.start_time)
        self.start_time = ts
        return dt
        
def degrees(rad):
    return rad * 180 / pi
    
def radians(deg):
    return deg * pi / 180
    
def asin(x):
    if x < -1 or x > 1:
        raise ValueError("math domain error")
    sum = x
    term = x
    n = 1
    while True:
        term *= (x * x * (2 * n - 1) * (2 * n - 1)) / ((2 * n) * (2 * n + 1))
        new_sum = sum + term
        if abs(new_sum - sum) < 1e-10:
            return new_sum
        sum = new_sum
        n += 1
      
def sqrt(x):
    if x < 0:
        raise ValueError("math domain error")
    if x == 0:
        return 0
    guess = x / 2.0
    while True:
        better_guess = 0.5 * (guess + x / guess)
        if abs(better_guess - guess) < 1e-10:
            return better_guess
        guess = better_guess
    
def atan(x):
    if x == 0:
        return 0
    if x < 0:
        return -atan(-x)
    if x > 1:
        return pi / 2 - atan(1 / x)
    sum = x
    term = x
    n = 1
    while True:
        term *= -x * x * (2 * n - 1) / (2 * n + 1)
        new_sum = sum + term
        if abs(new_sum - sum) < 1e-10:
            return new_sum
        sum = new_sum
        n += 1

def atan2(y, x):
    if x > 0:
        return atan(y / x)
    elif x < 0 and y >= 0:
        return atan(y / x) + pi
    elif x < 0 and y < 0:
        return atan(y / x) - pi
    elif x == 0 and y > 0:
        return pi / 2
    elif x == 0 and y < 0:
        return -pi / 2
    else:
        return 0

class Fusion(object):
    declination = 0                         
    def __init__(self, timediff=None):
        self.magbias = (0, 0, 0)            
        self.deltat = DeltaT(timediff)      
        self.q = [1.0, 0.0, 0.0, 0.0]       
        GyroMeasError = radians(40)         
        self.beta = sqrt(3.0 / 4.0) * GyroMeasError 
        self.pitch = 0
        self.heading = 0
        self.roll = 0

    def calibrate(self, getxyz):
        magmax = list(getxyz())            
        magmin = magmax[:]
        timeD = 0
        while timeD < 60:
            timeD = timeD + 1
            magxyz = tuple(getxyz())
            for x in range(3):
                magmax[x] = max(magmax[x], magxyz[x])
                magmin[x] = min(magmin[x], magxyz[x])
        self.magbias = tuple(map(lambda a, b: (a +b)/2, magmin, magmax))


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
