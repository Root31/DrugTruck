from __future__ import print_function
import pyzbar.pyzbar as pyzbar
import numpy as np
import cv2
import os

def decode(im):

    # zoek QR code
    decodedObjects = pyzbar.decode(im)

    # resultaat teruggeven
    return decodedObjects

def waardepakken():
    while True:
        os.system("raspistill -t 750 -o /home/pi/Documents/cameraFiles/image.png") #laat camera een foto maken
        im = cv2.imread('/home/pi/Documents/cameraFiles/image.png')
        decodedObjects = decode(im)
        if len(decodedObjects)>0:
            tijdelijk = str(decodedObjects[0][0]) #relevante data van bytewaarde naar string
            #waarde = int((tijdelijk[0])) # string naar integer # Alleen voor python3 KUT!
            if tijdelijk > 0:
                return tijdelijk

# Main
if __name__ == '__main__':
    print(waardepakken())
