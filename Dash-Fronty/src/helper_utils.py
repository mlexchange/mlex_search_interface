import requests
from dash import html
import dash_bootstrap_components as dbc
import plotly.express as px



def get_job(user, mlex_app):
    url = 'http://job-service:8080/api/v0/jobs?'
    if user:
        url += ('&user=' + user)
    if mlex_app:
        url += ('&mlex_app=' + mlex_app)
    
    response = requests.get(url).json()
    return response

def init_counters(user, job_type):
    job_list = get_job(user, 'mlex_search')
    if job_list is not None:
        for job in reversed(job_list):
            last_job = job['job_kwargs']['kwargs']['job_type'].split()
            value = int(last_job[-1])
            last_job = ' '.join(last_job[0:-1])
            if last_job == job_type:
                return value + 1
    return 0

def parse_contents(contents, filename, index):
    '''
    This function creates the reactive components to display 1 image with it's thumbnail card
    Args:
        contents:   Image contents
        filename:   Filename
        index:      Index of the reactive component
    Returns:
        reactive_component
    '''
    img_card = html.Div(
        dbc.Card(
            id={'type': 'thumbnail-card', 'index': index},
            children=[
                html.A(id={'type': 'thumbnail-image', 'index': index},
                       children=dbc.CardImg(id={'type': 'thumbnail-src', 'index': index},
                                            src=contents,
                                            bottom=False)),
                dbc.CardBody([
                    html.P(id={'type':'thumbnail-name', 'index': index}, children=filename)
                ])
            ],
            outline=False,
            color='white'
        ),
        id={'type': 'thumbnail-wrapper', 'index': index},
        style={'display': 'block'}
    )
    return img_card


def draw_rows(list_of_contents, list_of_names, n_cols, n_rows):
    '''
    This function display the images per page
    Args:
        list_of_contents:   List of contents
        list_of_names:      List of filenames
        n_cols:             Number of columns
        n_rows:             Number of rows
    Returns:
        reactivate component with all the images
    '''
    n_images = len(list_of_contents)
    n_cols = n_cols
    children = []
    visible = []
    for j in range(n_rows):
        row_child = []
        for i in range(n_cols):
            index = j * n_cols + i
            if index >= n_images:
                # no more images, on hanging row
                break
            content = list_of_contents[index]
            name = list_of_names[index]
            row_child.append(dbc.Col(parse_contents(content,
                                                    name,
                                                    j * n_cols + i),
                                     width="{}".format(12 // n_cols),
                                     )
                             )
            visible.append(1)
        children.append(dbc.Row(row_child))
    return children
