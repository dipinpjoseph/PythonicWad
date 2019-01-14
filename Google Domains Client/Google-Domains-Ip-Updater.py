import configparser
import requests
import re
import hashlib

configParser = configparser.RawConfigParser()
configFilePath = r'GoogleDomainsIpUpdater.config'
configParser.read(configFilePath)

googleUpdateUrl = configParser.get('googleParams', 'googleUpdateUrl')
hostName = configParser.get('googleParams', 'hostName')
username = configParser.get('googleParams', 'username')
ipSources = configParser.get('googleParams', 'ipSources')
password = configParser.get('googleParams', 'password')

print("Google Domains Client Started")
try:

    for ipSource in ipSources.split(","):
        print("IP fetching source - "+ipSource)
        response = requests.get(ipSource)
        print(response)
        ip = response.json()["ip"]
        print("IP found - "+ip)
        if (re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip)):
            break;
    googleUpdateUrl = "https://"+username+":"+password+googleUpdateUrl
    print(googleUpdateUrl,hostName,username,password)
    print("Started updating IP in Google Domains")
    response = requests.get(url=googleUpdateUrl,
                            params={"hostname": hostName.strip(), "myip": ip.strip(), "username": username.strip(),
                                    "password": password.strip()})
    print("Response from Google Domains - "+str(response.content))
except Exception as e:
    print ("Exception - "+str(e))
