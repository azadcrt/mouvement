import xbee
import time
import machine
import horloge
from horloge import *

dest = xbee.relay.BLUETOOTH 
i = 1
user_button_pin = machine.Pin('D4', machine.Pin.IN, machine.Pin.PULL_UP)
def my_micropython_data_callback(data):
    print("Data received from the MicroPython interface >> '%s'" % data.decode("utf-8"))
    
while i:
    message = xbee.relay.receive()
    if message is not None:
        i = 0
        message = b"1"
        xbee.transmit(xbee.ADDR_BROADCAST, message)
        print("1")
    time.sleep(1) 

i = 1 

while i:
    horloge.send_sync_message()
    
    message = xbee.relay.receive()
    if message is not None:
        i = 0
        message = b"1"
        xbee.transmit(xbee.ADDR_BROADCAST, message)
        print("2")
    time.sleep(1)
    

while True:
    try:
        received = xbee.receive()
        if received:
            msg = received['payload'].decode("utf-8")
            sender = received['sender_eui64']

            try:
                xbee.relay.send(dest, msg.encode("utf-8"))
                print("Relayed via Bluetooth:", msg)
            except ValueError:
                print("Error: Invalid parameters provided to relay.send()")
            except OSError as e:
                if e.errno == 105:  # ENOBUFS
                    print("Error: Unable to allocate buffer for the frame")
                elif e.errno == 19:  # ENODEV
                    print("Error: Invalid destination")
                elif e.errno == 111:  # ECONNREFUSED
                    print("Error: Bluetooth not connected or delivery failed")
                else:
                    print("Unknown OSError:", e)

    except Exception as e:
        print("General Error:", e)

    time.sleep(0.1) 
