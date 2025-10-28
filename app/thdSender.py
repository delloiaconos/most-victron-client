import threading
from influxdb import InfluxDBClient
from datetime import datetime
import queue
import time 
import json


class thdSender(threading.Thread):
    def __init__(self, config, shared ):
        super().__init__()
        
        import os
        self.PRINT_RECEIVED = os.environ.get( 'SENDER_RUN_PRINT_RECEIVED', 'False' ).lower() in ('true', '1', 't', 'yes', 'y')
        self.PRINT_KEEPALIVE = os.environ.get( 'SENDER_RUN_PRINT_KEEPALIVE', 'False' ).lower() in ('true', '1', 't', 'yes', 'y')

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
        print(f"[SENDER-RUN] ({datetime.now(tz=self.tz)}) Starting a thread")

        try:
            self.client = InfluxDBClient( self.influx_host, self.influx_port, database=self.influx_db , timeout=60)
        except Exception as ex:
            print( f"[SENDER-RUN] ({datetime.now(tz=self.tz)}) InfluxDBClient EXCEPTION {str(ex)}!!" )
            

        try:
            while not self._stop_event.is_set():
                try:
                    item = self.q.get(timeout=60)        
                    if self.PRINT_RECEIVED:
                        print( f"[SENDER-RUN] ({datetime.now(tz=self.tz)}) received `{item}`" )

                except queue.Empty:
                    print( f"[SENDER-RUN] ({datetime.now(tz=self.tz)}) Queue empty" ) 
                    continue
                
                try:
                    topic = item['topic'].split('/')
                except:
                    continue
                
                if "keepalive" in topic:
                    if self.PRINT_KEEPALIVE:
                        print( f"[SENDER-RUN] ({datetime.now(tz=self.tz)}) 'keepalive' `{item}`" )

                if len( topic ) < 4:
                    print( f"[SENDER-RUN] ({datetime.now(tz=self.tz)}) 'len( topic ) < 3' on `{item}`" )
                    continue

                if "History" in topic:
                    continue

                try:
                    msg = json.loads( item['msg'] )
                    val_str = str( msg['value'] )
                    if val_str.lower() in ['none', 'null', 'empty']:
                        continue
                    if len( val_str ) == 0:
                        continue
                except:
                    pass
                
                try:
                    value = float( msg['value'] )
                except:
                    continue
                
                try:
                    bus_id = int( topic[3] )
                except:
                    bus_id = str( topic[3] ) 
                
                try:    
                    data_point = {
                        'time'          : item['time'].isoformat(),
                        'measurement'   : topic[2],
                        'tags'          : { 'portal_id' : topic[1],
                                            'site_id' : self.id_site,
                                            'installation' : self.installation,
                                            'bus_id' : bus_id },
                        'fields'        : { "-".join( topic[4:] ) : value },
                    }
                    self.client.write_points( [data_point] )
                except Exception as ex:
                    print( f"[SENDER-RUN] ({datetime.now(tz=self.tz)}) WRITE EXCEPTION `{data_point}` - {str(ex)}!!" )
        finally:
            print( f"[SENDER-RUN] ({datetime.now(tz=self.tz)}) Sender thread stopped")

    def stop(self):
        print( f"[SENDER-STOP] ({datetime.now(tz=self.tz)}) Stopping Sender thread")
        self._stop_event.set()

if __name__ == "__main__":
    pass
