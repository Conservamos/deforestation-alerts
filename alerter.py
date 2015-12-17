#!/usr/bin/python
'''

'''

import sys
import logging
import httplib2
import os
import apiclient
from apiclient import discovery
from apiclient import http
from apiclient import errors
import oauth2client
from oauth2client import client
from oauth2client import tools
import fiona
from fiona import collection
from fiona.crs import from_epsg
from pyproj import Proj, transform
import csv
import shapely
from shapely.geometry import shape, MultiPolygon, Polygon, Point
import gspread

# optimize by using indeces for looping through geo features
from rtree import index

# pyshp for bbox function, may be replaced by shapely's bound
import shapefile

# Here goes the id of the Google Drive folder that you use to host both the shape files for which you want to have alerts and the file with the alerts.
drive_folder_id = "0B3EayI142qkFaURZUEV4bFBrSDQ"

# This is the file name of the shape file with private protected areas, called ACPs in Peru.
acps_shape_file_name = ""

# This is the file name of the shape file with conservation and ecotourism concessions in Peru.
concessions_shape_file_name = "protected_areas.zip"

# 
forma_file_name = "forma_api.csv"

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

SCOPES = ['https://www.googleapis.com/auth/drive', 'https://spreadsheets.google.com/feeds']
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'SPDA Deforestation Alert System'


def get_credentials():
    """Gets valid user credentials from storage.
    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.
    Returns: Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'drive-quickstart.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatability with Python 2.6
            credentials = tools.run(flow, store)
        print 'Storing credentials to ' + credential_path
    return credentials

def get_files():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v2', http=http)
    # get all file ids from shapefiles folder in alert folder in spda gis folder
    results= service.children().list(folderId=drive_folder_id).execute()
    items = results.get('items', [])

    shape_ids = []
    folder_files = []
    if not items:
        print 'No files found.'
    else:
        for item in items:
            shape_ids.append(item['id'])
        for k in shape_ids:
            kobject = service.files().get(fileId=k).execute()
            folder_files.append(kobject)
    shape = None
    forma = None
    if not folder_files:
        print 'No files found.'
    else:
        for i in folder_files:
            if i['title'] == concessions_shape_file_name:
                shape_file_id = i['id']
                shape_file = service.files().get(fileId=shape_file_id).execute()
                download_url = shape_file["downloadUrl"]
                if download_url:
                    resp, content = service._http.request(download_url)
                    shape = content
                    # if resp.status == 200:
                    #     print 'Status: %s' % resp
                    # else:
                    #     print 'An error occurred: %s' % resp
                    #     return None
                else:
                # The file doesn't have any content stored on Drive.
                    return None
        for k in folder_files:
            if k['title'] == forma_file_name:
                forma_file_id = k['id']
                forma_file = service.files().get(fileId=forma_file_id).execute()
                forma_url = forma_file["downloadUrl"]
                if forma_url:
                    resp, content = service._http.request(forma_url)
                    forma = content
                    # # if resp.status == 200:
                    # #     print 'Status: %s' % resp
                    # else:
                    #     print 'An error occurred: %s' % resp
                    #     return None
                else:
                # The file doesn't have any content stored on Drive.
                    return None
    print "Done downloading files"
    return (shape, forma)

# write shape file and csv to local file system
def save_files():
    shape, forma = get_files()
    with open('temp/protected_areas.zip', 'wb') as f:
        f.write(shape)
    with open('temp/forma_api.csv', 'wb') as g:
        g.write(forma)

def spatial_join():
    save_files()
    # Make this more generic like here or use native python functionality to unpack zip:
    # with fiona.drivers():
    #     for i, layername in enumerate(fiona.listlayers('/',vfs='zip://temp/protected_areas.zip')):
    #         with fiona.open('/',vfs='zip://temp/protected_areas.zip',layer=i) as src:   
    #             print(i, layername, len(src))

  
    # Multi = None
        # Multi = MultiPolygon([shape(pol['geometry'])])


    # logging.basicConfig(stream=sys.stderr, level=logging.INFO)

    with fiona.open('temp/protected_areas/conc_cons.shp', 'r') as concessions:
        sink_schema = concessions.schema.copy()
        p_in = Proj(concessions.crs)
        with fiona.open(
            'temp/protected_areas/conservacion_new.shp', 'w',
            crs=from_epsg(4326),
            driver=concessions.driver,
            schema=sink_schema,
            ) as sink:
            p_out = Proj(sink.crs)
            for f in concessions:
                
                try:
                    assert f['geometry']['type'] == "Polygon"
                    new_coords = []
                    for ring in f['geometry']['coordinates']:
                        x2, y2 = transform(p_in, p_out, *zip(*ring))
                        new_coords.append(zip(x2, y2))
                    f['geometry']['coordinates'] = new_coords
                    sink.write(f)
                
                except Exception, e:
                    # Writing uncleanable features to a different shapefile
                    # is another option.

                    logging.exception("Error transforming feature %s:", f['id'])

    concessions_new = fiona.open('temp/protected_areas/conservacion_new.shp', 'r')
    
# spatial join logic for csv file of alerts

    # alert_file = []

    # with open('temp/forma_api.csv', 'rb') as p:
    #     forma_alerts = csv.DictReader(p)
    #     for pol in concessions_new:
    #         area = shape(pol['geometry'])
    #         print area
    #         for row in forma_alerts:
    #             try: 
    #                 assert row['lon'] != ''
    #                 alert_point = Point(float(row['lon']), float(row['lat']))
    #                 if area.contains(alert_point):
    #                     alert_item = [pol['properties']['TITULAR'], pol['properties']['CONTRATO'], row['lat'], row['lon'], row['date']]
    #                     alert_file.append(alert_item)
    #             except Exception, e:
    #                 None
    # return alert_file

    alert_file = []

    concessions_idx = index.Index()
    count = -1
    concessions_shapes = []

# Spatial index based on bounding boxes of concession polygons 

    with fiona.open('temp/protected_areas/conservacion_new.shp', 'r') as c: 
        for conc in c:
            count +=1
            area = shape(conc['geometry'])
            concessions_idx.insert(count,area.bounds,obj=conc)
    with fiona.open("temp/peru_day2015.shp", "r") as d:
        for point in d:
# Retrieve date of last alert run 
# Only include new alerts
# Newest alert: 287
            alert_date = point['properties']['GRID_CODE']
            if int(alert_date) >= 280:
                alert_point = shape(point['geometry'])
                alert_point_raw = point['geometry']['coordinates']
                conc_objects = [n.object for n in concessions_idx.intersection(alert_point_raw, objects=True)]
                for i in conc_objects:
                    conc_pol = shape(i['geometry'])
                    if alert_point.within(conc_pol):
                        alert_item = [i['properties']['TITULAR'], i['properties']['CONTRATO'], alert_point_raw, alert_date]
                        print alert_item
                        alert_file.append(alert_item)
    
    return alert_file

def alerts_to_sheet():
    alerts = spatial_join()
    credentials = get_credentials()
    gc = gspread.authorize(credentials)
    #Open Spreadsheet
    wks = gc.open_by_url("https://docs.google.com/spreadsheets/d/1vr-RL2-WPywjzdrL7G0keXI2xkaXS3IQg78tmbB64Jc/edit#gid=0").sheet1
    for i in alerts:
        wks.append_row(i)

def main ():
    alerts_to_sheet()

if __name__ == '__main__':
    main()