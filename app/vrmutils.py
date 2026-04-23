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
    import requests, json, datetime

    id_site = int( config['id_site'] )
    api_access_token = config['api_access_token']

    url = f"https://vrmapi.victronenergy.com/v2/users/{config['idUser']}/installations"
    querystring = {"extended": "1"}
    headers = {
        "Content-Type": "application/json",
        "x-authorization": f"Token {api_access_token}",
    }

    r = requests.request("GET", url, headers=headers, params=querystring)
    if r.status_code != 200:
        print( f"[MAIN-getSiteInfo] ({datetime.datetime.now(tz=None)}) api: {r}" )

    data = json.loads(r.text)

    idSites = {}

    for i in data["records"]:
        idSites[i["idSite"]] = {
            "name": i["name"],
            "portal_id": i["identifier"],
            "mqtt_host": i["mqtt_host"],
        }
    
    return idSites[id_site] 



def loginVRM( config ):
    import requests, json, datetime

    # Require Bearer
    url= f"https://vrmapi.victronenergy.com/v2/auth/login"
    headers = {
        "Content-Type": "application/json"
    }
    data= {
        "username": f"{config['mqtt_user']}",
        "password": f"{config['mqtt_pass']}"
    }
    
    r = requests.request("POST", url, headers=headers, json=data)
    response = json.loads(r.text)
    
    try: 
        config['bearer'] = response.get("token")
        config['idUser'] = response.get("idUser")
        return True        
    except:
        return False

def revokeToken( config, idAccessToken ):
    import requests, json, datetime
    
    url = f"https://vrmapi.victronenergy.com/v2/users/{config['idUser']}/accesstokens/{idAccessToken}"

    headers = {
        "Content-Type": "application/json",
        "x-authorization": f"Bearer {config['bearer']}",
    }


    r = requests.request("DELETE", url, headers=headers)
    response = json.loads(r.text)

    return response.get("success")

def getAccessToken( config ):
    """
    Check if there is a valid access token, else generate it
    """
    import requests, json, datetime

    # Lista token esistenti
    url = f"https://vrmapi.victronenergy.com/v2/users/{config['idUser']}/accesstokens"
    
    querystring = {"extended": "1"}
    headers = {
        "Content-Type": "application/json",
        "x-authorization": f"Bearer {config['bearer']}",
    }

    r = requests.request("GET", url, headers=headers, params=querystring)
    response = json.loads(r.text)

    # Rimuoviamo token che iniziano con token_
    if response.get("success") == True:
        for token in response.get("tokens"):
            name = str(token["name"])
            if name.startswith( config['installation'] ):
                revokeToken( config, token["idAccessToken"] )
        
    # Richiesta nuovo token "token_"
    url = f"https://vrmapi.victronenergy.com/v2/users/{config['idUser']}/accesstokens/create"
    headers = {
        "Content-Type": "application/json",
        "x-authorization": f"Bearer {config['bearer']}",
    }
    data= {
        "name" : f"{config['installation']}-{int(datetime.datetime.now().timestamp())}"
    }
    
    r = requests.request("POST", url, headers=headers, json=data)
    response = r.json()
    
    config['api_access_token'] = response.get("token")
