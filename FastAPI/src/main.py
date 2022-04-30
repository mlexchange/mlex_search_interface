from logging import RootLogger
from fastapi import FastAPI, Path, Query, HTTPException, status
from typing import Optional
from pydantic import BaseModel
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Index, Document, UpdateByQuery
from datetime import datetime
import json


es = Elasticsearch('http://elasticsearch:9200')

app = FastAPI()

# Core HTTP Methods:
# GET : ask app to get something and return it to you
# POST: send information to the endpoint and create something new
# PUT: update something already in the database
# DELETE: get rid of the information

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

@app.get('/search/{keyword}')
def search(keyword: str, description = 'Search keyword within database'):
    '''
    Search the doc information based on input name.
    To do: add sort for ordered display
    '''
    resp = Search().using(es).query("multi_match", query = keyword, fuzziness = "AUTO").extra(track_total_hits = True).execute()
    return 'Total %d hits found: ' % resp.hits.total.value, [info for info in resp]

@app.post('/create-index/{index}')
def create_index(index: str):
    '''
    Check if the index exists, if not, add the given index
    '''
    try:
        resp = Index(index).create(using = es)
        return [f'Index: \"{index}\" has been successfully created!', resp]

    except Exception as e:
        return f'Index: \"{index}\" already exists, please check.'

@app.post('/create-doc/{index}/{doc}')
def create_doc(index: str, doc: str, description = 'Warning, this needs to be redesigned, do not use atm'):
    '''
    Check if the doc exists within the given index, then add/update doc to the index.
    This needs to be redesigned. Do not use
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

@app.delete('/delete-doc/{index}/{keyword}')
def delete_doc(index: str, keyword: str):
    '''
    Delete document within specified index
    '''
    resp = Search().using(es).index(index).query('match', name = keyword).delete()
    return 'Document has been deleted.'

@app.delete('/delete-index/{index}')
def delete_index(index: str):
    '''
    Check if the index exists, if not, add the given index
    '''
    try:
        resp = Index(index).delete(using = es)
        return [f'Index: \"{index}\" has been successfully deleted!', resp]
    except Exception as e:
        return f'Index: \"{index}\" does not exist.'













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
