import threading
import time
from os import system
from datetime import datetime, timezone
from queue import Queue
import json

CONSECUTIVE_SUCCESS_TH  = 1
CONSECUTIVE_FAILS_TH    = 5
DELTA_KEEPALIVE_SLEEP   = 45


class thdKeepAlive(threading.Thread):
    def __init__( self, config, shared ):
        super().__init__()

        import pytz
        self.tz = pytz.timezone("Europe/Rome")

        self.config = config
        self.shared = shared

        self.q = self.shared['queue']
        
        self._stop_event = threading.Event()

        self.success = 0
        self.fails = 0
        self.ConnectionState = False

    def run( self ):
        """
        This function is responsible for sending keepalive messages to the MQTT broker.
        It runs in a separate process and sends a keepalive message at regular intervals.
        """

        portal_id = self.config['portal_id']
        mqtt_host = self.config['broker_host']
        mqtt_port = self.config['broker_port']
        mqtt_cert = self.config['broker_crt']
        mqtt_usr = self.config['mqtt_user']
        mqtt_pwd = self.config['mqtt_pass']

        mqtt_clientid = self.config['client_id']

        addKeepAliveMsg = True

        try:
            while not self._stop_event.is_set():
                # Check if the initial keepalive message should be added
                if addKeepAliveMsg:
                    msg = '{ "keepalive-options" : ["suppress-republish"] }'
                else:
                    msg = ""

                command = f"""mosquitto_pub -t 'R/{portal_id}/keepalive' -m '{msg}' -h '{mqtt_host}' --cafile '{mqtt_cert}' -u '{mqtt_usr}' -P '{mqtt_pwd}' -p '{mqtt_port}' -I '{mqtt_clientid}-keep'"""

                ecode = system(command + " > /dev/null 2>&1")
                
                item = { }
                if ecode != 0:
                    addKeepAliveMsg = True
                    self.success = 0
                    self.fails = self.fails + 1

                    #print( f"[KEEPALIVE-RUN] ({datetime.now(tz=self.tz)}) command failed with `{ecode}` {self.success}/{self.fails}" )
                    item = { 'time'  : datetime.now(tz=self.tz),
                             'topic' : "K/keepalive/keepalive/-1/fail",
                             'msg'   : json.dumps( {'value' : self.fails } )
                        }

                else: # CHECK: https://mosquitto.org/man/mosquitto_pub-1.html
                    addKeepAliveMsg = False
                    self.success = self.success + 1
                    self.fails = 0

                    #print( f"[KEEPALIVE-RUN] ({datetime.now(tz=self.tz)}) sent successfully {self.success}/{self.fails}" )
                    item = { 'time'  : datetime.now(tz=self.tz),
                            'topic' : "K/keepalive/keepalive/-1/success",
                            'msg'   : json.dumps( {'value' : self.success } )
                    }

                try:
                    self.q.put(item, timeout=1)
                except queue.Full as e:
                    print(f"[RECEIVER-MESSAGE] ({datetime.now(tz=self.tz)}) Queue full!")

                time.sleep( DELTA_KEEPALIVE_SLEEP )
        finally:
            print( f"[KEEPALIVE-RUN] ({datetime.now(tz=self.tz)}) Stopped Keepalive thread!" )
            self.successfully = 0

    def stop(self):
        print( f"[KEEPALIVE-STOP] ({datetime.now(tz=self.tz)}) stop received." )
        self._stop_event.set()

    def getConnectionState( self ):

        if self.success > CONSECUTIVE_SUCCESS_TH:
            self.ConnectionState = True
        
        if self.fails > CONSECUTIVE_FAILS_TH:
            self.ConnectionState = False

        return self.ConnectionState

if __name__ == "__main__":
    pass
