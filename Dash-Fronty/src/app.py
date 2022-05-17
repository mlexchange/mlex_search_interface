from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from dash import dash_table
from dash.exceptions import PreventUpdate
import imageio
import numpy as np
import plotly.express as px
import requests
import json
import datetime
import os



#------------App Setup------------#
external_stylesheets = [dbc.themes.BOOTSTRAP, "assets/segmentation-style.css"]

app = Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)

#------------Global Variable-------------#
USER = 'Dummy-Searcher' 
DATA_DIR = str(os.environ['DATA_DIR'])
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
                    id = 'dataset',
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
        html.Div([
            dbc.Label("Upload Image Here: "),
            dcc.Upload(
                id = 'upload-image',
                children = html.Div([
                    'Drag and Drop or ',
                    html.A('Select Files')]),
                style = {
                    'width': '95%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '25px'},
        # Allow multiple files to be uploaded
                multiple = True),
        ]),
        html.Div(dcc.Graph(id='image-search-results',)),
        html.Div(id = 'selection')
])

def parse_contents(contents, filename, date):
    return html.Div([
        html.H5(filename),
        html.H6(datetime.datetime.fromtimestamp(date)),

        # HTML images accept base64 encoded strings in the same format
        # that is supplied by the upload
        html.Img(src = contents, style = {'width':'60%', 'margin': '25px'}),
        html.Hr(),
    ])

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

job_status_display = [
    html.Div(
        children=[
            dash_table.DataTable(
                id='job-table',
                columns=[
                    {'name': 'Job ID', 'id': 'job_id'},
                    {'name': 'Status', 'id': 'status'},
                    {'name': 'Submission Time', 'id': 'submission_time'},
                    {'name': 'Execution Time', 'id': 'execution_time'},
                    {'name': 'End Time', 'id': 'end_time'},
                    # {'name': 'Logs', 'id': 'job_logs'}
                ],
                data = [],
                row_selectable='single',
                style_cell={'padding': '1rem', 'textAlign': 'left'},
                fixed_rows={'headers': True},
                css=[{"selector": ".show-hide", "rule": "display: none"}],
                style_data_conditional=[
                    {'if': {'column_id': 'status', 'filter_query': '{status} = complete'},
                     'backgroundColor': 'green',
                     'color': 'white'},
                    {'if': {'column_id': 'status', 'filter_query': '{status} = failed'},
                     'backgroundColor': 'red',
                     'color': 'white'}
                ],
                style_table={'height':'18rem', 'overflowY': 'auto'}
            ),
            dcc.Interval(
                id='job-refresher',
                interval=1*2000, # milliseconds
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
        dbc.Row([html.H1("What do you want to search?")]),
        dbc.Row((text_search_card)),
        dbc.Row((image_search_card)),
        dbc.Row((job_display)),
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
    url = f'http://fastapi:8060/search/{input}'
    resp = requests.get(url).json()
    infos=[]
    keys =[]
    i = 0
    for info in resp[1]:
        info_dict = {}

        for key, value in info['_d_'].items():
            info_dict[key] = str(value)
            if i == 0:
                keys.append({'id': key, 'name': key})
        i += 1    
        infos.append(info_dict)
    return infos,keys

@app.callback(
    Output('output-image-upload', 'children'),
    Input('upload-image', 'contents'),
    State('upload-image', 'filename'),
    State('upload-image', 'last_modified')
)
def display_image(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children

@app.callback(
    Output('selection', 'children'),
    Input('image-search-button', 'n_clicks'),
    State('dataset', 'value'),
    State('cnn', 'value'),
    State('searching-method', 'value'),
    State('number-of-images', 'value'),
    prevent_intial_call = True
)
def image_search(n_clicks, dataset, cnn, searching_method, number_of_images):
    
    if n_clicks > 0:
        selection = [dataset, cnn, searching_method, number_of_images]

        paras = {
            "feature_extraction_method": cnn, 
            "searching_method": searching_method, 
            "number_of_images": number_of_images
            }

        job_request = {
            'user_uid': USER,
            'host_list': ['mlsandbox.als.lbl.gov', 'local.als.lbl.gov', 'vaughan.als.lbl.gov'],
            'requirements': {
                'num_processors': 2,
                'num_gpus': 0,
                'num_nodes': 1
                },
            'job_list': [{
                'mlex_app': 'mlex_search',
                'service_type': 'backend',
                'working_directory': DATA_DIR,
                # 'working_directory': '/Users/tibbers/MLExchange/mlex_pyCBIR/data',
                # 'working_directory': '/Users/tibbers/mlexchange/mlex_pyCBIR/data',
                'job_kwargs': {
                    'uri': 'mlexchange/pycbir', 
                    'cmd': f'python3 src/model.py data/{dataset}/database/ data/{dataset}/query/ data/{dataset}/output/ ' + '\'' + json.dumps(paras) + '\'',
                    # 'cmd': 'sleep 600',
                    # 'kwargs': {'parameters': ParaPlaceholder}
                    }
                }],
                'dependencies': {'0': []}
            }

        resp = requests.post('http://job-service:8080/api/v0/workflows', json = job_request)

        return f'Chosen parameters: {selection}; Status code: {resp.status_code}'

@app.callback(
    Output('job-table', 'data'),
    Input('job-refresher', 'n_intervals'),
)
def status_check(n):
    url = f'http://job-service:8080/api/v0/jobs?&user={USER}&mlex_app=mlex_search'
    # check the status of the job and show in the list
    list_of_jobs = requests.get(url).json()
    data_table = []
    for job in list_of_jobs:
        data_table.insert(0, dict(job_id=job['uid'],
                                  submission_time = job['timestamps']['submission_time'],
                                  execution_time = job['timestamps']['execution_time'],
                                  end_time = job['timestamps']['end_time'],
                                  status=job['status']['state'],
                                  job_logs=job['logs'])
        )
    return data_table

@app.callback(
    Output('job-logs', 'value'),
    Input('job-table', 'selected_rows'),
    State('job-table', 'data'),
)
def log_display(row, data):
    log = ''
    if row:
        log = data[row[0]]['job_logs']
    return log

@app.callback(
    Output('image-search-results', 'figure'),
    Input('job-table', 'selected_rows'),
    State('job-table', 'data'),
    State('dataset', 'value'),
    State('cnn', 'value'),
    State('searching-method', 'value'),
    State('number-of-images', 'value'),
    prevent_intial_call = True
)
def image_display(row, data, dataset, cnn, searching_method, number_of_images):
    if not row:
        raise PreventUpdate

    else:
        img_path = f'../../data/{dataset}/output/result_{cnn}_ed_{number_of_images}_searching_method_{searching_method}.png'
        img = np.array(imageio.imread(img_path))
        img = parse_images(img)

        return img

if __name__ == '__main__':
    app.run_server(host = '0.0.0.0', port = 8061, debug=True)