from thdReceiver import thdReceiver
from thdKeepAlive import thdKeepAlive
from thdSender import thdSender
import queue
import time
from datetime import datetime, timezone
import configparser, argparse
from vrmutils import *


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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help="configuration file overloading")
    args = parser.parse_args()

    if args.config is not None:
        CONFIG_FILE = args.config

    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    config = {s:config['DEFAULT'][s] for s in config['DEFAULT'].keys()}  

    main( args, config )