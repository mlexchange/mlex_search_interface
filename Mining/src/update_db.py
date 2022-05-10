from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Index, Document, UpdateByQuery
import json
import urllib.request

es = Elasticsearch('https://es01:9200',
                    basic_auth=('elastic','elastic'))

#-----Define editing functions------#
def create_index(index: str):
    '''
    Check if the index exists, if not, add the given index
    '''
    try:
        resp = Index(index).create(using = es)
        return [f'Index: \"{index}\" has been successfully created!', resp]

    except Exception as e:
        return f'Index: \"{index}\" already exists, please check.'

def create_doc(index: str, id: str, doc: dict):
    '''
    Check if the doc exists within the given index, then add/update doc to the index.
    '''
    check_index = Index(index).exists(using = es)
    if not check_index:
        return f'Index: \"{index}\" does not exist, please check.'
    else:
        check_doc = Document().exists(using = es, index = index, id = id)
        if check_doc:
            es.index(index = index, id = id, document = doc)
            return 'UID: \"' + id + '\" has been updated.'
        else:
            es.index(index = index, id = id, document = doc)
            return f'New document has been successfully inserted in \"{index}\".'

#-----Content Registry API calls-----#
def content_list_GET_call(url):
    """
    Get the whole model registry data from the fastapi url.
    """
    response = urllib.request.urlopen(url)
    data = json.loads(response.read())
    return data

#-----Testing Database-----#
# with open('database.json') as json_file:
#     database = json.load(json_file)

# # Convert string to dict    
# database = json.loads(database)

# for key, values in database.items():
#     create_index(key)
#     for item in values:
#         create_doc(key, item['uid'], item)

#-----Content Registry-----#
keys = ["name", "version", "type", "uri", "application", "reference", "description", "content_type", "content_id", "owner"]
url_head = 'http://content-api:8000/api/v0/'
catagory = ['models', 'apps', 'workflows']

for item in catagory:
    url = url_head + item
    for model in content_list_GET_call(url):
        create_index(model['content_type'])
        content_data = {}
        for key, value in model.items():
            if key in keys:
                content_data[key] = value
        create_doc(content_data['content_type'], content_data['content_id'], content_data)        

for h in Search().using(es).scan():
    print(h)