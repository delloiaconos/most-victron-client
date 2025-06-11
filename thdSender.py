import threading
from influxdb import InfluxDBClient
from datetime import datetime
import queue
import time 
import json

class thdSender(threading.Thread):
    def __init__(self, config, shared ):
        super().__init__()

        import pytz
        self.tz = pytz.timezone("Europe/Rome")

        self.config = config
        self.shared = shared

        self.influx_host  = self.config["influx_host"]
        self.influx_port  = self.config["influx_port"]
        self.influx_db    = self.config["influx_db"]

        self.installation   = self.config["installation"]
        self.id_site        = self.config['id_site']

        self.q = self.shared['queue']
        self._stop_event = threading.Event()


    def run(self):
        print(f"[SENDER-RUN] ({datetime.now(tz=self.tz)}) Starting Sender thread")

        self.client = InfluxDBClient( self.influx_host, self.influx_port, database=self.influx_db )

        try:
            while not self._stop_event.is_set():
                try:
                    item = self.q.get(timeout=60)        
                    print( f"[SENDER-RUN] ({datetime.now(tz=self.tz)}) received `{item}`" )

                    try:
                        topic = item['topic'].split('/')
                        msg = json.loads( item['msg'] )

                        try:
                            value = float( msg['value'] )
                        except:
                            value = str( msg['value'] )
                        
                        data_point = {
                            'time'          : item['time'].isoformat(),
                            'measurement'   : topic[2],
                            'tags'          : { 'portal_id' : topic[1],
                                                'site_id' : self.id_site,
                                                'installation' : self.installation,
                                                'bus_id' : int( topic[3] ) },
                            'fields'        : { "-".join( topic[4:] ) : value },
                        }
                        self.client.write_points( [data_point] )
                    except:
                        print( f"[SENDER-RUN] ({datetime.now(tz=self.tz)}) EXCEPTION `{item}`!!" )

                except queue.Empty:
                    print( f"[SENDER-RUN] ({datetime.now(tz=self.tz)}) Queue empty" )    
        finally:
            print( f"[SENDER-RUN] ({datetime.now(tz=self.tz)}) Sender thread stopped")

    def stop(self):
        print( f"[SENDER-STOP] ({datetime.now(tz=self.tz)}) Stopping Sender thread")
        self._stop_event.set()

if __name__ == "__main__":
    pass
