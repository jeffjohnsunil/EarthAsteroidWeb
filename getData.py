import requests
import json
import configparser
import xlsxwriter
import time
from datetime import datetime
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
workbook = xlsxwriter.Workbook(configOut)
worksheet = workbook.add_worksheet()
z0_format = workbook.add_format({'num_format': '#,##0'})
z1_format = workbook.add_format({'num_format': '#,##0.0'})
z2_format = workbook.add_format({'num_format': '#,##0.00'})
z3_format = workbook.add_format({'num_format': '#,##0.000'})

# write the headers on the spreadsheet
now = datetime.now()
nowStr = now.strftime("%m/%d/%Y %H:%M:%S")
worksheet.write('A1','INTLDES')
worksheet.write('B1','NORAD_CAT_ID')
worksheet.write('C1','OBJECT_TYPE')
worksheet.write('D1','SATNAME')
worksheet.write('E1','COUNTRY')
worksheet.write('F1','LAUNCH')
worksheet.write('G1','PERIOD')
worksheet.write('H1','INCLINATION')
worksheet.write('I1','APOGEE')
worksheet.write('J1','PERIGEE')
worksheet.write('K1','LAUNCH_YEAR')
worksheet.write('L1','CURRENT')
worksheet.write('M1','ECCENTRICITY')
worksheet.write('N1','SEMI_MAJOR_AXIS')
worksheet.write('O1','SEMI_MINOR_AXIS')
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
    for e in retData:
        if numAnalysed < 1000:
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
            # each element is one reading of the orbital elements for one Starlink
            print("Scanning satellite called " + e['SATNAME'])
            worksheet.write(wsline, 0, e['INTLDES'])
            worksheet.write(wsline, 1, int(e['NORAD_CAT_ID']))
            worksheet.write(wsline, 2, e['OBJECT_TYPE'])
            worksheet.write(wsline, 3, e['SATNAME'])
            worksheet.write(wsline, 4, e['COUNTRY'])
            worksheet.write(wsline, 5, e['LAUNCH'])
            worksheet.write(wsline, 6, float(e['PERIOD']))
            worksheet.write(wsline, 7, float(e['INCLINATION']))
            worksheet.write(wsline, 8, float(e['APOGEE']))
            worksheet.write(wsline, 9, float(e['PERIGEE']))
            worksheet.write(wsline, 10, int(e['LAUNCH_YEAR']))
            worksheet.write(wsline, 11, e['CURRENT'])

            semiMajorAxis = (float(e['APOGEE']) + float(e['PERIGEE'])) / 2
            eccentricity = (float(e['APOGEE']) / semiMajorAxis) - 1
            semiMinorAxis = math.sqrt(semiMajorAxis ** 2 * (1 - eccentricity ** 2))

            worksheet.write(wsline, 12, eccentricity)
            worksheet.write(wsline, 13, semiMajorAxis)
            worksheet.write(wsline, 14, semiMinorAxis)
            wsline = wsline + 1
            maxs = maxs + 1
            if maxs > 18:
                print("Snoozing for 60 secs for rate limit reasons (max 20/min and 200/hr)...")
                maxs = 1
        numAnalysed += 1
    session.close()
    with open("starlink-track.json", "w") as outfile:
        json.dump(jsonPush, outfile)
workbook.close()
print("Completed session") 