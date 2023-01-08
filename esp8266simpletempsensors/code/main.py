from machine import Pin, SoftI2C
from time import sleep,sleep_ms,time
from network import WLAN
from network import STA_IF
from umqtt.robust import MQTTClient
import onewire, ds18x20

MQTT_CONNECT_NUMBER_OF_RETRY = 3

THINGNAME = "PUT_THING_NAME_HERE"

#This works for either ESP8266 ESP32 if you rename certs before moving into /flash 
CERT_FILE = "cert"
KEY_FILE = "key"

#if you change the ClientId make sure update AWS policy
MQTT_CLIENT_ID = THINGNAME
MQTT_PORT = 8883

#if you change the topic make sure update AWS policy
MQTT_TOPIC = "esp8266simpletempsensors/{}".format(THINGNAME)

#Change the following three settings to match your environment
MQTT_HOST = "PUT_MQTT_HOST_HERE"
WIFI_SSID = "PUT_WIFI_SSID_HERE"
WIFI_PW = "PUT_WIFI_PASSWORD_HERE"

def connect_wifi(ssid, pw):
    wlan = WLAN(STA_IF)
    if not wlan.active():
        wlan.active(True)

    nets = wlan.scan()
    if(wlan.isconnected()):
        wlan.disconnect()            
    wlan.connect(ssid, pw)         
    while not wlan.isconnected():             
        machine.idle() # save power while waiting
        print('WLAN connection succeeded!')         
        break 
    print("connected:", wlan.ifconfig())

mqtt_client = None

def pub_msg(msg):
    global mqtt_client
    try:    
        mqtt_client.publish(MQTT_TOPIC, msg)
        print("Sent: " + msg)
        sleep(10)
    except Exception as e:
        print("Exception publish: " + str(e))
        raise

def connect_mqtt():    
    global mqtt_client

    try:
        with open(KEY_FILE, "r") as f: 
            key = f.read()

        print("Got Key")
            
        with open(CERT_FILE, "r") as f: 
            cert = f.read()

        print("Got Cert")	

        mqtt_client = MQTTClient(client_id=MQTT_CLIENT_ID, server=MQTT_HOST, port=MQTT_PORT, keepalive=1200, ssl=True, ssl_params={"cert":cert, "key":key, "server_side":False})

        myNumberOfRetry = MQTT_CONNECT_NUMBER_OF_RETRY
        
        while myNumberOfRetry > 0:
            myNumberOfRetry -= 1
            try:
                mqtt_client.connect()
                print('MQTT Connected')
                return
            except Exception as e:
                print('Cannot connect MQTT: ' + str(e))
                print('but we got more tries '+ str(myNumberOfRetry))
        
        raise Exception('Impossible to connect')
        
    except Exception as e:
        print('Cannot connect MQTT: ' + str(e))
        raise

def disconnect_mqtt():    
    global mqtt_client
    mqtt_client.disconnect()
    sleep(10)

    print('MQTT disconnected')

def deep_sleep(msecs):
  #configure RTC.ALARM0 to be able to wake the device
  rtc = machine.RTC()
  rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)
  # set RTC.ALARM0 to fire after Xmilliseconds, waking the device
  rtc.alarm(rtc.ALARM0, msecs)
  #put the device to sleep
  machine.deepsleep()
  
  
#connecting the temperature sensor
ds_pin = machine.Pin(14)
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))

roms = ds_sensor.scan()
print('Found DS devices: ', roms)

#while True:
ds_sensor.convert_temp()
sleep_ms(750)

myTemperature = ds_sensor.read_temp(roms[0])

#connect to the wifi
connect_wifi(WIFI_SSID,WIFI_PW)

try:

    print("Connecting MQTT")
    connect_mqtt()
    print("Publishing")
    pub_msg("{\"temperature\":" + str(myTemperature) + "}")
    print("OK")
    disconnect_mqtt()

except Exception as e:
    print('We got exception: ' + str(e))
    print('but we must continue to run')

deep_sleep(300000)


