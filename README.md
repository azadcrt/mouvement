# Installation

- **Tools** :  
  - [XBee Studio](https://www.digi.com/resources/documentation/digidocs/90002385/) or [XCTU](https://www.digi.com/resources/documentation/digidocs/90001526/) for setting up XBee.  
  - On Linux, u need reading right on USB.  

- **File Compilation** :  
  -  `.mpy` are compiled with `mpy-cross`, or directly in xbee with os.compile().  

- **Logs** :  
  - The **USER** button on groove card is set to print log on a text file.  
  - ⚠️ **Attention** : be careful one file by xbee at the same time u have to delete it after.  

---

# 802.15.4  
It's a basic version of the project using the **802.15.4** protocol.  

# Maryline  
This folder contain the bluethoot version of the project
### Additional step :
1. **Connecting the mobile app to the sink** 
2. **Synchronisation** : Press the **SEND** button on the app.
3. 2. **Start recording** : Press the **SEND** button on the app.

# deposit
last version of the code.

NODE/ — code for the sensor nodes.

SINK/ — code for the receiver / sink.

Each folder includes two types of files:

*.py : Python source files (readable / executable).

*.mp or *.mpy : compiled MicroPython files.

Purpose of each file:

main.py: entry point — automatically executed by the XBee chip at startup.

horloge.py (or horloge.mpy): handles the global timer. The code is the same for both the SINK and NODE; only the way it’s called in main.py differs.

api.py: manages the XBee API mode configuration. If you don’t use Bluetooth, set the XBee API mode to 1. For Bluetooth use, you may need mode 4 depending on the firmware — check your XBee documentation.

em.py: implements the network protocol (message management, routing, etc.).

xbeEm.py: controls the sensors and handles XBee setup (initialization, sensor reading, sending/receiving data).
# reconnaitre.zip  
 **Android Studio** project for the mobile app.
