import paho.mqtt. client as mqtt
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path='../.env')

MQTT_BROKER = os.getenv('MQTT_BROKER')
MQTT_PORT = int(os.getenv('MQTT_PORT'))
MQTT_USERNAME = os.getenv('MQTT_USERNAME')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD')

print(f"MQTT_BROKER: {MQTT_BROKER}")
print(f"MQTT_PORT: {MQTT_PORT}")
print(f"MQTT_USERNAME: {MQTT_USERNAME}")
print(f"MQTT_PASSWORD: {MQTT_PASSWORD}")

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")


mqtt_client = mqtt.Client()

mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
mqtt_client.connect(MQTT_BROKER,MQTT_PORT,keepalive=60)


mqtt_client.loop_start()