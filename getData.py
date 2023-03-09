import random
import requests
import json
import configparser
import math

class MyError(Exception):
    def __init___(self,args):
        Exception.__init__(self,"my exception was raised with arguments {0}".format(args))
        self.args = args

# See https://www.space-track.org/documentation for details on REST queries
# the "Find Starlinks" query searches all satellites with NORAD_CAT_ID > 40000, with OBJECT_NAME matching STARLINK*, 1 line per sat
# the "OMM Starlink" query gets all Orbital Mean-Elements Messages (OMM) for a specific NORAD_CAT_ID in JSON format

uriBase                = "https://www.space-track.org"
requestLogin           = "/ajaxauth/login"
requestCmdAction       = "/basicspacedata/query" 
requestFindStarlinks   = "/class/satcat/COUNTRY/<>de/format/json/orderby/COUNTRY%20asc"

# Parameters to derive apoapsis and periapsis from mean motion (see https://en.wikipedia.org/wiki/Mean_motion)

GM = 398600441800000.0
GM13 = GM ** (1.0/3.0)
MRAD = 6378.137
PI = 3.14159265358979
TPI86 = 2.0 * PI / 86400.0

# Use configparser package to pull in the ini file (pip install configparser)
config = configparser.ConfigParser()
config.read("./SLTrack.ini")
configUsr = config.get("configuration","username")
configPwd = config.get("configuration","password")
configOut = config.get("configuration","output")
siteCred = {'identity': configUsr, 'password': configPwd}

# User xlsxwriter package to write the xlsx file (pip install xlsxwriter)

# write the headers on the spreadsheet
wsline = 1

# use requests package to drive the RESTful session with space-track.org
with requests.Session() as session:
    # run the session in a with block to force session to close if we exit

    # need to log in first. note that we get a 200 to say the web site got the data, not that we are logged in
    resp = session.post(uriBase + requestLogin, data = siteCred)
    if resp.status_code != 200:
        raise MyError(resp, "POST fail on login")

    # this query picks up all Starlink satellites from the catalog. Note - a 401 failure shows you have bad credentials 
    resp = session.get(uriBase + requestCmdAction + requestFindStarlinks)
    if resp.status_code != 200:
        print(resp)
        raise MyError(resp, "GET fail on request for Starlink satellites")

    # use the json package to break the json formatted response text into a Python structure (a list of dictionaries)
    retData = json.loads(resp.text)
    jsonPush = []
    satCount = len(retData)
    numAnalysed = 0
    maxs = 1
    # save the data into a JSON file for later use
    for e in retData:
        if numAnalysed < 3000:
            try:
                semiMajorAxis = (float(e['APOGEE']) + float(e['PERIGEE'])) / 2
                eccentricity = (float(e['APOGEE']) / semiMajorAxis) - 1
                semiMinorAxis = math.sqrt(semiMajorAxis ** 2 * (1 - eccentricity ** 2))
                jsonPush.append({
                    'INTLDES': e['INTLDES'],
                    'NORAD_CAT_ID': int(e['NORAD_CAT_ID']),
                    'OBJECT_TYPE': e['OBJECT_TYPE'],
                    'SATNAME': e['SATNAME'],
                    'COUNTRY': e['COUNTRY'],
                    'LAUNCH': e['LAUNCH'],
                    'PERIOD': float(e['PERIOD']),
                    'INCLINATION': float(e['INCLINATION']),
                    'APOGEE': float(e['APOGEE']),
                    'PERIGEE': float(e['PERIGEE']),
                    'LAUNCH_YEAR': int(e['LAUNCH_YEAR']),
                    'CURRENT': e['CURRENT'],
                    'ECCENTRICITY': eccentricity,
                    'SEMI_MAJOR_AXIS': semiMajorAxis,
                    'SEMI_MINOR_AXIS': semiMinorAxis
                })
            except:
                semiMajorAxis = random.randint(1000,3000)
                eccentricity = 0
                semiMinorAxis = semiMajorAxis
                jsonPush.append({
                    'INTLDES': e['INTLDES'],
                    'NORAD_CAT_ID': int(e['NORAD_CAT_ID']),
                    'OBJECT_TYPE': e['OBJECT_TYPE'],
                    'SATNAME': e['SATNAME'],
                    'COUNTRY': e['COUNTRY'],
                    'LAUNCH': e['LAUNCH'],
                    'PERIOD': random.randint(1000,1500),
                    'INCLINATION': random.randint(0,90),
                    'APOGEE': semiMajorAxis,
                    'PERIGEE': semiMajorAxis,
                    'LAUNCH_YEAR': 2000,
                    'CURRENT': e['CURRENT'],
                    'ECCENTRICITY': eccentricity,
                    'SEMI_MAJOR_AXIS': semiMajorAxis,
                    'SEMI_MINOR_AXIS': semiMinorAxis
                })
        numAnalysed += 1
    session.close()
    with open("starlink-track.json", "w") as outfile:
        json.dump(jsonPush, outfile)
print("Completed session") 