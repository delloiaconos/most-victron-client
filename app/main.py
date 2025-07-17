from thdReceiver import thdReceiver
from thdKeepAlive import thdKeepAlive
from thdSender import thdSender
import queue
import time
from datetime import datetime, timezone
import configparser, argparse
from vrmutils import *
import sys, os

DELTA_HEALTHCHECK      = "30m"
DELTA_SYSINFO_RETRIVAL = 600
DELTA_SLEEP            = 5
CONFIG_FILE = '/config/config.ini'

def main( args, config ):
    # Site Info initial retrival from VRM
    siteInfo = getSiteInfo( config )
    print( f"[MAIN] ({datetime.now(tz=None)}) {siteInfo}" )

    config['broker_host'] = siteInfo['mqtt_host']
    config['portal_id'] = siteInfo['portal_id']
    config['client_id'] = getBaseClientId()
    config['topic_subscribe'] = [f"N/{siteInfo['portal_id']}/#"]

    shared = {}
    shared['queue'] = queue.Queue()

    received_thd = thdReceiver( config, shared )

    keepalive_thd = thdKeepAlive( config, shared )
    keepalive_thd.start()

    sender_thd = thdSender( config, shared )
    sender_thd.start()

    lastConnection = datetime.now()
    while True:
        time.sleep(DELTA_SLEEP)
        ConnectionState = keepalive_thd.getConnectionState()

        if ConnectionState:
            lastConnection = datetime.now()
            if not received_thd.is_alive():
                print( f"[MAIN] ({datetime.now(tz=None)}) Starting receiver thread")
                received_thd = thdReceiver( config, shared )
                received_thd.start()

        elif not ConnectionState:
            if received_thd.is_alive():
                print( f"[MAIN] ({datetime.now(tz=None)}) Stopping receiver thread")
                received_thd.stop()
                received_thd.join()
            
            delta = (datetime.now() - lastConnection).total_seconds()
            if delta > DELTA_SYSINFO_RETRIVAL:

                if keepalive_thd.is_alive():
                    print( f"[MAIN] ({datetime.now(tz=None)}) Stopping keepalive thread")
                    keepalive_thd.stop()
                    keepalive_thd.join()

                # Update connection info!
                siteInfo = getSiteInfo( config )
                print( f"[MAIN] ({datetime.now(tz=None)}) {siteInfo}" )

                config['broker_host'] = siteInfo['mqtt_host']
                config['portal_id'] = siteInfo['portal_id']
                config['client_id'] = getBaseClientId()
                config['topic_subscribe'] = [f"N/{siteInfo['portal_id']}/#"]

                keepalive_thd = thdKeepAlive( config, shared )
                keepalive_thd.start()

    keepalive_thd.stop()
    keepalive_thd.join()

    sender_thd.stop()
    sender_thd.join()


def healthcheck( args, config ):
    from influxdb import InfluxDBClient
    import json
    import pytz

    tz = pytz.timezone("Europe/Rome")

    print( f"[HEALTHCHECK] ({datetime.now(tz=tz)}) called")
    
    client = InfluxDBClient( config["influx_host"], config["influx_port"], database=config["influx_db"] )

    res = client.query( f"""SHOW SERIES WHERE ("installation" = '{config['installation']}')""")
    measurements = list( set( [ i['key'].split(',')[0] for i in list( res.get_points() ) ] ) )
    
    if 'keepalive' in measurements:
        measurements.remove( 'keepalive' )

    objs = {}
    for meas in measurements:
        res = client.query( f"""SELECT COUNT(*) FROM "{meas}" WHERE ("installation" = '{config['installation']}') AND time >= now() - {DELTA_HEALTHCHECK}""")
        if res:
            for (measurement, tags), points in res.items():
                point = list( points )[0]
                objs = { **objs, **point }

    #print( json.dumps( objs ), file=sys.stderr )
    notNullKeys = [k for k, v in objs.items() if v is not None]
    #print( notNullKeys )
    
    if bool( objs ):
        del objs['time' ]
        if any( objs.values() ):
            print( f"[HEALTHCHECK] ({datetime.now(tz=tz)}) passed")
            exit( 0 )
        else:
            print( f"[HEALTHCHECK] ({datetime.now(tz=tz)}) no points")
            exit( 1 )
    else:
        print( f"[HEALTHCHECK] ({datetime.now(tz=tz)}) no data")
        exit( 2 )
        

if __name__ == "__main__":

    # overload parameters from environment variables
    DELTA_HEALTHCHECK       = os.environ.get( 'HOME', DELTA_HEALTHCHECK )
    DELTA_SYSINFO_RETRIVAL  = os.environ.get( 'HOME', DELTA_SYSINFO_RETRIVAL )
    DELTA_SLEEP             = os.environ.get( 'HOME', DELTA_SLEEP )
    CONFIG_FILE             = os.environ.get( 'HOME', CONFIG_FILE )

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help="configuration file overloading")
    parser.add_argument('-hc', '--healthcheck', help="perform an healthcheck", action="store_true")
    args = parser.parse_args()

    if args.config is not None:
        CONFIG_FILE = args.config

    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    config = {s:config['DEFAULT'][s] for s in config['DEFAULT'].keys()}  

    if args.healthcheck:
        healthcheck( args, config )
    else:
        main( args, config )