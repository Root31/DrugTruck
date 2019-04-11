import brickpi3 
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
from time import sleep
import main
import os
import threading

BP = brickpi3.BrickPi3()

#Maximale aantal kamers
rooms = 5

#Kamer nummer waar je naartoe wilt gaan
room = 5

#MQT server informatie
MQTT_SERVER = 'localhost'
MQTT_STATUS = 't1_status'
MQTT_SPEED = 't1_speed'

#Geluidje
def bing():
    os.system('mpg321 beepFinal.mp3 &')

    
#Lijn volgen tot bij een kruispunt
def cross(number):
    crossed = 0
    print("Cross " + str(number))
    while(number!=crossed):
        BP.set_motor_power(BP.PORT_C,20)
        BP.set_motor_power(BP.PORT_B,20)
        publish.single(MQTT_SPEED, "30", hostname=MQTT_SERVER)
        sleep(0.5)
        while(1):
            #Als dubbel zwart = stop
            if((BP.get_sensor(BP.PORT_3)>2100) and (BP.get_sensor(BP.PORT_1)[3]<420)):
                print("Dubbel zwart")
                BP.set_motor_power(BP.PORT_B,0)
                BP.set_motor_power(BP.PORT_C,0)
                publish.single(MQTT_SPEED, "0", hostname=MQTT_SERVER)
                crossed+=1  
                break
             #Als lichtsensor op wit is, ga naar links 
            if(BP.get_sensor(BP.PORT_3)<1900):
                BP.set_motor_power(BP.PORT_B,0)
                BP.set_motor_power(BP.PORT_C,70)
            #Als lichtsensor in het midden van het zwarte is ga naar rechts
            if(BP.get_sensor(BP.PORT_3)>2200):
                BP.set_motor_power(BP.PORT_C,0)
                BP.set_motor_power(BP.PORT_B,70)
            #Als geen van beide, rij door
            else:
                BP.set_motor_power(BP.PORT_B,33)
                BP.set_motor_power(BP.PORT_C,33)

#Ga rechts
def right():
    print("Right")
    BP.set_motor_position_relative(BP.PORT_B,1200)
    BP.set_motor_position_relative(BP.PORT_C,0)
    sleep(1)
    print("While")
    #Blijf doordraaien totdat je zwart vindt
    while(1):
        if(BP.get_sensor(BP.PORT_3)>2100):
            BP.set_motor_power(BP.PORT_B,0)
            print("Zwart gevonden")
            break
    print("Goede cross")
    cross(1)

#Ga links
def left():
    print("Left")
    BP.set_motor_power(BP.PORT_B,0)
    BP.set_motor_power(BP.PORT_C,70)
    sleep(1)
    #Blijf doordraaien totdat je zwart vindt
    while(1):
        if(BP.get_sensor(BP.PORT_3)>2000):
            BP.set_motor_power(BP.PORT_C,0)
            break
    cross(1)

#Draai om
def around():
    BP.set_motor_position_relative(BP.PORT_B,1300)
    BP.set_motor_position_relative(BP.PORT_C,-1300)
    sleep(1)

#Route naar kammer (N) van max aantal kamers (max)
def route(n, max):
    around()
    #Blijf door draaien totdat het zwart is 
    while(BP.get_sensor(BP.PORT_3)<2200):
        BP.set_motor_power(BP.PORT_C,0)
        BP.set_motor_power(BP.PORT_B,70)
        publish.single(MQTT_SPEED, "15", hostname=MQTT_SERVER)
    stops = (n/2)
    #Als N oneven is ga N/2+1 aantal krijspunten over
    if((n%2)==1):
        stops+=1
        cross(stops)
    #Als N even is ga dan N/2 aantal krijspunten oer
    else:
        cross(stops)
    if((n%2)==1):
        #Als N oneven is en de laatste kamer doe dan niks
        if(n==max):
            print("Hoeft niet want het is max")
        #Anders ga naar links
        else:
			left()
    #Ga naar rechts als N even is
    else:
		right()
    bing()

#Route terug
def back(n, max):
        around()
        #Doordraaien totdat het zwart is
        while(BP.get_sensor(BP.PORT_3)<2200):
            BP.set_motor_power(BP.PORT_C,0)
            BP.set_motor_power(BP.PORT_B,70)
            publish.single(MQTT_SPEED, "15", hostname=MQTT_SERVER)
        stops = (n/2)
        #Zorg ervoor dat de robot terug op het krijspunt komt in het midden en dan kijkt richting het afhaal punt
        if((n%2)==1):
            if(n==max):
                cross(1)
            else:
                cross(1)
                right()
        else:
            cross(1)
            left()
            stops-=1
        cross(stops)
        bing()

try:
    publish.single(MQTT_STATUS, "Robot staat aan", hostname=MQTT_SERVER)
    wait=0
    #RBG sensoren instellen
    BP.set_sensor_type(BP.PORT_1, BP.SENSOR_TYPE.NXT_COLOR_FULL)
    BP.set_sensor_type(BP.PORT_2, BP.SENSOR_TYPE.NXT_ULTRASONIC)
    BP.set_sensor_type(BP.PORT_3, BP.SENSOR_TYPE.NXT_LIGHT_ON)
    BP.set_sensor_type(BP.PORT_4, BP.SENSOR_TYPE.TOUCH)
    sleep(2)
    publish.single(MQTT_STATUS, "Wacht bij afhaalpunt op pakketje", hostname=MQTT_SERVER)
    #Zorg ervoor dat de robot goed bij het afhaalpunt komt
    cross(1)
    while(1):
        if(BP.get_sensor(BP.PORT_4) == 1):
            room = int(main.waardepakken())
            #room = room.decode('utf-8')
            #Stuur status door naar Website
            publish.single(MQTT_STATUS, "Onderweg naar kamer {}".format(room), hostname=MQTT_SERVER)
            sleep(5)
            route(room,rooms)
            #Wacht een minuut of totdat het pakketje eraf is gehaald
            while(wait<61):
                if(BP.get_sensor(BP.PORT_4)==1):
                    wait+=1
                    publish.single(MQTT_STATUS, "Robot wacht bij kamer {} en keert terug na een minuut als het pakketje niet is opgehaald".format(room), hostname=MQTT_SERVER)
                    sleep(1)
                else:
                    publish.single(MQTT_STATUS, "Pakketje van kamer {} is opgehaald en keert nu terug".format(room), hostname=MQTT_SERVER)
                    break
            wait=0
            sleep(5)
            back(room,rooms)
            sleep(2)
            publish.single(MQTT_STATUS, "Wacht bij afhaalpunt op pakketje", hostname=MQTT_SERVER)

except KeyboardInterrupt:
    publish.single(MQTT_STATUS, "Robot staat uit", hostname=MQTT_SERVER)
    publish.single(MQTT_SPEED, "0", hostname=MQTT_SERVER)
    BP.reset_all()

 
