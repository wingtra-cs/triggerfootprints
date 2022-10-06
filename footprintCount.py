import streamlit as st
import json
import requests
import utm
import math
from shapely.geometry import Polygon, MultiPolygon
import geopandas as gpd
import pydeck as pdk
import pandas as pd
import rasterio.sample

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
    
    model = data['model']
    
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
    
    with st.spinner('Visualizing Footprints...'):
        agl = []
        terrain = []
        
        south = min(lat) - 0.001
        north = max(lat) + 0.001
        west = min(lon) - 0.001
        east = max(lon) + 0.001
        api_key = '9650231c82589578832a8851f1692a2e'
        
        req = 'https://portal.opentopography.org/API/globaldem?demtype=SRTMGL3&south=' + str(south) + '&north=' + str(north) + '&west=' + str(west) + '&east=' + str(east) + '&outputFormat=GTiff&API_Key=' + api_key
        
        resp = requests.get(req)
        open('raster.tif', 'wb').write(resp.content)
        elev = rasterio.open('raster.tif', crs='EPSG:4326')
        points = list(zip(lon,lat))
        
        ctr = 0
        for val in elev.sample(points):
            terrain.append(val[0])
            agl.append(height[ctr] - val[0])
            ctr += 1
        
        mean_agl = round(sum(agl)/len(agl),2)
        st.text('Average AGL: ' + str(mean_agl) + ' meters.')
        
        utm_points = []
        for x in range(len(names)):
            utm_conv = utm.from_latlon(points[x][1], points[x][0])
            utm_points.append((utm_conv[0], utm_conv[1]))
            utm_zone1 = utm_conv[2]
            utm_zone2 = utm_conv[3]
            
        # Image Footprints
        # {model: [x, y, f, tilt]}
        st.text('Payload Used: ' + model + '.')
        
        if model[-2:] != 'v4':
            model = model + " v4"
        
        img_param = {'RX1RII 42MP v4': [35.8, 23.9, 35, 0],
                      'Micasense RE-P v4': [8.52, 7.10, 10.3, 0]}
        sensor_x = img_param[model][0]
        sensor_y = img_param[model][1]
        f = img_param[model][2]
        
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
        footprints_gdf = gpd.GeoDataFrame(list(zip(names,footprints_geom)), index=range(len(names)), 
                                          columns=['Image', 'geometry'], crs="EPSG:4326")
        
        points_df = pd.DataFrame(list(zip(lat,lon)), index=range(len(lat)), columns=['lat', 'lon'])
    
    st.success('Visualization Successful.')
    # Plotting
    
    view = pdk.data_utils.viewport_helpers.compute_view(points_df, view_proportion=1)
    level = int(str(view).split('"zoom": ')[-1].split('}')[0])
    
    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/satellite-streets-v11',
        initial_view_state=pdk.ViewState(
            latitude=points_df['lat'].mean(),
            longitude=points_df['lon'].mean(),
            zoom=level,
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
                opacity=0.7,
                get_position='[lon, lat]',
                get_color='[0, 0, 0]',
                get_radius=5,
            ),
            ],
    ))    
    st.stop()

else:
    st.stop()
