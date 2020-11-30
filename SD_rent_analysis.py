#!/usr/bin/env python
# coding: utf-8

# # Capstone project:
# # La Jolla Rental House Prices in relation to Venues
# ### Author: James Lee
# 
# ## 1. Background
# 
# San Diego is a city on Pacific coast of California with around 1.5  million residents. Because of its warm climate and beaches, San Diego has one of the highest cost of living in California. La Jolla is a seaside neighborhood where UC San Diego is located at and has an even higher cost of living compared to other parts of San Diego. <br> 
# 
# The main purpose of this project is to analyze the relationships between the venues and rental prices across different areas near UCSD.
# <br> 
# 
# 
# ## 2. Dataset
# 
# * I will be obtaining all the data for venues in San Diego through **Foursquare API**.
# <br> <br> 
# * Data for neighborhoods and zip codes are collectedfrom SANDAG. <br> 
# Link Address: https://opendata.arcgis.com/datasets/41c3a7bd375547069a78fce90153cbc0_5.csv?outSR=%7B%22latestWkid%22%3A3857%2C%22wkid%22%3A102100%7D
# 
# <br> <br> 
# * The rental prices dataset was obtained from Zillow. The particular dataset does not include raw rental prices. The values are weighted to rental housing stock to ensure representativeness acorss the entire market. The values are caculated so that they fall into the 40-60th percentile rnage for all rents in a given region in order to represent the average rent prices.
# <br>
# Link Address: http://files.zillowstatic.com/research/public_v2/zori/Metro_ZORI_AllHomesPlusMultifamily_SSA.csv  
# 
# <br>
# 

# 1) Import all the necessary libraries

# In[131]:


import requests # library to handle requests
import pandas as pd # library for data analsysis
import numpy as np # library to handle data in a vectorized manner
import random # library for random number generation
import seaborn as sns

from geopy.geocoders import Nominatim # module to convert an address into latitude and longitude values

# libraries for displaying images
from IPython.display import Image 
from IPython.core.display import HTML 
    
# tranforming json file into a pandas dataframe library
from pandas.io.json import json_normalize

import folium # plotting library

print('Libraries imported.')


# 2) Download all the region info (zip codes and communities)
# <br>

# In[2]:


district = pd.read_csv('https://opendata.arcgis.com/datasets/41c3a7bd375547069a78fce90153cbc0_5.csv?outSR=%7B%22latestWkid%22%3A3857%2C%22wkid%22%3A102100%7D')
district = district[['ZIP', 'COMMUNITY']]
district.head()


# 3) import all the adjusted rent data from Zillow
# <br>

# In[3]:


rent_temp = pd.read_csv('http://files.zillowstatic.com/research/public_v2/zori/Zip_ZORI_AllHomesPlusMultifamily_SSA.csv')
rent_temp = rent_temp[rent_temp.MsaName == 'San Diego, CA']
rent_temp.shape


# In[4]:


rent = rent_temp.iloc[:, [1, 85]] 
rent.columns = ['ZIP', 'rent']
rent.shape


# 4) Import latitude and longitude info and match with rent dataframe

# In[5]:


coordinates = pd.read_csv('https://public.opendatasoft.com/explore/dataset/us-zip-code-latitude-and-longitude/download/?format=csv&timezone=America/Los_Angeles&lang=en&use_labels_for_header=true&csv_separator=%3B', sep=';')
coordinates = coordinates[['Zip', 'Latitude', 'Longitude']]
coordinates.columns = ['ZIP', 'lat', 'lng']


# In[6]:


coordinates.head()


# In[7]:


merged_df1 = rent.merge(coordinates, how='inner', on='ZIP')
merged_df1.head()


# In[8]:


merged_df1.shape


# In[9]:


merged_df = merged_df1.merge(district, how='inner', on='ZIP')
merged_df.head()


# 5) Input the Foursquare API credentials below

# In[10]:


CLIENT_ID = '4F3OHVNT3U3RPUMFIX4CFGUI0JGY4PQCEWS3O2K44BYAVMEZ' # your Foursquare ID
CLIENT_SECRET = 'EPSZOXGJ0XBNCF53QFEIS1PS4VSDED0MFNVX0HWH0W2SJASL' # your Foursquare Secret
ACCESS_TOKEN = 'RBRF5NB4DRMNX4LBATUAMGLKJRTT0GX2A5RAENH55JJ1JYOL' # your FourSquare Access Token
VERSION = '20180604'
LIMIT = 50
print('Your credentails:')
print('CLIENT_ID: ' + CLIENT_ID)
print('CLIENT_SECRET:' + CLIENT_SECRET)


# In[13]:


merged_df.head()


# In[288]:


# convert ZIP's data type to 'object' first
final_df = merged_df
final_df['ZIP'] = final_df['ZIP'].astype('object')
final_df.head()


# 6) Now let's search up to 50 venues in each region (within 500m radius)  <br>
# (The only issue with free Foursquare API is that the limit of query result is set to 50...)

# In[86]:


search_query = ''
radius = 500
LIMIT = 50
vdf = pd.DataFrame([])

# create a new dataframe with venues in each region
for lat, lng in zip(final_df['lat'], final_df['lng']):
    latitude = lat
    longitude = lng
    url = 'https://api.foursquare.com/v2/venues/search?client_id={}&client_secret={}&ll={},{}&oauth_token={}&v={}&query={}&radius={}&limit={}'.format(CLIENT_ID, CLIENT_SECRET, latitude, longitude, ACCESS_TOKEN, VERSION, search_query, radius, LIMIT)
    results = requests.get(url).json()
    venues = results['response']['venues']
    temp_df = json_normalize(venues)
    temp_df = temp_df[['name', 'categories', 'location.postalCode']]
    temp_df.columns = ['venue', 'categories', 'ZIP']
    vdf = vdf.append(temp_df)


# In[161]:


vdf_valid = vdf.dropna()
vdf_valid.head()


# In[162]:


vdf_update = vdf_valid

# function that extracts the category of the venue
def get_category_type(row):
    
    categories_list = row['categories']
        
    if len(categories_list) == 0:
        return None
    else:
        return categories_list[0]['name']


# In[163]:


# filter the category for each row
vdf_update['categories'] = vdf_valid.apply(get_category_type, axis=1)


# In[306]:


vdf_final = vdf_update.dropna()
vdf_final.head()


# 7) Before drawing the map, merge the final_df with coorindate values with the venue information

# In[189]:


vdf_count = vdf_final.value_counts('ZIP').rename_axis('unique_values').reset_index(name='counts')
vdf_count.head()


# In[273]:


vdf_count.columns = ['ZIP', 'count']
vdf_count.head()


# In[313]:


vdf_count['ZIP'] = vdf_count['ZIP'].astype(str)
vdf_final['ZIP'] = vdf_final['ZIP'].astype(str)
final_df['ZIP'] = final_df['ZIP'].astype(str)


# In[311]:


#delete all the specific zip code appendices. (e.g For ZIP 92037-1234, we want to eliminate -1234 at the end)
final_df['ZIP']=final_df['ZIP'].str.split('-').str[0]


# In[314]:


#extract integers from string
vdf_count['ZIP'] = vdf_count.ZIP.str.extract('(\d+)').astype(int)
vdf_final['ZIP'] = vdf_final.ZIP.str.extract('(\d+)').astype(int)
final_df['ZIP'] = final_df.ZIP.str.extract('(\d+)').astype(int)


# In[338]:


map_df = final_df.merge(vdf_final, on = 'ZIP', how ='left')
map_df['lat'] = map_df['lat'].astype('float64')
map_df['lng'] = map_df['lng'].astype('float64')
map_df


# In[325]:


map_df.value_counts('categories').shape


# **There are 373 unique venues!**

# In[346]:


#make a smaller dataset with counts instead of all categories
map_df2 = final_df.merge(vdf_count, on = 'ZIP', how ='left')


# 8) Visualization of rents in San Diego

# In[448]:


#set latitude and logitude value to UCSD
address = 'UCSD'

geolocator = Nominatim(user_agent="foursquare_agent")
location = geolocator.geocode(address)
SD_latitude = location.latitude
SD_longitude = location.longitude
print(latitude, longitude)


# Use folium library to generate a map of SD

# In[449]:


UCSD_map = folium.Map(location=[SD_latitude, SD_longitude], zoom_start=10) # generate map centred around UCSD

# add a red circle marker to represent UCSD
folium.CircleMarker(
    [SD_latitude, SD_longitude],
    radius=15,
    color='red',    
    popup='UCSD',
    fill = True,
    fill_color = 'red',
    fill_opacity = 0.6
).add_to(UCSD_map)

# add the restaurants as blue circle markers
for lat, lng in zip(map_df2.lat, map_df2.lng):
    folium.CircleMarker(
        [lat, lng],
        radius=5,
        color='blue',
        fill = True,        
        fill_color='blue',
        fill_opacity=0.6
    ).add_to(UCSD_map)

# display map
UCSD_map


# 

# ## Scatterplot of rent cost  in San Diego

# In[417]:


splot = sns.scatterplot(data = map_df2, x = 'COMMUNITY', y= 'rent', color = 'red')
splot.set_xticklabels(splot.get_xticklabels(), rotation=90)
splot


# ## Use Choropleth to take a look at the rent

# In[426]:


#Download GeoJSON file of San Diego
SD_geo = 'https://data.sandiegocounty.gov/api/geospatial/vsuf-uefy?method=export&format=GeoJSON'


# Now we have to convert ZIP back to string again since this GeoJSON contains all features as strings

# In[437]:


map_df3 = map_df2
map_df3['ZIP'] = map_df2['ZIP'].astype(str)


# In[443]:


#set latitude and logitude value to SD
address = 'Ramona, San Diego'

geolocator = Nominatim(user_agent="foursquare_agent")
location = geolocator.geocode(address)
latitude = location.latitude
longitude = location.longitude
print(latitude, longitude)


# In[452]:


# create a plain world map
SD_map = folium.Map(location=[latitude, longitude], zoom_start=10)

SD_map.choropleth(
    geo_data=SD_geo,
    data=map_df3,
    columns=['ZIP', 'rent'],
    key_on='feature.properties.zip',
    fill_color='YlOrRd', 
    fill_opacity=0.7, 
    line_opacity=0.2,
    legend_name='Rent in San Diego'
)

# add a red circle marker to represent UCSD
folium.CircleMarker(
    [SD_latitude, SD_longitude],
    radius=15,
    color='blue',    
    popup='UCSD',
    fill = True,
    fill_color = 'blue',
    fill_opacity = 0.6
).add_to(SD_map)

SD_map


# The graph above shows different areas in SD with their rent cost. The blue dot is my school, UC San Diego

# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:




