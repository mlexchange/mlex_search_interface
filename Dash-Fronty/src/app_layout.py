import base64
import dash
from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from dash import dash_table
import dash_uploader as du
import dash_daq as daq
from dash.exceptions import PreventUpdate
from file_manager import filename_list, move_a_file, move_dir, docker_to_local_path, \
                         add_paths_from_dir, check_duplicate_filename
from helper_utils import blank_fig
import imageio
import json
import math
import numpy as np
import os
import pathlib
import plotly.express as px
import requests
import shutil
import templates
import uuid
import zipfile

#------------App Setup-------------------#
external_stylesheets = [dbc.themes.BOOTSTRAP, "assets/segmentation-style.css"]

app = Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)

app.title = 'MLExchange Search'

#------------Global Variable-------------#
USER = 'Dummy-Searcher' 

NUMBER_OF_ROWS = 4
NUMBER_IMAGES_PER_ROW = 4

DOCKER_DATA = pathlib.Path.home() / 'data'
LOCAL_DATA = str(os.environ['DATA_DIR'])
DOCKER_HOME = str(DOCKER_DATA) + '/'
LOCAL_HOME = str(LOCAL_DATA) 

UPLOAD_FOLDER_ROOT = DOCKER_DATA / 'query'
du.configure_upload(app, UPLOAD_FOLDER_ROOT, use_upload_id=False)

#--------------------------Start Layout---------------------------#
header = templates.header('search')

#----------Text Search Panel---------------#
content_meta = ["name", "version", "type", "uri", "reference", 
                "description", "content_type", "content_id", "owner"]

text_search_card = dbc.Card(
    id = "text-search-card",
    children = [
        html.H2("Text"),
        html.Hr(),
        dbc.Label("Type in Keyword Here: "),
        dbc.Row([
            dbc.Col(
                dbc.Input(
                    id = 'text-input', 
                    type = 'text', 
                    placeholder = 'Your Keyword'), 
                width = True),
            dbc.Col(
                dbc.Button(
                    "Search",
                    id = "text-search-button",
                    color = "success",
                    n_clicks = 0,
                    style = {'width':'100%'}
                    ),
                width = 3
                ),
            ], 
            justify = "end"
            ),
        html.Br(),        
        dash_table.DataTable(
            id = 'text-output',
            columns = ([{'id': param, 'name': param} for param in content_meta]),
            row_selectable = 'multi',
            editable = False,
            style_cell = {'padding': '0.5rem', 'textAlign': 'left'},
            css = [{"selector": ".show-hide", "rule": "display: none"}],
            style_table = {'height':'20rem', 'overflowY': 'auto'}
            ),
        ])

#---------File Manager Layouts-------------#
# files display
file_paths_table = html.Div(
        children=[
            dash_table.DataTable(
                id='files-table',
                columns=[
                    {'name': 'type', 'id': 'file_type'},
                    {'name': 'File Table', 'id': 'file_path'},
                ],
                data = [],
                hidden_columns = ['file_type'],
                row_selectable='single', #'multi',
                style_cell={'padding': '0.5rem', 'textAlign': 'left'},
                fixed_rows={'headers': False},
                css=[{"selector": ".show-hide", "rule": "display: none"}],
                style_data_conditional=[
                    {'if': {'filter_query': '{file_type} = dir'},
                     'color': 'blue'},
                 ],
                style_table={'height':'18rem', 'overflowY': 'auto'}
            )
        ]
    )

# UPLOAD DATASET OR USE PRE-DEFINED DIRECTORY
data_access = html.Div([
    dbc.Card([
        dbc.CardBody(id='data-body',
                      children=[
                          dbc.Label('1. Upload a new file or a zipped folder:', className='mr-2'),
                          html.Div([du.Upload(
                                            id="dash-uploader",
                                            max_file_size=60000,  # 1800 Mb
                                            cancel_button=True,
                                            pause_button=True
                                    )],
                                    style={  # wrapper div style
                                        'textAlign': 'center',
                                        'width': '770px',
                                        'padding': '5px',
                                        'display': 'inline-block',
                                        'margin-bottom': '10px',
                                        'margin-right': '20px'},
                          ),
                          dbc.Label('2. Choose files/directories:', className='mr-2'),
                          dbc.Row([
                            dbc.Col(
                                dbc.Row([
                                    dbc.Col(dbc.InputGroupText("Browse Format: ", style={'height': '2.5rem', 'width': '100%'}),
                                            width=5),
                                    dbc.Col(dcc.Dropdown(
                                                id='browse-format',
                                                options=[
                                                    {'label': 'dir', 'value': 'dir'},
                                                    {'label': 'all (*)', 'value': '*'},
                                                    {'label': '.png', 'value': '*.png'},
                                                    {'label': '.jpg/jpeg', 'value': '*.jpg,*.jpeg'},
                                                    {'label': '.tif/tiff', 'value': '*.tif,*.tiff'},
                                                    {'label': '.txt', 'value': '*.txt'},
                                                    {'label': '.csv', 'value': '*.csv'},
                                                ],
                                                value='dir',
                                                style={'height': '2.5rem', 'width': '100%'}),
                                            width=7)
                                ], className="g-0"),
                                width=4,
                            ),
                            dbc.Col([
                                dbc.Button("Delete the Selected",
                                             id="delete-files",
                                             className="ms-auto",
                                             color="danger",
                                             size='sm',
                                             outline=True,
                                             n_clicks=0,
                                             style={'width': '100%', 'height': '2.5rem'}
                                    ),
                                dbc.Modal([
                                    dbc.ModalHeader(dbc.ModalTitle("Warning")),
                                    dbc.ModalBody("Files cannot be recovered after deletion. Do you still want to proceed?"),
                                    dbc.ModalFooter([
                                        dbc.Button(
                                            "Delete", id="confirm-delete", color='danger', outline=False, 
                                            className="ms-auto", n_clicks=0
                                        )])
                                    ],
                                    id="modal",
                                    is_open=False,
                                    style = {'color': 'red'}
                                )
                            ], width=2),
                            dbc.Col(
                                dbc.Row([
                                    dbc.Col(dbc.InputGroupText("Import Format: ", style={'height': '2.5rem', 'width': '100%'}),
                                            width=5),
                                    dbc.Col(dcc.Dropdown(
                                            id='import-format',
                                            options=[
                                                {'label': 'all files (*)', 'value': '*'},
                                                {'label': '.png', 'value': '*.png'},
                                                {'label': '.jpg/jpeg', 'value': '*.jpg,*.jpeg'},
                                                {'label': '.tif/tiff', 'value': '*.tif,*.tiff'},
                                                {'label': '.txt', 'value': '*.txt'},
                                                {'label': '.csv', 'value': '*.csv'},
                                            ],
                                            value='*',
                                            style={'height': '2.5rem', 'width': '100%'}),
                                            width=7)
                                ], className="g-0"),
                                width=4
                            ),
                            dbc.Col(
                                dbc.Button("Import",
                                             id="import-dir",
                                             className="ms-auto",
                                             color="secondary",
                                             size='sm',
                                             outline=True,
                                             n_clicks=0,
                                             style={'width': '100%', 'height': '2.5rem'}
                                ),
                                width=2,
                            ),
                          ]),        
                        dbc.Label('3. (Optional) Move a file or folder into a new directory:', className='mr-2'),
                        dbc.Button(
                            "Open File Mover",
                            id="file-mover-button",
                            size="sm",
                            className="mb-3",
                            color="secondary",
                            outline=True,
                            n_clicks=0,
                        ),
                        dbc.Collapse(
                            html.Div([
                                dbc.Col([
                                      dbc.Label("Home data directory (Docker HOME) is '{}'.\
                                                 Dataset is by default uploaded to '{}'. \
                                                 You can move the selected files or directories (from File Table) \
                                                 into a new directory.".format(DOCKER_DATA, UPLOAD_FOLDER_ROOT), className='mr-5'),
                                      html.Div([
                                          dbc.Label('Move data into directory:', className='mr-5'),
                                          dcc.Input(id='dest-dir-name', placeholder="Input relative path to Docker HOME. e.g., test/dataset1", 
                                                        style={'width': '40%', 'margin-bottom': '10px'}),
                                          dbc.Button("Move",
                                               id="move-dir",
                                               className="ms-auto",
                                               color="secondary",
                                               size='sm',
                                               outline=True,
                                               n_clicks=0,
                                               #disabled = True,
                                               style={'width': '22%', 'margin': '5px'}),
                                      ],
                                      style = {'width': '100%', 'display': 'flex', 'align-items': 'center'},
                                      )
                                  ])
                             ]),
                            id="file-mover-collapse",
                            is_open=False,
                        ),
                        html.Div([ html.Div([dbc.Label('4. (Optional) Show Local/Docker Path')], style = {'margin-right': '10px'}),
                                    daq.ToggleSwitch(
                                        id='my-toggle-switch',
                                        value=False
                                    )],
                            style = {'width': '100%', 'display': 'flex', 'align-items': 'center', 'margin': '10px', 'margin-left': '0px'},
                        ),
                        file_paths_table,
                        ]),
    ],
    id="data-access",
    )
])

file_explorer = html.Div(
    [
        dbc.Button(
            "Toggle File Manager",
            id="collapse-button",
            size="lg",
            className="m-2",
            color="secondary",
            outline=True,
            n_clicks=0,
        ),
        dbc.Button(
            "Clear Images",
            id="clear-data",
            size="lg",
            className="m-2",
            color="secondary",
            outline=True,
            n_clicks=0,
        ),
        dbc.Collapse(
            data_access,
            id="collapse",
            is_open=True,
        ),
    ]
)

# DISPLAY DATASET
display = html.Div(
    [
        #file_explorer,
        html.Div(id='output-image-upload'),
        dbc.Row([
            dbc.Col(dbc.Row(dbc.Button('<', id='prev-page', style={'width': '10%'}, disabled=True), justify='end')),
            dbc.Col(dbc.Row(dbc.Button('>', id='next-page', style={'width': '10%'}, disabled=True), justify='start'))
        ],justify='center'
        )
    ]
)

browser_cache =html.Div(
        id="no-display",
        children=[
            dcc.Store(id='docker-file-paths', data=[]),
            dcc.Store(id='current-page', data=0),
            dcc.Store(id='image-order', data=[]),
            dcc.Store(id='counter', data=0),
            dcc.Store(id='dummy-data', data=0)
        ],
    )

#-----------Image Search Panel--------------#
image_search_card = dbc.Card(
    id = "image-search-card",
    children = [
        html.H2("Image"),
        html.Hr(),
        dbc.Row([
            dbc.Col(
                dcc.Dropdown(
                    options = [
                            {'label': 'Cells', 'value': 'cells'},
                            {'label': 'Fibers', 'value': 'fibers'},
                            {'label': 'GISAXS', 'value': 'gisaxs'},
                            ],
                    id = 'category',
                    placeholder = "Select Category",
                    )
                ),
            dbc.Col(
                dcc.Dropdown(
                    options = [
                            {'label': 'Inception_resnet', 'value': 'pretrained_inception_resnet'},
                            {'label': 'VGG16', 'value': 'pretrained_vgg16'},
                            {'label': 'Nasnet', 'value': 'pretrained_nasnet'},
                            ],
                    id = 'cnn',
                    placeholder = "Select CNN",
                    )
                ),
            dbc.Col(
                dcc.Dropdown(
                    options = [
                            {'label': 'Faiss', 'value': 'faiss'},
                            {'label': 'Brute Force', 'value': 'bf'},
                            {'label': 'KDTree', 'value': 'kd'},
                            {'label': 'BallTree', 'value': 'bt'},
                            ],
                    id = 'searching-method',
                    placeholder = "Select Searching Method",
                    )
                ),
            dbc.Col(
                dcc.Dropdown(
                    options = [
                            {'label': '1', 'value': 1},
                            {'label': '2', 'value': 2},
                            {'label': '3', 'value': 3},
                            {'label': '4', 'value': 4},
                            {'label': '5', 'value': 5},
                            {'label': '6', 'value': 6},
                            {'label': '7', 'value': 7},
                            {'label': '8', 'value': 8},
                            {'label': '9', 'value': 9},
                            {'label': '10', 'value': 10},
                            ],
                    id = 'number-of-images',
                    placeholder = "Select Result Image Number",
                    )
                ),
            dbc.Col(
                dbc.Button(
                    "Search",
                    id = "image-search-button",
                    color = "success",
                    n_clicks = 0,
                    style = {'width':'100%'}
                    ),
                width = 3
                ),
            ], 
            justify = "end"
            ),
        html.Br(),
        dbc.Label("Upload Image Here: "),   
        file_explorer,
        dbc.Row([
            dbc.Col(display, width = 6),
            dbc.Col(dcc.Graph(id='image-search-results', figure = blank_fig()), width = 6),
        ])
])

job_status_display = [
    html.Div(
        children=[
            dash_table.DataTable(
                id='job-table',
                columns=[
                    {'name': 'ID', 'id': 'job_id'},
                    {'name': 'Type', 'id': 'job_type'},
                    {'name': 'Status', 'id': 'status'},
                    {'name': 'Database', 'id': 'database'},
                    {'name': 'CNN', 'id': 'cnn'},
                    {'name': 'Searching Method', 'id': 'searching_method'},
                    {'name': 'Number of Retrieved Images', 'id': 'number_of_images'},
                ],
                data = [],
                hidden_columns = ['job_id'],
                row_selectable='single',
                style_cell={'padding': '1rem', 'textAlign': 'left'},
                css=[{"selector": ".show-hide", "rule": "display: none"}],
                style_data_conditional=[
                    {'if': {'column_id': 'status', 'filter_query': '{status} = complete'},
                     'backgroundColor': 'green',
                     'color': 'white'},
                    {'if': {'column_id': 'status', 'filter_query': '{status} = failed'},
                     'backgroundColor': 'red',
                     'color': 'white'}
                ],
                style_table={'height':'18rem', 'overflowX': 'auto', 'overflowY': 'auto'}
            ),
            dcc.Interval(
                id='job-refresher',
                interval=2*1000, # milliseconds
                n_intervals=0,
                ),
            ]
        )
    ]

job_display = dbc.Card(
    id = "job-display",
    children = [
        dbc.Row([
            dbc.Col(
                dbc.Card(
                    children = [
                        dbc.CardHeader("List of Jobs"),
                        dbc.CardBody(job_status_display)
                    ],
                ),
                width = 9),
            dbc.Col(
                dbc.Card(
                    children = [
                        dbc.CardHeader("Job Logs"),
                        dbc.CardBody(
                            dcc.Textarea(id='job-logs',
                                 value='',
                                 style={'width': '100%', 'height': '10rem'})
                        )
                    ],
                ),
                width = 3),    
        ])
    ]
)

#-----------Overall Layout--------------#
app.layout = html.Div([
    header,
    dbc.Container([
        dbc.Row(html.H1("What do you want to search?")),
        dbc.Row(text_search_card),
        dbc.Row(image_search_card),
        dbc.Row(job_display),
        dbc.Row(browser_cache),
        ]),
])
