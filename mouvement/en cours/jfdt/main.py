import machine
import time

# Configuration de la broche DIO4 pour l'User Button
user_button_pin = machine.Pin('D4', machine.Pin.IN, machine.Pin.PULL_UP)

# Fonction principale
def main():
    while True:
        if user_button_pin.value() == 0:  # Le bouton est appuyé (0 signifie niveau bas)
            print("User Button appuyé")
        else:
            print("User Button non appuyé")
        time.sleep(0.1)

# Lancer le programme principal
if __name__ == "__main__":
    main()
