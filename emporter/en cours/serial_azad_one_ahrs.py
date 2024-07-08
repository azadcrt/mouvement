import serial
import socket
from quaternion import Quaternion
import time

port_name = '/dev/ttyUSB0'
baud_rate = 9600

HOST = '127.0.0.1' 
PORT = 12345   

etallonage = [Quaternion(10, 10, 10, 10) for _ in range(5)]

def eui64_to_hex(eui64_bytes):
    return ''.join('{:02X}'.format(b) for b in eui64_bytes)

def send_data(obj_name, quaternion):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((HOST, PORT))
        quaternion_data = Quaternion.getFloor(quaternion)
        data = f"{obj_name}:{quaternion_data}"
        client_socket.sendall(data.encode())
        print(f"Données envoyées avec succès au serveur Blender: {data}")

known_eui64 = [
    "62275C7830305C7831335C7861325C783030425C7831625C7864335C78613927",
       "62275C7830305C7831335C7861325C783030425C7831625C7864343C27",
       "62275C7830305C7831335C7861325C783030425C7831625C7864305C78653827",
       "62275C7830305C7831335C7861325C783030425C7831625C7864335C78643427",
       "62275C7830305C7831335C7861325C783030425C7831645C7861355C78633127"
]
object_names = ["upperarm_RL", "upperarm_R", "lowerarm_R", "clavicle_L", "clavicle_R"]

try:
    with serial.Serial(port_name, baud_rate) as ser:
        while True:
            try:
                data = ser.readline().decode('ascii', errors='replace').strip()
                values = data.split()
                if len(values) >= 7:
                    try:
                        eui64_hex = eui64_to_hex(values[-2].encode('ascii'))
                        print(values)
                        if eui64_hex in known_eui64:
                            ind = known_eui64.index(eui64_hex)
                            obj_name = object_names[ind]
                            quaternion = Quaternion(float(values[-6]), float(values[-5]), float(values[-4]), float(values[-3]))
                            if etallonage[ind].q[1] == 10:
                                etallonage[ind].q[1] = 20
                            elif etallonage[ind].q[1] == 20:
                                etallonage[ind] = quaternion.conj()
                            else:
                                #quaternion = quaternion * etallonage[ind]
                                send_data(obj_name, quaternion)
                                print(obj_name, quaternion)
                        else:
                            print(f"EUI64 inconnu: {eui64_hex}")
                    except ValueError as e:
                        print(f"Erreur de conversion des valeurs: {e}")
                else:
                    print("Données incorrectes:", values)
            except UnicodeDecodeError as e:
                print("Erreur de décodage:", e)
except KeyboardInterrupt:
    print("Programme arrêté par l'utilisateur.")
except serial.SerialException as e:
    print(f"Erreur avec le port série: {e}")
    time.sleep(1)


