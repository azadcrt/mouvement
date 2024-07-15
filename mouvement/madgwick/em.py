import machine
import struct
import time
import xbee


i2c = machine.I2C(1)

message_id = 0
received_messages = {}

local_eui64 = xbee.atcmd("SH") + xbee.atcmd("SL")

def sq(x):
    return x ** 0.5

class Quaternion:
    __slots__ = ['q']
    def __init__(self, w_or_q, x=None, y=None, z=None):
        if x is not None and y is not None and z is not None:
            self.q = [w_or_q, x, y, z]
        elif isinstance(w_or_q, Quaternion):
            self.q = w_or_q.q[:]
        else:
            q = list(w_or_q)
            if len(q) != 4:
                raise ValueError("Expecting a 4-element array or w x y z as parameters")
            self.q = q

    def conj(self):
        w, x, y, z = self.q
        return Quaternion(w, -x, -y, -z)

    def norm(self):
        return sq(sum(x * x for x in self.q))

    def mult(self, other):
        w1, x1, y1, z1 = self.q
        w2, x2, y2, z2 = other.q
        return Quaternion(
            w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
            w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
            w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
            w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2
        )

    def add(self, other):
        return Quaternion([self.q[i] + other.q[i] for i in range(4)])

    def mul(self, scalar):
        return Quaternion([scalar * x for x in self.q])

def madg(accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, mag_x, mag_y, mag_z, quaternion):
    samPer = 1 / 50
    beta = 1
    zeta = 0.1
    accm = [accel_x, accel_y, accel_z]
    gysc = [gyro_x, gyro_y, gyro_z]
    

    mag_y, mag_z = -mag_y, -mag_z
    magme = [mag_x, mag_y, mag_z]
    accel_norm = sq(sum(a * a for a in accm))
    mag_norm = sq(sum(m * m for m in magme))
    accm = [a / accel_norm for a in accm]
    magme = [m / mag_norm for m in magme]
    
    q = quaternion
    h = q.mult(Quaternion(0, magme[0], magme[1], magme[2])).mult(q.conj())
    b = [0, sq(h.q[1]**2 + h.q[2]**2), 0, h.q[3]]

    f = [
        2 * (q.q[1] * q.q[3] - q.q[0] * q.q[2]) - accm[0],
        2 * (q.q[0] * q.q[1] + q.q[2] * q.q[3]) - accm[1],
        2 * (0.5 - q.q[1]**2 - q.q[2]**2) - accm[2],
        2 * b[1] * (0.5 - q.q[2]**2 - q.q[3]**2) + 2 * b[3] * (q.q[1] * q.q[3] - q.q[0] * q.q[2]) - magme[0],
        2 * b[1] * (q.q[1] * q.q[2] - q.q[0] * q.q[3]) + 2 * b[3] * (q.q[0] * q.q[1] + q.q[2] * q.q[3]) - magme[1],
        2 * b[1] * (q.q[0] * q.q[2] + q.q[1] * q.q[3]) + 2 * b[3] * (0.5 - q.q[1]**2 - q.q[2]**2) - magme[2]
    ]

    j = [
        [-2 * q.q[2], 2 * q.q[3], -2 * q.q[0], 2 * q.q[1]],
        [2 * q.q[1], 2 * q.q[0], 2 * q.q[3], 2 * q.q[2]],
        [0, -4 * q.q[1], -4 * q.q[2], 0],
        [-2 * b[3] * q.q[2], 2 * b[3] * q.q[3], -4 * b[1] * q.q[2] - 2 * b[3] * q.q[0], -4 * b[1] * q.q[3] + 2 * b[3] * q.q[1]],
        [-2 * b[1] * q.q[3] + 2 * b[3] * q.q[1], 2 * b[1] * q.q[2] + 2 * b[3] * q.q[0], 2 * b[1] * q.q[1] + 2 * b[3] * q.q[3], -2 * b[1] * q.q[0] + 2 * b[3] * q.q[2]],
        [2 * b[1] * q.q[2], 2 * b[1] * q.q[3] - 4 * b[3] * q.q[1], 2 * b[1] * q.q[0] - 4 * b[3] * q.q[2], 2 * b[1] * q.q[1]]
    ]

    step = [sum(j[i][k] * f[k] for k in range(4)) for i in range(4)]
    step_norm = sq(sum(s * s for s in step))
    step = [s / step_norm for s in step]

    gyroQuat = Quaternion(0, gysc[0], gysc[1], gysc[2])
    stepQuat = Quaternion(step[0], step[1], step[2], step[3])
    gyroQuat = gyroQuat.add(q.conj().mult(stepQuat)).mul(2 * samPer * zeta * -1)
    qdot = q.mult(gyroQuat).mul(0.5).add(stepQuat.mul(-beta))
    q = Quaternion([q.q[i] + qdot.q[i] * samPer for i in range(4)])
    quat = Quaternion([q.q[i] / q.norm() for i in range(4)])
    return quat

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
    return x * 0.15, y * 0.15, z * 0.15

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

eui64_hash = eui64_to_hash(local_eui64)

def create_message(message, message_id, path):
    path_str = ",".join(path)
    full_message = f"{message_id}:{path_str}:{message}"
    return full_message

def send_broadcast(message):
    global message_id
    full_message = create_message(message, message_id, [local_eui64.decode()])
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
        message = ":".join(parts[2:])
        
        if sender in received_messages:
            last_message_id = int(received_messages[sender])
        else:
            last_message_id = -1
            
        message_id = int(message_id_str)
        
        if message_id > last_message_id:
            received_messages[sender] = message_id_str
            path.append(local_eui64.decode())
            full_message = create_message(message, message_id_str, path)
            xbee.transmit(xbee.ADDR_BROADCAST, full_message.encode())
            print(f"Message retransmis: {full_message}")
    except Exception as e:
        print("Erreur lors de la gestion du message reçu:", e)

def receive_messages():
    try:
        data = xbee.receive()
        if data:
            handle_received_message(data['payload'],data['sender_eui64'])
    except Exception as e:
        print("Erreur lors de la réception du message:", e)

        


