from thdReceiver import thdReceiver
from thdKeepAlive import thdKeepAlive
from thdSender import thdSender
import queue

import time
from datetime import datetime, timezone
import configparser

DELTA_SYSINFO_RETRIVAL = 600
DELTA_SLEEP            = 5

def getBaseClientId():
    """
    Generates a base client ID for the MQTT connection.
    The client ID is constructed using a random string.
    """
    import random, string
    length = 10
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


def getSiteInfo( config ):
    """
    Reads the idSites VRM API.
    """
    import requests, json

    id_site = int( config['id_site'] )
    api_ui = config['api_ui']
    api_access_token = config['api_access_token']

    url = f"https://vrmapi.victronenergy.com/v2/users/{api_ui}/installations"
    querystring = {"extended": "1"}
    headers = {
        "Content-Type": "application/json",
        "x-authorization": f"Token {api_access_token}",
    }

    r = requests.request("GET", url, headers=headers, params=querystring)
    if r.status_code != 200:
        print( f"[MAIN-getSiteInfo] ({datetime.now(tz=None)}) api: {r}" )

    data = json.loads(r.text)

    idSites = {}

    for i in data["records"]:
        idSites[i["idSite"]] = {
            "name": i["name"],
            "portal_id": i["identifier"],
            "mqtt_host": i["mqtt_host"],
        }
    
    return idSites[id_site] 



if __name__ == "__main__":

    config = configparser.ConfigParser()

    config.read('config/config.ini')
    config = {s:config['DEFAULT'][s] for s in config['DEFAULT'].keys()}  

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