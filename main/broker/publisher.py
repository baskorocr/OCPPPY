import paho.mqtt. client as mqtt

MQTT_BROKER = 'localhost'
MQTT_PORT = 1883
MQTT_USERNAME = 'baskorocr'
MQTT_PASSWORD = 'baskorocr'

mqtt_client = mqtt.Client()

mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
mqtt_client.connect(MQTT_BROKER,MQTT_PORT)

mqtt_client.loop_start()