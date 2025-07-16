
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
