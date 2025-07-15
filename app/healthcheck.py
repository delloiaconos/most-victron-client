import time, pytz
from datetime import datetime, timezone
from influxdb import InfluxDBClient
        
import configparser

DELTA_SYSINFO_RETRIVAL = 600
DELTA_SLEEP            = 5


if __name__ == "__main__":

    config = configparser.ConfigParser()

    config.read('/config/config.ini')
    config = {s:config['DEFAULT'][s] for s in config['DEFAULT'].keys()}  

    # Site Info initial retrival from VRM
    siteInfo = getSiteInfo( config )
    print( f"[MAIN] ({datetime.now(tz=None)}) {siteInfo}" )

    config['broker_host'] = siteInfo['mqtt_host']
    config['portal_id'] = siteInfo['portal_id']
    config['client_id'] = getBaseClientId()
    config['topic_subscribe'] = [f"N/{siteInfo['portal_id']}/#"]

    tz = pytz.timezone("Europe/Rome")
    pass