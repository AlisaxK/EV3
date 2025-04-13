from ev3dev2.sensor.lego import ColorSensor
from time import sleep

# Initialisiere den Farb-Sensor an Port 2
sensor = ColorSensor(address='in2')

print("Halte einen Gegenstand vor den Sensor, um die Farbe zu erkennen. Druecke STRG+C zum Beenden.")

try:
    while True:
        color = sensor.color
        print("Erkannte Farbe: {}".format(color))
        sleep(0.5)  # Wartezeit, um die Ausgabe lesbar zu halten
except KeyboardInterrupt:
    print("Test beendet.")
