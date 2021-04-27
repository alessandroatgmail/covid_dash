from dash import Dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
import plotly.express as px
from flask import Flask
import folium
import pandas as pd
from folium.plugins import TimestampedGeoJson
import json
import branca
import numpy as np
from folium import plugins
import re
import branca
import os
THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))

############################################################################
# LOAD DATA
############################################################################

colorscale = branca.colormap.linear.YlOrRd_09.scale(0, 200e2)

# load regional data
regions_data = pd.read_csv('covid19_italy_region.csv')
regions_data['Date'] = pd.to_datetime(regions_data['Date'])
# region_geo = 'italy-regions.json'
# f = open(region_geo)
# regions_json=json.load(f)

filename = os.path.join(THIS_FOLDER, "region-fetures.json")
f = open(filename)
features=json.load(f)

# # load provincial data
# provinces_data = pd.read_csv('covid19_italy_province.csv')
# provinces_data['Date'] = pd.to_datetime(provinces_data['Date'])
# provinces_geo = 'italy-provinces.json'
# f = open(provinces_geo)
# provinces_json=json.load(f)

# load world data

world = pd.read_csv("covid_19_clean_complete.csv")
world['Date'] = pd.to_datetime(world['Date'])
world = world[world['Province/State'].isna() == True]
world['actual_cases'] = 0
world['actual_cases'] = world['Confirmed'] - world['Recovered'] - world['Deaths']

print (world.head())

world_geo = 'countries.json'
world_geo = os.path.join(THIS_FOLDER, world_geo)
f = open(world_geo)
world_json = json.load(f)

########################################################################
# CREATE FEATURES FOR REGIONS MAP
#######################################################################
# features = []
# i=0


# for d in regions_data['Date'].unique():
#     region_geo = 'italy-regions.json'
#     g = open(region_geo)
#     f=json.load(g)
#     for r in regions_data['RegionCode'].unique():
#         f['features'][r-1]['properties'] = {
#             'area': regions_json['features'][r-1]['properties']['area'],
#             'times': [np.datetime_as_string(d, unit='D')],
#             'style': {
#                     'bodercolor': 'Black',
#                   'color': colorscale (regions_data[(regions_data['RegionCode'] == r) &
#                     (regions_data['Date']==d)].groupby(
#                     ['RegionCode', 'Date']).sum()['TotalPositiveCases'].values
#                     ),
#                     'weight': 1,
#                     'line_opacity':100
#                     },
#             'name': regions_json['features'][r-1]['properties']['name'],
#             'length': regions_json['features'][r-1]['properties']['length'],
#             'id': regions_json['features'][r-1]['properties']['id']


#         }

#     features.append(f)

########################################################################
# PRINT MAP FOR REGIONS
#######################################################################

m= folium.Map(location=[41.878552, 12.509186],
                        zoom_start=6,
                        tiles="Stamen Toner")

plugins.TimestampedGeoJson({
    'type': 'FeatureCollection',
    'features': features,
    'loop': False
}, period='P1D', add_last_point=True).add_to(m)
# folium.LayerControl().add_to(m)
colorscale.caption = 'covid 19 number of casese'
m.add_child(colorscale)

html_map = m.get_root().render()


############################################################################
# BUILD WORLD MAP
############################################################################

world.loc[world['Country/Region'] == 'US', ['Country/Region']] = 'United States of America'
world_last = world[(world['Date'] == world['Date'].max()) &
                  (world['Province/State'].isna() == True)]
world_last2 = world[(world['Date'] == world['Date'].max()) &
                  (world['Province/State'].isna() == False)]
world_last2 = world_last2.groupby('Country/Region').sum().reset_index()
world_last2 = world_last2[world_last2['Confirmed'] > 1000]
world_last.drop('Province/State', inplace=True, axis=1)
world_last3 = pd.concat([world_last, world_last2], ignore_index=True )

fig = px.choropleth_mapbox(
            world_last3,
            geojson=world_json,
            locations='Country/Region',
            featureidkey="properties.ADMIN",
            color='Confirmed',
            color_continuous_scale="Sunsetdark",
            range_color=(0, world_last['Confirmed'].max()),
            mapbox_style="carto-positron",
            zoom=1,
            center = {"lat": 37.0902, "lon": -95.7129},
            opacity=0.5,
            )
fig.update_layout(margin={"r":0,"t":5,"l":0,"b":0})

p_style = {
        'margin-bottom': '0px',
        'margin-top': '0px',
        'display': 'inline-block'
    }

############################################################################
# RUNNING DASH APP
############################################################################
app = Dash()


app.layout = html.Div([
                html.H1('COVID-19 GEO DISTRIBUTION'),
                html.P("""
                This work represent just an example of a dashboard created with Dash a plotly opensource platform that enable to build interactive plots using only python
                """),
                html.P("""
                More information on plotly and dash at the official page:
                """, style=p_style),
                dcc.Link('https://plotly.com/dash/', href='https://plotly.com/dash/'),
                html.P("""
                Data are from kaggle and are update from time to time:
                """, style={
                    'margin-bottom': '0px',
                    'margin-top': '0px'
                    }),
                html.P("""
                World dataset is from here:
                """, style=p_style),
                dcc.Link('https://www.kaggle.com/imdevskp/corona-virus-report',
                        href='''
                            https://www.kaggle.com/imdevskp/corona-virus-report
                            '''),
                html.Br(),
                html.P('and data for Italian region are from: '
                , style=p_style
                ),
                dcc.Link('https://www.kaggle.com/imdevskp/corona-virus-report',
                      href='https://www.kaggle.com/imdevskp/corona-virus-report'),
                html.Br(style={'margin-bottom': '5px'}),

                html.Div([
                    dcc.Tabs(id='main-tab', value='', children=[
                        dcc.Tab(label="World", children=[
                            html.Div( children =[
                                html.Div(
                                    children=[
                                        html.P('''
                                        Click on a country to visualize details and timeseries plot
                                        ''')
                                        ],
                                    style={'width': '100%'}),
                                html.Div(
                                    id='info',
                                    style={'width': '30%',
                                           'height':'100%',
                                           'display':'inline-block',
                                           'vertical-align': 'top'}
                                ),
                                html.Div(
                                    dcc.Graph(id='world-map',
                                         figure=fig
                                         ),
                                    style ={'width': '35%', 'height':'100%', 'display':'inline-block'}
                                ),
                                html.Div( id='barplot',
                                 style = {'width': '30%',
#                                           'height':'800px',
                                          'display':'inline-block'}
                                ),
#
                            ],
                             style = {
                                    'margin-top': '5%'

                             } # style main div

                             ) # end main Div including in world-map and barplot
                        ]),   # end tab world

                        dcc.Tab( label="italy", value='Italy', children=[
                        dcc.Interval(id='interval',
                            interval=3000,
                            n_intervals=0),
                        html.Iframe(
                            id='italy-map',
                            srcDoc=html_map,
                            style={'width': '100%', 'height':'800px'})]),
                        dcc.Tab(label='Countries comparison', value='altro',
                               children=[
                                   html.Div(
                                       children = [
                                           html.Div(id='Filters', children=[
                                               html.H3('''
                                               Please choose one or more countries fot time series about confirmed cases, deaths, recovered people and currente actual cases
                                               ''',
                                                style={'width':'50%'}),
                                               dcc.Dropdown(
                                                    id='country-filter',
                                                    options = [{'label':c, 'value': c} for c in world_last3['Country/Region'].unique()],
                                                   multi=True,
                                                   style={'width':'80%', 'bottom-margin': '2%'}
                                               ),
                                        html.Div(
                                              id='idgraphs',
                                              children=[
                                              html.Div( children=[
                                                  html.Div(
                                                      id='confirmed_graph',
                                                      children=[],
                                                      style ={'width': '40%',
                                                      'display':'inline-block',
                                                      'margin-left': '5%'
                                                      }
                                                  ),
                                                  html.Div(
                                                      id='deaths_graph',
                                                      children=[],
                                                      style ={
                                                            'width': '40%',
                                                            'display':'inline-block',
                                                            'margin-left': '5%'}
                                                  )],
                                                    style={'margin-bottom': '5%'},
                                                  ),
                                              html.Div( children = [
                                                  html.Div(
                                                      id='recovered_graph',
                                                      children=[],
                                                      style ={
                                                            'width': '40%',
                                                            'display':'inline-block',
                                                            'margin-left': '5%'
                                                            }
                                                  ),
                                                  html.Div(
                                                      id='actual_graph',
                                                      children=[],
                                                      style ={
                                                            'width': '40%',
                                                            'display':'inline-block',
                                                            'margin-left': '5%'}
                                                  )],
                                                  style={'margin-bottom': '5%'},
                                                  ),
                                              ]
                                        )
                                         ],
                                   style = {} # style the main div
                                   ) # end main diiv
                               ]) # end tab
                    ])

                ], style={'width':'100%',
#                           'height':'80%',
                          'display':'inline-block',
                          'align':'center',
                          },
                    ),
                ],style={'width':'100%', 'display':'inline-block'})# end first Div
], style={'margin-left': '10%', 'margin-right': '10%'})


###############################################################################
# CALLBACK TO SHOW INFO AND BARPLOT FOR SELECTED COUNTRY
###############################################################################

@app.callback(Output('barplot','children'),
             [Input('world-map', 'clickData')])
def callback_graph(clickData):
    # filter data for location
    if clickData:
        df = world[world['Country/Region'] == clickData['points'][0]['location']]

        nat_data = go.Figure(go.Bar(x=df['Date'], y=df['Deaths'], name='Deaths'))
        nat_data.add_trace(go.Bar(x=df['Date'], y=df['Recovered'], name='Recovered'))
        nat_data.add_trace(go.Bar(x=df['Date'], y=df['actual_cases'], name='Actual Cases'))

        nat_data.update_layout(barmode='stack',
                              legend=dict(x=0, y=1),
                              xaxis={'categoryorder':'array', 'categoryarray':df['Date']},
                              height=400, margin={"r":0,"t":5,"l":0,"b":0})
        return dcc.Graph (id='output-graph', figure=nat_data)

@app.callback(Output('info','children'),
             [Input('world-map', 'clickData')])
def update_info(clickData):
    if clickData:
        vals = world_last3[world_last3['Country/Region'] == clickData['points'][0]['location']][
            ['Confirmed', 'Recovered', 'Deaths', 'actual_cases', 'Date']].values[0]
        children = [
                html.H1('Country: {}'.format(clickData['points'][0]['location'])),
                html.H2('Totals at date: {}'.format(vals[4])),
                html.H3('Total Confirmed Cases: {}'.format(
                    vals[0])),
                html.H3('Total Recovered Cases: {}'.format(
                    vals[1])),
                html.H3('Total Death: {}'.format(
                    vals[2])),
                html.H3('Total Actual Cases: {}'.format(
                    vals[3])),
        ]

        return children

###############################################################################
#  CALL BACKS FOR TAB COUNTRIES COMPARISON
###############################################################################

@app.callback(Output('confirmed_graph', 'children'),
              [Input('country-filter', 'value')])
def update_confirmed_graph(countries):
    if countries:
        nat_data = go.Figure()
        for c in countries:
            df = world[world['Country/Region'] == c]
            nat_data.add_trace(go.Scatter(x=df['Date'], y=df['Confirmed'], name=c))
        nat_data.update_layout(
                # title="Confirmed Positive Cases",
                legend=dict(x=0, y=1),
                margin={"r":0,"t":5,"l":0,"b":0})
#         print (nat_data)
        children = html.Div(children=[
            html.H3('Total confirmed Cases'),
            dcc.Graph (id='output-confirmed-graph', figure=nat_data)
        ],
        )
        return children

@app.callback(Output('deaths_graph', 'children'),
              [Input('country-filter', 'value')])
def update_confirmed_graph(countries):
    if countries:
        nat_data = go.Figure()
        for c in countries:
            df = world[world['Country/Region'] == c]
            nat_data.add_trace(go.Scatter(x=df['Date'], y=df['Deaths'], name=c))
        nat_data.update_layout(
                # title="Number of Death00s",
                legend=dict(x=0, y=1),
                margin={"r":0,"t":5,"l":0,"b":0})
        children = html.Div(children=[
            html.H3('Total Number of Deaths'),
            dcc.Graph (id='output-confirmed-graph', figure=nat_data)
        ])
#         print (nat_data)
        return children

@app.callback(Output('recovered_graph', 'children'),
              [Input('country-filter', 'value')])
def update_confirmed_graph(countries):
    if countries:
        nat_data = go.Figure()
        for c in countries:
            df = world[world['Country/Region'] == c]
            nat_data.add_trace(go.Scatter(x=df['Date'], y=df['Recovered'], name=c))
        nat_data.update_layout(
                # title="Recovered",
                legend=dict(x=0, y=1),
                margin={"r":0,"t":5,"l":0,"b":0})
        children = html.Div(children=[

            html.H3('Total Recovered'),
            dcc.Graph (id='output-confirmed-graph', figure=nat_data)
            ])
        return children

@app.callback(Output('actual_graph', 'children'),
              [Input('country-filter', 'value')])
def update_confirmed_graph(countries):
    if countries:
        nat_data = go.Figure()
        for c in countries:
            df = world[world['Country/Region'] == c]
            nat_data.add_trace(go.Scatter(x=df['Date'], y=df['actual_cases'], name=c))
        nat_data.update_layout(
                    # title="Acutal Positives",
                    legend=dict(x=0, y=1),
                    margin={"r":0,"t":5,"l":0,"b":0})
        children = html.Div(children=[
        html.H3('Total Number of Actual Positive Cases'),
        dcc.Graph (id='output-confirmed-graph', figure=nat_data)
        ])
        return children


if __name__ == '__main__':
    # from waitress import serve
    # serve(app, host='0.0.0.0', port=8050)
    app.run_server()
