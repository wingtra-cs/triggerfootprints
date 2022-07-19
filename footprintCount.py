import streamlit as st
import json
import requests
import time
import utm
import math
from shapely.geometry import MultiPoint, Polygon, MultiPolygon
import geopandas as gpd
import pydeck as pdk
import pandas as pd


st.set_page_config(layout="wide")

st.title('Flight Triggers and Footprints')

st.sidebar.image('./logo.png', width=260)
st.sidebar.markdown('#')
st.sidebar.write('This application visualizes and reports the number of triggers captured during a flight.')
st.sidebar.write('If you have any questions regarding the application, please contact us at support@wingtra.com.')
st.sidebar.markdown('#')
st.sidebar.info('This is a prototype application. Wingtra AG does not guarantee correct functionality. Use with discretion.')

# Upload button for JSON

uploaded_json = st.file_uploader('Please Select Project JSON file in the DATA folder.', accept_multiple_files=False)
uploaded = False

if uploaded_json is not None:
    if uploaded_json.name.lower().endswith('.json'):
        uploaded = True
    else:
        msg = 'Please upload a JSON file.'
        st.error(msg)
        st.stop()

if uploaded:
    
    # Parse and Visualize JSON
      
    data = json.load(uploaded_json)
    try:
        triggers = data['flights'][0]['geotag']
        trigger_count = len(triggers)
        camera = data['model']
    except:
        msg = 'Please upload a valid Wingtra JSON file.'
        st.error(msg)
        st.stop()
    
    st.success('JSON File Uploaded.')
    st.subheader('There are ' + str(trigger_count) + ' triggers.')
    
    lat = []
    lon = []
    roll = []
    pitch = []
    yaw = []
    height = []
    names = []   
    
    i = 1
    for trigger in triggers:
        lat.append(float(trigger['coordinate'][0]))
        lon.append(float(trigger['coordinate'][1]))
        height.append(float(trigger['coordinate'][2]))
        roll.append(float(trigger['roll']))
        pitch.append(float(trigger['pitch']))
        yaw.append(float(trigger['yaw']))
        names.append('Image ' + str(i))
        i += 1
    
    # Converting to AGL
    
    agl = []
    responses = []
    terrain = []
    
    t = st.empty()
    my_bar = st.progress(0)
    for x in range(0,len(height),10):
        t.markdown('Visualizing Footprints... ' + str(100*round(x/len(height),2)) + '%')
        my_bar.progress(x/len(height))
        
        call = ''
        if x + 10 <= len(height):
            for x in range(x,x+10):
                call = call + str(lat[x]) + ',' + str(lon[x]) + '|'
        else:
            for x in range(x,len(height)):
                call = call + str(lat[x]) + ',' + str(lon[x]) + '|'
        
        call = call[:-1]
        
        req =  'http://api.opentopodata.org/v1/srtm90m?locations=' + call
        resp = requests.get(req).json()
        time.sleep(1)
        
        for item in resp['results']:
            terrain.append(item['elevation'])
    
    my_bar.progress(1.0)
    my_bar.empty()
    t.markdown('Visualization Successful.')
    
    points = list(zip(lon,lat))
    points_geom = MultiPoint(points)
    utm_points = []
    
    for x in range(len(terrain)):
        agl.append(height[x] - terrain[x])
        utm_conv = utm.from_latlon(points[x][1], points[x][0])
        utm_points.append((utm_conv[0], utm_conv[1]))
        utm_zone1 = utm_conv[2]
        utm_zone2 = utm_conv[3]
    
    # Image Footprints
    sensor_x = 35.8
    sensor_y = 23.9
    f = 35
    hfv = 2*math.atan(sensor_x/(2*f))
    vfv = 2*math.atan(sensor_y/(2*f))
    
    footprints = []
    for x in range(len(utm_points)):
        foot = []
        for y in range(0,4):
            if y == 0:
                dx = math.tan(hfv/2 + pitch[x])*agl[x]
                dy = math.tan(vfv/2 + roll[x])*agl[x]
                dutm_x = dx*math.cos(yaw[x]) - dy*math.sin(yaw[x])
                dutm_y = -dx*math.sin(yaw[x]) - dy*math.cos(yaw[x])
                utm_x = utm_points[x][0] + dutm_x
                utm_y = utm_points[x][1] + dutm_y
                
                lat_point = utm.to_latlon(utm_x, utm_y, utm_zone1, utm_zone2)[0]
                lon_point = utm.to_latlon(utm_x, utm_y, utm_zone1, utm_zone2)[1]
                foot.append([lon_point, lat_point])    
            elif y == 1:
                dx = math.tan(-hfv/2 + pitch[x])*agl[x]
                dy = math.tan(vfv/2 + roll[x])*agl[x]
                dutm_x = dx*math.cos(yaw[x]) - dy*math.sin(yaw[x])
                dutm_y = -dx*math.sin(yaw[x]) - dy*math.cos(yaw[x])
                utm_x = utm_points[x][0] + dutm_x
                utm_y = utm_points[x][1] + dutm_y
                
                lat_point = utm.to_latlon(utm_x, utm_y, utm_zone1, utm_zone2)[0]
                lon_point = utm.to_latlon(utm_x, utm_y, utm_zone1, utm_zone2)[1]
                foot.append([lon_point, lat_point])    
            elif y == 2:
                dx = math.tan(-hfv/2 + pitch[x])*agl[x]
                dy = math.tan(-vfv/2 + roll[x])*agl[x]
                dutm_x = dx*math.cos(yaw[x]) - dy*math.sin(yaw[x])
                dutm_y = -dx*math.sin(yaw[x]) - dy*math.cos(yaw[x])
                utm_x = utm_points[x][0] + dutm_x
                utm_y = utm_points[x][1] + dutm_y
                
                lat_point = utm.to_latlon(utm_x, utm_y, utm_zone1, utm_zone2)[0]
                lon_point = utm.to_latlon(utm_x, utm_y, utm_zone1, utm_zone2)[1]
                foot.append([lon_point, lat_point])  
            elif y == 3:
                dx = math.tan(hfv/2 + pitch[x])*agl[x]
                dy = math.tan(-vfv/2 + roll[x])*agl[x]
                dutm_x = dx*math.cos(yaw[x]) - dy*math.sin(yaw[x])
                dutm_y = -dx*math.sin(yaw[x]) - dy*math.cos(yaw[x])
                utm_x = utm_points[x][0] + dutm_x
                utm_y = utm_points[x][1] + dutm_y
                
                lat_point = utm.to_latlon(utm_x, utm_y, utm_zone1, utm_zone2)[0]
                lon_point = utm.to_latlon(utm_x, utm_y, utm_zone1, utm_zone2)[1]
                foot.append([lon_point, lat_point])    
    
        poly = Polygon(foot)
        footprints.append(poly)
    
    footprints_geom = MultiPolygon(footprints)
    points_gdf = gpd.GeoDataFrame(list(zip(names,points_geom)), index=range(len(names)), 
                                  columns=['Image', 'geometry'], crs='EPSG:4326')
    footprints_gdf = gpd.GeoDataFrame(list(zip(names,footprints_geom)), index=range(len(names)), 
                                      columns=['Image', 'geometry'], crs="EPSG:4326")
    
    points_df = pd.DataFrame(list(zip(lat,lon)), index=range(len(lat)), columns=['lat', 'lon'])
    
    
    # Plotting
    
    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/satellite-streets-v11',
        initial_view_state=pdk.ViewState(
            latitude=points_df['lat'].mean(),
            longitude=points_df['lon'].mean(),
            zoom=14,
            pitch=0,
        ),
        layers=[
            pdk.Layer(
                'GeoJsonLayer',
                data=footprints_gdf['geometry'],
                get_fill_color='[39, 157, 245]',
                get_line_color='[39, 157, 245]',
                opacity=0.2,
            ),
            pdk.Layer(
                'ScatterplotLayer',
                data=points_df,
                get_position='[lon, lat]',
                get_color='[0, 0, 0]',
                get_radius=5,
                opacity=0.8
            ),
            ],
    ))    
    st.stop()

else:
    st.stop()
