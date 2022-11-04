from app_layout import app, USER, \
                       LOCAL_DATA, UPLOAD_FOLDER_ROOT, DOCKER_DATA, DOCKER_HOME, LOCAL_HOME, \
                       NUMBER_OF_ROWS, NUMBER_IMAGES_PER_ROW
import base64
import dash
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from file_manager import filename_list, move_a_file, move_dir, docker_to_local_path, \
                         add_paths_from_dir
from helper_utils import init_counters, parse_images
import imageio
import json
import math
import numpy as np
import os
import pathlib
import requests
import shutil
import uuid
import zipfile

#-------------------Callbacks----------------------------#
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
    counts = init_counters(USER, 'deploy')

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
    Input('import-dir', 'n_clicks'),

    State("collapse", "is_open")
)
def toggle_collapse(n, import_n_clicks, is_open):
    if n or import_n_clicks:
        return not is_open
    return is_open


@app.callback(
    Output("file-mover-collapse", "is_open"),
    Input("file-mover-button", "n_clicks"),
    State("file-mover-collapse", "is_open")
)
def file_mover_collapse(n, is_open):
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
    Output('docker-file-paths', 'data'),

    Input('clear-data', 'n_clicks'),
    Input('browse-format', 'value'),
    Input('import-dir', 'n_clicks'),
    Input('confirm-delete','n_clicks'),
    Input('move-dir', 'n_clicks'),
    Input('docker-file-paths', 'data'),
    Input('my-toggle-switch', 'value'),
    Input('dummy-data', 'data'),
    Input('files-table', 'selected_rows'),

    State('dest-dir-name', 'value'),
)
def load_dataset(clear_data, browse_format, import_n_clicks, delete_n_clicks, 
                move_dir_n_clicks, selected_paths, docker_path, uploaded_data, rows, dest):
    '''
    This callback displays manages the actions of file manager
    Args:
        clear_data:         Clear loaded images
        browse_format:      File extension to browse
        import_n_clicks:    Import button
        delete_n_clicks:    Delete button
        move_dir_n_clicks:  Move button
        selected_paths:     Selected paths in cache
        docker_path:        [bool] docker vs local path
        dest:               Destination path
        rows:               Selected rows
    Returns
        files:              Filenames to be displayed in File Manager according to browse_format from docker/local path
        selected_files:     List of selected filename FROM DOCKER PATH (no subdirectories)
    '''
    changed_id = dash.callback_context.triggered[0]['prop_id']
    files = filename_list(DOCKER_DATA, browse_format, sort=True)
        
    selected_files = []
    if bool(rows):
        for row in rows:
            selected_files.append(files[row])
    
    if changed_id == 'confirm-delete.n_clicks':
        for filepath in selected_files:
            if os.path.isdir(filepath['file_path']):
               shutil.rmtree(filepath['file_path'])
            else:
                os.remove(filepath['file_path'])
        selected_files = []
        files = filename_list(DOCKER_DATA, browse_format, sort=True)
    
    if changed_id == 'move-dir.n_clicks':
        if dest is None:
            dest = ''
        destination = DOCKER_DATA / dest
        destination.mkdir(parents=True, exist_ok=True)
        if bool(rows):
            sources = selected_paths
            print(f'sources {sources}')
            for source in sources:
                if os.path.isdir(source['file_path']):
                    move_dir(source['file_path'], str(destination))
                    shutil.rmtree(source['file_path'])
                else:
                    move_a_file(source['file_path'], str(destination))

            selected_files = []
            files = filename_list(DOCKER_DATA, browse_format)
    
    if changed_id == 'clear-data.n_clicks':
        selected_files = []

    # do not update 'docker-file-paths' when only toggle docker path 
    if selected_files == selected_paths:
        selected_files = dash.no_update

    if docker_path:
        return files, selected_files
    else:
        return docker_to_local_path(files, DOCKER_HOME, LOCAL_HOME), selected_files

@app.callback(
    Output('image-order','data'),
    Input('docker-file-paths','data'),
    Input('import-dir', 'n_clicks'),
    Input('import-format', 'value'),
    Input('files-table', 'selected_rows'),
    Input('confirm-delete','n_clicks'),
    Input('move-dir', 'n_clicks'),
    State('image-order','data'),
    prevent_initial_call=True)
def display_index(file_paths, import_n_clicks, import_format, rows,
                  delete_n_clicks, move_dir_n_clicks, image_order):
    '''
    This callback arranges the image order according to the following actions:
        - New content is uploaded
        - Buttons sort or hidden are selected
    Args:
        file_paths :            Absolute file paths selected from path table
        import_n_clicks:        Button for importing selected paths
        import_format:          File format for import
        rows:                   Rows of the selected file paths from path table
        delete_n_clicks:        Button for deleting selected file paths
        image_order:            Order of the images according to the selected action (sort, hide, new data, etc)

    Returns:
        image_order:            Order of the images according to the selected action (sort, hide, new data, etc)
        data_access_open:       Closes the reactive component to select the data access (upload vs. directory)
    '''
    supported_formats = []
    import_format = import_format.split(',')
    if import_format[0] == '*':
        supported_formats = ['tiff', 'tif', 'jpg', 'jpeg', 'png']
    else:
        for ext in import_format:
            supported_formats.append(ext.split('.')[1])

    changed_id = dash.callback_context.triggered[0]['prop_id']
    if import_n_clicks and bool(rows):
        list_filename = []
        if bool(file_paths):
            for file_path in file_paths:
                if file_path['file_type'] == 'dir':
                    list_filename = add_paths_from_dir(file_path['file_path'], supported_formats, list_filename)
                else:
                    list_filename.append(file_path['file_path'])
        else:
            image_order = []
    
        num_imgs = len(list_filename)
        if  changed_id == 'import-dir.n_clicks' or \
            changed_id == 'confirm-delete.n_clicks' or \
            changed_id == 'files-table.selected_rows' or \
            changed_id == 'move_dir_n_clicks':
            image_order = list(range(num_imgs))
            
    else:
        image_order = []

    
    print(f'file paths 0 {file_paths}')
    print(f'image order 0 {image_order}')
    return image_order


@app.callback([
    Output('output-image-upload', 'children'),
    Output('prev-page', 'disabled'),
    Output('next-page', 'disabled'),
    Output('current-page', 'data'),

    Input('image-order', 'data'),
    Input('prev-page', 'n_clicks'),
    Input('next-page', 'n_clicks'),
    Input('files-table', 'selected_rows'),
    Input('import-format', 'value'),
    Input('docker-file-paths','data'),
    Input('my-toggle-switch', 'value'),

    State('current-page', 'data'),
    State('import-dir', 'n_clicks')],
    prevent_initial_call=True)
def update_output(image_order, button_prev_page, button_next_page, rows, import_format,
                  file_paths, docker_path, current_page, import_n_clicks):
    '''
    This callback displays images in the front-end
    Args:
        image_order:            Order of the images according to the selected action (sort, hide, new data, etc)
        button_prev_page:       Go to previous page
        button_next_page:       Go to next page
        rows:                   Rows of the selected file paths from path table
        import_format:          File format for import
        file_paths:             Absolute file paths selected from path table
        docker_path:            Showing file path in Docker environment
        current_page:           Index of the current page
        import_n_clicks:        Button for importing the selected paths
    Returns:
        children:               Images to be displayed in front-end according to the current page index and # of columns
        prev_page:              Enable/Disable previous page button if current_page==0
        next_page:              Enable/Disable next page button if current_page==max_page
        current_page:           Update current page index if previous or next page buttons were selected
    '''
    supported_formats = []
    import_format = import_format.split(',')
    if import_format[0] == '*':
        supported_formats = ['tiff', 'tif', 'jpg', 'jpeg', 'png']
    else:
        for ext in import_format:
            supported_formats.append(ext.split('.')[1])
    
    changed_id = dash.callback_context.triggered[0]['prop_id']
    # update current page if necessary
    if changed_id == 'image-order.data':
        current_page = 0
    if changed_id == 'prev-page.n_clicks':
        current_page = current_page - 1
    if changed_id == 'next-page.n_clicks':
        current_page = current_page + 1

    children = []
    num_imgs = 0
    if import_n_clicks and bool(rows):
        list_filename = []
        for file_path in file_paths:
            if file_path['file_type'] == 'dir':
                list_filename = add_paths_from_dir(file_path['file_path'], supported_formats, list_filename)
            else:
                list_filename.append(file_path['file_path'])
    
        # plot images according to current page index and number of columns
        num_imgs = len(image_order)
        if num_imgs>0:
            start_indx = NUMBER_OF_ROWS * NUMBER_IMAGES_PER_ROW * current_page
            max_indx = min(start_indx + NUMBER_OF_ROWS * NUMBER_IMAGES_PER_ROW, num_imgs)
            new_contents = []
            new_filenames = []
            for i in range(start_indx, max_indx):
                filename = list_filename[image_order[i]]
                with open(filename, "rb") as file:
                    img = base64.b64encode(file.read())
                    file_ext = filename[filename.find('.')+1:]
                    new_contents.append('data:image/'+file_ext+';base64,'+img.decode("utf-8"))
                if docker_path:
                    new_filenames.append(list_filename[image_order[i]])
                else:
                    new_filenames.append(docker_to_local_path(list_filename[image_order[i]], DOCKER_HOME, LOCAL_HOME, 'str'))
                
            children = helper_utils.draw_rows(new_contents, new_filenames, NUMBER_IMAGES_PER_ROW, NUMBER_OF_ROWS)

    return children, current_page==0, math.ceil((num_imgs//NUMBER_IMAGES_PER_ROW)/NUMBER_OF_ROWS)<=current_page+1, \
           current_page


if __name__ == '__main__':
    app.run_server(host = '0.0.0.0', port = 8061, debug=True)