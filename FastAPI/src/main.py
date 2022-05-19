from fastapi import FastAPI
from pydantic import BaseModel
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Index, Document
from ssl import create_default_context

#----------Elastic Authentication----------#
cert = create_default_context(cafile = '/app/fastapi/src/certs/ca/ca.crt')
es = Elasticsearch('https://es01:9200',
                    http_auth=('elastic','elastic'),
                    ssl_context=cert)

#----------Global Varibles----------#
API_URL_PREFIX = '/search_api'

#----------Classes----------#
class NewIndex(BaseModel):
    index: str

class NewDocument(BaseModel):
    name: str
    version: str
    type: str
    uri: str
    application: str
    reference: str
    description: str
    content_type: str
    content_id: str
    owner: str

#----------Fast API Setup----------#
app = FastAPI(docs_url = "/search_api/docs")

# Core HTTP Methods:
# GET : ask app to get something and return it to you
# POST: send information to the endpoint and create something new
# PUT: update something already in the database
# DELETE: get rid of the information

#----------GET----------#
@app.get(API_URL_PREFIX + '/search/document/', tags = ['Keyword'])
def search(keyword: str) -> list: 
    '''
    Search the keyword within documents stored in elastic.

    Args:
        keyword: the keyword used to put into a search query
    Return:
        list of documents matching the search query, with order associated with ranking score.

    '''
    resp = Search().using(es).query("multi_match", query = keyword, fuzziness = "AUTO").extra(track_total_hits = True).execute()
    return list(resp)

#----------POST----------#
@app.post(API_URL_PREFIX + '/index/', tags = ['Index'])
def create_index(req: NewIndex):
    '''
    Create a new index for elasticsearch.

    Args:
        req: the name of index waiting for creation.

    Return:

    '''
    try:
        resp = Index(req.index).create(using = es)
        return [f'Index: \"{req.index}\" has been successfully created!', resp]

    except Exception as e:
        return f'Index: \"{req.index}\" already exists, please check.'

@app.post(API_URL_PREFIX + '/index/document', tags = ['Document'])
def index_doc(index: str, doc_id: str, doc: dict):
    '''
    Insert a document to the index.

    Args:

    Return:

    '''
    
    check_index = Index(index).exists(using = es)
    if not check_index:
        return f'Index: \"{index}\" does not exist, please check.'
    else:
        check_doc = Document().exists(using = es, index = index, id = doc['uid'])
        if check_doc:
            es.index(index = index, id = doc['uid'], document = doc)
            return 'UID: \"' + doc['uid'] + '\" has been updated.'
        else:
            es.index(index = index, id = doc['uid'], document = doc)
            return f'New document has been successfully inserted in \"{index}\".'

#----------PUT----------#


#----------DELETE----------#
@app.delete(API_URL_PREFIX + '/index/{index}', tags = ['Index'])
def delete_index(index: str):
    '''
    Delete an index.

    Args:

    Return:

    '''
    try:
        resp = Index(index).delete(using = es)
        return [f'Index: \"{index}\" has been successfully deleted!', resp]
    except Exception as e:
        return f'Index: \"{index}\" does not exist.'
    

@app.delete(API_URL_PREFIX + '/index/{index}/document/{doc_id}', tags = ['Document'])
def delete_doc(index: str, doc_id: str):
    '''
    Delete the document within the index.

    Args:

    Return:

    '''
    
    


# class Item(BaseModel):
#     name: str
#     affiliation: str
#     role: str
#     uid: str
#     #brand: Optional[str] = None

# class UpdateItem(BaseModel):
#     name: str
#     affiliation: Optional[str] = None
#     role: str
#     uid: Optional[str] = None

# @app.get('/get-by-name/{item_id}')
# def get_item(*, item_id: int, name: Optional[str] = None, test: int):
#     for item_id in inventory:
#         if inventory[item_id].name == name:
#             return inventory[item_id]
#         raise HTTPException(status_code=404, detail = 'Item name not found.')

# @app.post('/create-item/{item_id}')
# def create_item(item_id: int, item: Item):
#     if item_id in inventory:
#         return {'Error': 'Item ID already exists.'}

#     inventory[item_id] = item
#     #doc[id] = doc


#     return inventory[item_id]

# @app.put('/update-item/{item_id}')
# def update_item(item_id: int, item: UpdateItem):
#     if item_id not in inventory:
#         raise HTTPException(status_code=404, detail = 'Item name not found.')

#     if item.name != None:
#         inventory[item_id].name = item.name
#     if item.price != None:
#         inventory[item_id].price = item.price
#     if item.brand != None:
#         inventory[item_id].brand = item.brand

#     return inventory[item_id]

# @app.delete('/delete-item')
# def delete_item(item_id: int = Query(..., description = 'The ID of the item to delete')):
#     if item_id not in inventory:
#         return {'Error': 'ID does not exist'}
    
#     del inventory[item_id]
#     return {'Success': 'Item deleted!'}
