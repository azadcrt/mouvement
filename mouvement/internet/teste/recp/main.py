import micropython
import xbee

received_messages = {}

def parse_message(message):
    try:
        parts = message.split(':')
        if len(parts) != 5:
            raise ValueError("Invalid message format")

        message_id = int(parts[0])
        path = parts[1].split(',')
        rssi_list = list(map(int, parts[2].split(',')))
        start_time = float(parts[3])
        quaternion_str = parts[4]
        w, x, y, z = map(float, quaternion_str.split(','))
        return message_id, path, rssi_list, start_time, (w, x, y, z)
    except Exception as e:
        print("Error parsing message:", e)
        return None, None, None, None, None

while True:
    frame = xbee.receive()
    if frame:
        payload = frame['payload'].decode('utf-8')
        sender = frame['sender_eui64']
        try:
            message_id, path, rssi_list, start_time, quaternion = parse_message(payload)
            if message_id is not None:
                last_message_id = received_messages.get(sender, -1)
            
                if message_id > last_message_id:
                    received_messages[sender] = message_id
                    current_rssi = xbee.atcmd('DB')
                    w, x, y, z = quaternion
                    print(message_id, path, w, x, y, z, sender, current_rssi)
                else:
                    print("Message ID already processed or invalid for")
        except ValueError as ve:
            print("Erreur de conversion des valeurs quaternion:", ve)
        except Exception as ex:
            print("Une erreur s'est produite:", ex)

def eui64_to_hash(eui64):
    return ''.join('{:02X}'.format(b) for b in eui64)


