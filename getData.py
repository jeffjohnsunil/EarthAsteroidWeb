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
worksheet.write('A1', 'Starlink data from' + uriBase + " on " + nowStr)
worksheet.write('A3','INTLDES')
worksheet.write('B3','NORAD_CAT_ID')
worksheet.write('C3','OBJECT_TYPE')
worksheet.write('D3','SATNAME')
worksheet.write('E3','COUNTRY')
worksheet.write('F3','LAUNCH')
worksheet.write('G3','PERIOD')
worksheet.write('H3','INCLINATION')
worksheet.write('I3','APOGEE')
worksheet.write('J3','PERIGEE')
worksheet.write('K3','LAUNCH_YEAR')
worksheet.write('L3','CURRENT')
worksheet.write('M3','ECCENTRICITY')
worksheet.write('N3','SEMI_MAJOR_AXIS')
worksheet.write('O3','SEMI_MINOR_AXIS')
wsline = 3

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
    satCount = len(retData)
    numAnalysed = 0
    maxs = 1
    for e in retData:
        if numAnalysed < 100:
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
workbook.close()
print("Completed session") 