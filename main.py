from thdReceiver import thdReceiver
from thdKeepAlive import thdKeepAlive

import time
from datetime import datetime, timezone
import configparser


def get_base_client_id(length):
    """
    Generates a base client ID for the MQTT connection.
    The client ID is constructed using the VRM site ID and a random string.
    """
    import random, string
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
        log.error(f"VRM api: {r}")

    data = json.loads(r.text)
    # PORTAL_ID = user_data["records"][0]["identifier"]
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

    config.read('config/vrm-config.ini')
    config = {s:config['DEFAULT'][s] for s in config['DEFAULT'].keys()}  

    siteInfo = getSiteInfo( config )
    print( siteInfo )

    config['broker_host'] = siteInfo['mqtt_host']
    config['portal_id'] = siteInfo['portal_id']
    config['client_id'] = get_base_client_id(10)
    config['topic_subscribe'] = [f"N/{siteInfo['portal_id']}/#"]


    received_thd = thdReceiver( config )
    
    keepalive_thd = thdKeepAlive( config )
    keepalive_thd.start( )

    while True:
        time.sleep(5)
        ConnectionState = keepalive_thd.getConnectionState()

        if ConnectionState:
            if not received_thd.is_alive():
                print( f"[MAIN] ({datetime.now(tz=None)}) Starting receiver thread")
                received_thd.start()
        else:
            if received_thd.is_alive():
                print( f"[MAIN] ({datetime.now(tz=None)}) stopping receiver thread")
                received_thd.stop()
                received_thd.join()
                received_thd = thdReceiver( config )
        
    keepalive_thd.stop()
    keepalive_thd.join()
