import dash
from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from dash import dash_table
import dash_uploader as du
import dash_daq as daq
from dash.exceptions import PreventUpdate
import imageio
import numpy as np
import plotly.express as px
import plotly.graph_objs as go
import requests
import json
import datetime
import os
import pathlib
import zipfile
import shutil
from file_manager import filename_list, docker_to_local_path
import helper_utils
import uuid


#------------App Setup------------#
external_stylesheets = [dbc.themes.BOOTSTRAP, "assets/segmentation-style.css"]

app = Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)

#------------Global Variable-------------#
USER = 'Dummy-Searcher' 

DOCKER_DATA = pathlib.Path.home().parent / 'data'
LOCAL_DATA = str(os.environ['DATA_DIR'])
DOCKER_HOME = str(DOCKER_DATA) + '/'
LOCAL_HOME = str(LOCAL_DATA) 

UPLOAD_FOLDER_ROOT = DOCKER_DATA / 'query'
du.configure_upload(app, UPLOAD_FOLDER_ROOT, use_upload_id=False)
#-----------Layout----------------#
header= dbc.Navbar(
    dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        html.Img(
                            id="logo",
                            src='assets/mlex.png',
                            height="60px",
                        ),
                        md="auto",
                    ),
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.H3("MLExchange | Search"),
                                ],
                                id="app-title",
                            )
                        ],
                        md=True,
                        align="center",
                    ),
                ],
                align="center",
            ),
        ],
        fluid=True,
    ),
    dark=True,
    color="dark",
    sticky="top",
)

content_meta = ["name", "version", "type", "uri", "reference", "description", "content_type", "content_id", "owner"]

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
                row_selectable='single',
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

file_manager = html.Div([
    dbc.Card([
        dbc.CardBody(id='data-body',
                      children=[
                              
    du.Upload(
        id="dash-uploader",
        max_file_size=1800,  # 1800 Mb
        cancel_button=True,
        pause_button=True,
        # style = {
        #     'width': '95%',
        #     'height': '60px',
        #     'lineHeight': '60px',
        #     'borderWidth': '1px',
        #     'borderStyle': 'dashed',
        #     'borderRadius': '5px',
        #     'textAlign': 'center',
        #     'margin': '25px'},
        ),
        #     dcc.Upload(
        #         id = 'upload-image',
        #         children = html.Div([
        #             'Drag and Drop or ',
        #             html.A('Select Files')]),
        #         style = {
        #             'width': '95%',
        #             'height': '60px',
        #             'lineHeight': '60px',
        #             'borderWidth': '1px',
        #             'borderStyle': 'dashed',
        #             'borderRadius': '5px',
        #             'textAlign': 'center',
        #             'margin': '25px'},
        # # Allow multiple files to be uploaded
        #         multiple = True),
    dbc.Label('Choose files/directories:'),
    html.Div(
                [dbc.Button("Browse",
                            id="browse-dir",
                            className="ms-auto",
                            color="secondary",
                            outline=True,
                            n_clicks=0,
                            style={'width': '15%', 'margin': '5px'}),
                html.Div([
                    dcc.Dropdown(
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
                            value='*')
                        ],
                        style={"width": "15%", 'margin-right': '60px'}
                ),
                dbc.Button("Delete the Selected",
                            id="delete-files",
                            className="ms-auto",
                            color="danger",
                            outline=True,
                            n_clicks=0,
                            style={'width': '22%', 'margin-right': '10px'}
                ),
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle("Warning")),
                        dbc.ModalBody("Files cannot be recovered after deletion. Do you still want to proceed?"),
                        dbc.ModalFooter([
                            dbc.Button(
                                "Delete", id="confirm-delete", color='danger', outline=False, 
                                className="ms-auto", n_clicks=0
                            ),
                        ]),
                    ],
                    id="modal",
                    is_open=False,
                    style = {'color': 'red'}
                ), 
                dbc.Button("Import",
                            id="import-dir",
                            className="ms-auto",
                            color="secondary",
                            outline=True,
                            n_clicks=0,
                            style={'width': '22%', 'margin': '5px'}
                ),
                html.Div([
                    dcc.Dropdown(
                            id='import-format',
                            options=[
                                {'label': 'all files (*)', 'value': '*'},
                                {'label': '.png', 'value': '*.png'},
                                {'label': '.jpg/jpeg', 'value': '*.jpg,*.jpeg'},
                                {'label': '.tif/tiff', 'value': '*.tif,*.tiff'},
                                {'label': '.txt', 'value': '*.txt'},
                                {'label': '.csv', 'value': '*.csv'},
                            ],
                            value='*')
                        ],
                        style={"width": "15%"}
                ),
                ],
            style = {'width': '100%', 'display': 'flex', 'align-items': 'center'},
        ),
    html.Div([ html.Div([dbc.Label('Show Local/Docker Path')], style = {'margin-right': '10px'}),
                daq.ToggleSwitch(
                    id='my-toggle-switch',
                    value=False
                )],
        style = {'width': '100%', 'display': 'flex', 'align-items': 'center', 'margin': '10px', 'margin-left': '0px'},
    ),
    file_paths_table,
                      ])
        ])

    ]),

file_explorer = html.Div(
    [
        dbc.Button(
            "Open File Manager",
            id="collapse-button",
            size="lg",
            className="mb-3",
            color="secondary",
            outline=True,
            n_clicks=0,
        ),
        dbc.Collapse(
            file_manager,
            id="collapse",
            is_open=False,
        ),
    ]
)

browser_cache =html.Div(
        id="no-display",
        children=[
            dcc.Store(id='file-paths', data=[]),
            dcc.Store(id='current-page', data=0),
            dcc.Store(id='image-order', data=[]),
            dcc.Store(id='counter', data=0),
            dcc.Store(id='dummy-data', data=0)
        ],
    )

def parse_images(img):
    # Convert the image string to numpy array and create a
    # Plotly figure, see https://plotly.com/python/imshow/
    fig = px.imshow(img)

    # Hide the axes and the tooltips
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(t=20, b=0, l=0, r=0),
        xaxis=dict(
            showgrid=False,
            showticklabels=False,
            linewidth=0
        ),
        yaxis=dict(
            showgrid=False,
            showticklabels=False,
            linewidth=0
        ),
        hovermode=False
    )
    return fig

def blank_fig():
    fig = go.Figure(go.Scatter(x=[], y = []))
    fig.update_layout(template = None)
    fig.update_xaxes(showgrid = False, showticklabels = False, zeroline=False)
    fig.update_yaxes(showgrid = False, showticklabels = False, zeroline=False)
    return fig

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
            dbc.Col(dcc.Graph(id='raw-image-results', figure = blank_fig())),
            dbc.Col(dcc.Graph(id='image-search-results', figure = blank_fig())),
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
                interval=1000, # milliseconds
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

#-----------Callback---------------#
@app.callback(
    Output('text-output', 'data'),
    Output('text-output', 'columns'),
    Input('text-search-button', 'n_clicks'),
    State('text-input', 'value')
)
def text_search(n_clicks, input):
    url = f'http://search-api:8060/api/v0/search/document/?keyword={input}'
    resp = requests.get(url).json()
    infos=[]
    keys =[]
    i = 0
    for info in resp:
        info_dict = {}

        for key, value in info['_d_'].items():
            info_dict[key] = str(value)
            if i == 0:
                keys.append({'id': key, 'name': key})
        i += 1    
        infos.append(info_dict)
    return infos, keys

@app.callback(
    Output('counter', 'data'),
    Input('image-search-button', 'n_clicks'),
    State('category', 'value'),
    State('cnn', 'value'),
    State('searching-method', 'value'),
    State('number-of-images', 'value'),
    State('counter', 'data'),
    prevent_initial_call = True
)
def image_search(n_clicks, category, cnn, searching_method, number_of_images, counts):

    # initializes the counter according to the latest deploy job in the database
    counts = helper_utils.init_counters(USER, 'deploy')

    database_dir = f'data/database/{category}/'
    query_dir = 'data/query/'
    output_dir = 'data/output/'
    experiment_id = str(uuid.uuid4())  # create unique id for experiment
    search_id = f'deploy_{counts}_' + experiment_id
    pre_trained_cnn = f'data/cnn/{cnn}.h5'

    paras = {
        "feature_extraction_method": cnn, 
        "searching_method": searching_method, 
        "number_of_images": number_of_images
        }

    job_request = {
        'user_uid': USER,
        'host_list': ['mlsandbox.als.lbl.gov', 'local.als.lbl.gov', 'vaughan.als.lbl.gov'],
        'requirements': {
            'num_processors': 2, # number of cpus, up to 10
            'num_gpus': 0, # number of gpus, up to 2 in vaughan
            'num_nodes': 1 # how many workers needed, suggested to keep as 1
            },
        'job_list': [{
            'mlex_app': 'mlex_search',
            'service_type': 'backend',
            'working_directory': LOCAL_DATA,
            'job_kwargs': {
                'uri': 'mlexchange/pycbir', 
                'cmd': f'python3 src/pycbir_cl.py {database_dir} {query_dir} {output_dir} {search_id} {pre_trained_cnn} ' + '\'' + json.dumps(paras) + '\'',
                'kwargs': {
                    'job_id': search_id,
                    'job_type': f'deploy {counts}',
                    'database': category,
                    'cnn': paras['feature_extraction_method'],
                    'searching_method': paras['searching_method'],
                    'number_of_images': paras['number_of_images'],
                }
                }
            }],
            'dependencies': {'0': []}
        }

    resp = requests.post('http://job-service:8080/api/v0/workflows', json = job_request)
    counts += 1
    return counts

@app.callback(
    Output('job-table', 'data'),
    Input('job-refresher', 'n_intervals'),
)
def status_check(n):
    url = f'http://job-service:8080/api/v0/jobs?&user={USER}&mlex_app=mlex_search'
    # check the status of the job and show in the list
    list_of_jobs = requests.get(url).json()
    print(list_of_jobs, '------------')
    data_table = []
    for job in list_of_jobs:
        data_table.insert(0, dict(job_id = job['job_kwargs']['kwargs']['job_id'],
                                  job_type = job['job_kwargs']['kwargs']['job_type'],
                                  status = job['status']['state'],
                                  database = job['job_kwargs']['kwargs']['database'],
                                  cnn = job['job_kwargs']['kwargs']['cnn'],
                                  searching_method = job['job_kwargs']['kwargs']['searching_method'],
                                  number_of_images = job['job_kwargs']['kwargs']['number_of_images'],
                                  job_logs = job['logs'])
        )
    return data_table

@app.callback(
    Output('job-logs', 'value'),
    Input('job-refresher', 'n_intervals'),
    State('job-table', 'selected_rows'),
    State('job-table', 'data')
)
def log_display(n, row, data):
    log = ''
    if row:
        log = data[row[0]]['job_logs']
    return log

@app.callback(
    Output('image-search-results', 'figure'),
    Input('job-refresher', 'n_intervals'),
    State('job-table', 'selected_rows'),
    State('job-table', 'data'),
    prevent_initial_call = True
)
def image_display(n, row, data):
    if (not row) or (data[row[0]]['status'] != 'complete'):
        raise PreventUpdate

    else:
        search_id = data[row[0]]['job_id']
        database = data[row[0]]['database']
        cnn = data[row[0]]['cnn']
        number_of_images = data[row[0]]['number_of_images']
        searching_method = data[row[0]]['searching_method']
        img_path = f'../../data/output/{search_id}/result_{database}_{cnn}_ed_{number_of_images}_searching_method_{searching_method}.png'
        img = np.array(imageio.imread(img_path))
        img = parse_images(img)

        return img

#---File Manager Related Callbacks---#
@app.callback(
    Output("collapse", "is_open"),
    Input("collapse-button", "n_clicks"),
    State("collapse", "is_open")
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    Output("modal", "is_open"),
    Input("delete-files", "n_clicks"),
    Input("confirm-delete", "n_clicks"),  
    State("modal", "is_open")
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app.callback(
    Output('dummy-data', 'data'),
    [Input('dash-uploader', 'isCompleted')],
    [State('dash-uploader', 'fileNames'),
     State('dash-uploader', 'upload_id')],
)
def upload_zip(iscompleted, upload_filename, upload_id):
    if not iscompleted:
        return 0

    if upload_filename is not None:
        path_to_zip_file = pathlib.Path(UPLOAD_FOLDER_ROOT) / upload_filename[0]
        if upload_filename[0].split('.')[-1] == 'zip':   # unzip files and delete zip file
            zip_ref = zipfile.ZipFile(path_to_zip_file)  # create zipfile object
            path_to_folder = pathlib.Path(UPLOAD_FOLDER_ROOT) / upload_filename[0].split('.')[-2]
            if (upload_filename[0].split('.')[-2] + '/') in zip_ref.namelist():
                zip_ref.extractall(pathlib.Path(UPLOAD_FOLDER_ROOT))    # extract file to dir
            else:
                zip_ref.extractall(path_to_folder)

            zip_ref.close()  # close file
            os.remove(path_to_zip_file)

    return 0 

@app.callback(
    Output('files-table', 'data'),
    Output('file-paths', 'data'),
    Input('browse-format', 'value'),
    Input('browse-dir', 'n_clicks'),
    Input('import-dir', 'n_clicks'),
    Input('confirm-delete','n_clicks'),
    Input('files-table', 'selected_rows'),
    Input('file-paths', 'data'),
    Input('my-toggle-switch', 'value'),
)
def file_manager(browse_format, browse_n_clicks, import_n_clicks, delete_n_clicks, 
                rows, selected_paths, docker_path):
    changed_id = dash.callback_context.triggered[0]['prop_id']
    files = []
    if browse_n_clicks or import_n_clicks:
        files = filename_list(UPLOAD_FOLDER_ROOT, browse_format)
        
    selected_files = []
    if bool(rows):
        for row in rows:
            selected_files.append(files[row])
    
    if browse_n_clicks and changed_id == 'confirm-delete.n_clicks':
        for filepath in selected_files:
            if os.path.isdir(filepath['file_path']):
               shutil.rmtree(filepath['file_path'])
            else:
                os.remove(filepath['file_path'])
        selected_files = []
        files = filename_list(UPLOAD_FOLDER_ROOT, browse_format)

    if docker_path:
        return files, selected_files
    else:
        return docker_to_local_path(files, DOCKER_HOME, LOCAL_HOME), selected_files

@app.callback(
    Output('raw-image-results', 'figure'),
    Input('files-table', 'selected_rows'),
    Input('file-paths', 'data'),
)
def display_raw_image(row, selected_files):
    if not row:
        raise PreventUpdate
    
    else:
        if bool(selected_files):
        
            if selected_files[0]['file_type'] == 'file':
                img_path = selected_files[0]['file_path']
                img = np.array(imageio.imread(img_path))
                img = parse_images(img)
                return img
            else:
                raise PreventUpdate
        else:
            raise PreventUpdate
# Maybe do clear out rather than prevent


if __name__ == '__main__':
    app.run_server(host = '0.0.0.0', port = 8061, debug=True)