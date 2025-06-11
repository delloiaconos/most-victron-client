import threading
import time
import paho.mqtt.client as mqtt
import ssl
from datetime import datetime, timezone

class thdReceiver(threading.Thread):
    def __init__(self, config ):
        super().__init__()

        self.config = config

        self.broker_host = self.config['broker_host']
        self.broker_port = self.config['broker_port']
        self.client_id = self.config['client_id']
        self.topic_subscribe = self.config['topic_subscribe'] or []

        self._stop_event = threading.Event()

        #MQTT Client

        self.client = mqtt.Client(client_id=self.client_id)

        self.client.username_pw_set( self.config['mqtt_user'], self.config['mqtt_pass'] )
        self.client.tls_set( self.config['broker_crt'], tls_version=ssl.PROTOCOL_TLSv1_2)
        self.client.tls_insecure_set(True)

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        print(f"[MQTT-CONNECT] ({datetime.now(tz=None)}) Connected with result code {rc}")
        for topic in self.topic_subscribe:
            self.client.subscribe(topic)
            print(f"[MQTT-CONNECT] ({datetime.now(tz=None)}) Subscribed to {topic}")

    def on_message(self, client, userdata, msg):
        print(f"[MQTT-MESSAGE] ({datetime.now(tz=None)}) @ {msg.topic}")

    def run(self):
        print(f"[MQTT-RUN] ({datetime.now(tz=None)}) Starting MQTT thread")
        self.client.connect(self.broker_host, self.broker_port, keepalive=60)
        self.client.loop_start()
        try:
            while not self._stop_event.is_set():
                time.sleep(0.1)
        finally:
            self.client.loop_stop()
            self.client.disconnect()
            print( f"[MQTT-RUN] ({datetime.now(tz=None)}) MQTT thread stopped")

    def stop(self):
        print( f"[MQTT-STOP] ({datetime.now(tz=None)}) Stopping MQTT thread")
        self._stop_event.set()

if __name__ == "__main__":
    pass
