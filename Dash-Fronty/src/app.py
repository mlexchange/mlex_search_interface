from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from dash import dash_table
import requests
import json
import datetime


#------------App Setup------------#
external_stylesheets = [dbc.themes.BOOTSTRAP, "assets/segmentation-style.css"]

app = Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)


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

#params = ['name', 'affliation', 'role', 'uid']
params = ["name", "version", "type", "uri", "reference", "description", "content_type", "content_id", "owner"]

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
            columns = ([{'id': p, 'name': p} for p in params]),
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
                    ['Cells', 'Fibers', 'GISAXS'],
                    id = 'label',
                    placeholder = "Select Category",
                    )
                ),
            dbc.Col(
                dcc.Dropdown(
                    ['Inception_resnet', 'VGG16', 'Nasnet'],
                    id = 'cnn',
                    placeholder = "Select CNN",
                    )
                ),
            dbc.Col(
                dcc.Dropdown(
                    ['Brute Force (bf)', 'KDTree (kd)', 'BallTree (bt)'],
                    id = 'searching-method',
                    placeholder = "Select Searching Method",
                    )
                ),
            dbc.Col(
                dcc.Dropdown(
                    [num for num in range(1, 11)],
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
        html.Div(id = 'output-image-upload'),
        ]),
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

job_status_display = [
    html.Div(
        children=[
            dash_table.DataTable(
                id='job_table',
                columns=[
                    {'name': 'Job ID', 'id': 'job_id'},
                    {'name': 'Type', 'id': 'job_type'},
                    {'name': 'Status', 'id': 'status'},
                    {'name': 'Dataset', 'id': 'dataset'},
                    {'name': 'Image length', 'id': 'image_length'},
                    {'name': 'Model', 'id': 'model_name'},
                    {'name': 'Parameters', 'id': 'parameters'},
                    {'name': 'Experiment ID', 'id': 'experiment_id'},
                    {'name': 'Logs', 'id': 'job_logs'}
                ],
                data = [],
                hidden_columns = ['job_id', 'image_length', 'experiment_id', 'job_logs'],
                row_selectable='single',
                style_cell={'padding': '1rem', 'textAlign': 'left'}, #, 'maxWidth': '7rem', 'whiteSpace': 'normal'},
                fixed_rows={'headers': True},
                css=[{"selector": ".show-hide", "rule": "display: none"}],
                style_data_conditional=[
                    {'if': {'column_id': 'status', 'filter_query': '{status} = completed'},
                     'backgroundColor': 'green',
                     'color': 'white'},
                    {'if': {'column_id': 'status', 'filter_query': '{status} = failed'},
                     'backgroundColor': 'red',
                     'color': 'white'}
                ],
                style_table={'height':'18rem', 'overflowY': 'auto'}
            )
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
                width = True),
            dbc.Col(
                dbc.Card(
                    children = [
                        dbc.CardHeader("Job Logs"),
                        dbc.CardBody(
                            dcc.Textarea(id='job-logs',
                                 value='Placeholder for job logs',
                                 style={'width': '100%', 'height': '10rem'})
                        )
                    ],
                ),
                width = 3),    
        ],
        justify = "end"
        ),
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
    State('label', 'value'),
    State('cnn', 'value'),
    State('searching-method', 'value'),
    State('number-of-images', 'value')
)
def image_search(n_clicks, label, cnn, smtd, noi):
    selection = [label, cnn, smtd, noi]
    return f'Chosen parameters: {selection}'





if __name__ == '__main__':
    app.run_server(host = '0.0.0.0', port = 8061, debug=True)