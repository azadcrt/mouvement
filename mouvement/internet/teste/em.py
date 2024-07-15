import machine
import struct
import time
import xbee


i2c = machine.I2C(1)

message_id = 0
received_messages = {}
pi = 3.141592653589793
local_eui64 = xbee.atcmd("SH") + xbee.atcmd("SL")
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
        
    def update(self, accel, gyro, mag, ts=None):     
        mx, my, mz = (mag[x] - self.magbias[x] for x in range(3))
        ax, ay, az = accel
        gx, gy, gz = (radians(x) for x in gyro)
        q1, q2, q3, q4 = (self.q[x] for x in range(4))

        _2q1 = 2 * q1
        _2q2 = 2 * q2
        _2q3 = 2 * q3
        _2q4 = 2 * q4
        _2q1q3 = 2 * q1 * q3
        _2q3q4 = 2 * q3 * q4
        q1q1 = q1 * q1
        q1q2 = q1 * q2
        q1q3 = q1 * q3
        q1q4 = q1 * q4
        q2q2 = q2 * q2
        q2q3 = q2 * q3
        q2q4 = q2 * q4
        q3q3 = q3 * q3
        q3q4 = q3 * q4
        q4q4 = q4 * q4

        # Normalise accelerometer measurement
        norm = sqrt(ax * ax + ay * ay + az * az)
        if (norm == 0):
            return # handle NaN
        norm = 1 / norm                    
        ax *= norm
        ay *= norm
        az *= norm

        # Normalise magnetometer measurement
        norm = sqrt(mx * mx + my * my + mz * mz)
        if (norm == 0):
            return                          
        norm = 1 / norm                     
        mx *= norm
        my *= norm
        mz *= norm

        # Reference direction of Earth's magnetic field
        _2q1mx = 2 * q1 * mx
        _2q1my = 2 * q1 * my
        _2q1mz = 2 * q1 * mz
        _2q2mx = 2 * q2 * mx
        hx = mx * q1q1 - _2q1my * q4 + _2q1mz * q3 + mx * q2q2 + _2q2 * my * q3 + _2q2 * mz * q4 - mx * q3q3 - mx * q4q4
        hy = _2q1mx * q4 + my * q1q1 - _2q1mz * q2 + _2q2mx * q3 - my * q2q2 + my * q3q3 + _2q3 * mz * q4 - my * q4q4
        _2bx = sqrt(hx * hx + hy * hy)
        _2bz = -_2q1mx * q3 + _2q1my * q2 + mz * q1q1 + _2q2mx * q4 - mz * q2q2 + _2q3 * my * q4 - mz * q3q3 + mz * q4q4
        _4bx = 2 * _2bx
        _4bz = 2 * _2bz

        # Gradient descent algorithm corrective step
        s1 = (-_2q3 * (2 * q2q4 - _2q1q3 - ax) + _2q2 * (2 * q1q2 + _2q3q4 - ay) - _2bz * q3 * (_2bx * (0.5 - q3q3 - q4q4)
             + _2bz * (q2q4 - q1q3) - mx) + (-_2bx * q4 + _2bz * q2) * (_2bx * (q2q3 - q1q4) + _2bz * (q1q2 + q3q4) - my)
             + _2bx * q3 * (_2bx * (q1q3 + q2q4) + _2bz * (0.5 - q2q2 - q3q3) - mz))

        s2 = (_2q4 * (2 * q2q4 - _2q1q3 - ax) + _2q1 * (2 * q1q2 + _2q3q4 - ay) - 4 * q2 * (1 - 2 * q2q2 - 2 * q3q3 - az)
             + _2bz * q4 * (_2bx * (0.5 - q3q3 - q4q4) + _2bz * (q2q4 - q1q3) - mx) + (_2bx * q3 + _2bz * q1) * (_2bx * (q2q3 - q1q4)
             + _2bz * (q1q2 + q3q4) - my) + (_2bx * q4 - _4bz * q2) * (_2bx * (q1q3 + q2q4) + _2bz * (0.5 - q2q2 - q3q3) - mz))

        s3 = (-_2q1 * (2 * q2q4 - _2q1q3 - ax) + _2q4 * (2 * q1q2 + _2q3q4 - ay) - 4 * q3 * (1 - 2 * q2q2 - 2 * q3q3 - az)
             + (-_4bx * q3 - _2bz * q1) * (_2bx * (0.5 - q3q3 - q4q4) + _2bz * (q2q4 - q1q3) - mx)
             + (_2bx * q2 + _2bz * q4) * (_2bx * (q2q3 - q1q4) + _2bz * (q1q2 + q3q4) - my)
             + (_2bx * q1 - _4bz * q3) * (_2bx * (q1q3 + q2q4) + _2bz * (0.5 - q2q2 - q3q3) - mz))

        s4 = (_2q2 * (2 * q2q4 - _2q1q3 - ax) + _2q3 * (2 * q1q2 + _2q3q4 - ay) + (-_4bx * q4 + _2bz * q2) * (_2bx * (0.5 - q3q3 - q4q4)
              + _2bz * (q2q4 - q1q3) - mx) + (-_2bx * q1 + _2bz * q3) * (_2bx * (q2q3 - q1q4) + _2bz * (q1q2 + q3q4) - my)
              + _2bx * q2 * (_2bx * (q1q3 + q2q4) + _2bz * (0.5 - q2q2 - q3q3) - mz))

        norm = 1 / sqrt(s1 * s1 + s2 * s2 + s3 * s3 + s4 * s4)   
        s1 *= norm
        s2 *= norm
        s3 *= norm
        s4 *= norm

        # Compute rate of change of quaternion
        qDot1 = 0.5 * (-q2 * gx - q3 * gy - q4 * gz) - self.beta * s1
        qDot2 = 0.5 * (q1 * gx + q3 * gz - q4 * gy) - self.beta * s2
        qDot3 = 0.5 * (q1 * gy - q2 * gz + q4 * gx) - self.beta * s3
        qDot4 = 0.5 * (q1 * gz + q2 * gy - q3 * gx) - self.beta * s4

        # Integrate to yield quaternion
        deltat = self.deltat(ts)
        q1 += qDot1 * deltat
        q2 += qDot2 * deltat
        q3 += qDot3 * deltat
        q4 += qDot4 * deltat
        norm = 1 / sqrt(q1 * q1 + q2 * q2 + q3 * q3 + q4 * q4)    
        self.q = q1 * norm, q2 * norm, q3 * norm, q4 * norm
        self.heading = self.declination + degrees(atan2(2.0 * (self.q[1] * self.q[2] + self.q[0] * self.q[3]),
            self.q[0] * self.q[0] + self.q[1] * self.q[1] - self.q[2] * self.q[2] - self.q[3] * self.q[3]))
        self.pitch = degrees(-asin(2.0 * (self.q[1] * self.q[3] - self.q[0] * self.q[2])))
        self.roll = degrees(atan2(2.0 * (self.q[0] * self.q[1] + self.q[2] * self.q[3]),
            self.q[0] * self.q[0] - self.q[1] * self.q[1] - self.q[2] * self.q[2] + self.q[3] * self.q[3]))


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
        
def eui64_to_hash(eui64):
    return ''.join('{:02X}'.format(b) for b in eui64)

# Adresse EUI-64 locale
local_eui64 = xbee.atcmd("SH") + xbee.atcmd("SL")
eui64_hash = eui64_to_hash(local_eui64)
message_id = 0
received_messages = {}

def create_message(message, message_id, path, rssi_list, start_time):
    path_str = ",".join(path)
    rssi_str = ",".join(map(str, rssi_list))  # Convertir les éléments de rssi_list en chaînes
    full_message = f"{message_id}:{path_str}:{rssi_str}:{start_time}:{message}"
    return full_message

def send_broadcast(message):
    global message_id
    start_time = time.ticks_us()
    rssi_list = [0]  # Initialisation de la liste des RSSI
    full_message = create_message(message, message_id, [local_eui64.decode()], rssi_list, start_time)
    try:
        xbee.transmit(xbee.ADDR_BROADCAST, full_message.encode())
        print(f"Message broadcast envoyé avec succès: {full_message}")
        message_id += 1
    except Exception as e:
        print("Erreur lors de l'envoi du message:", e)

def handle_received_message(data, sender):
    global received_messages
    try:
        message_str = data.decode('utf-8').strip()
        parts = message_str.split(":")
        message_id_str = parts[0]
        
        path = parts[1].split(",")
        rssi = parts[2].split(",")
        start_time = parts[3]
        message = ":".join(parts[4:])
        
        if sender in received_messages:
            last_message_id = int(received_messages[sender])
        else:
            last_message_id = -1
            
        message_id = int(message_id_str)
        
        if message_id > last_message_id:
            received_messages[sender] = message_id_str
            path.append(local_eui64.decode())
            new_rssi = xbee.atcmd("DB")  # RSSI de la retransmission
            rssi.append(new_rssi)
            full_message = create_message(message, message_id_str, path, rssi, start_time)
            xbee.transmit(xbee.ADDR_BROADCAST, full_message.encode())
            print(f"Message retransmis: {full_message}")
    except Exception as e:
        print("Erreur lors de la gestion du message reçu:", e)

def receive_messages():
    try:
        data = xbee.receive()
        if data:
            handle_received_message(data['payload'], data['sender_eui64'])
    except Exception as e:
        print("Erreur lors de la réception du message:", e)
