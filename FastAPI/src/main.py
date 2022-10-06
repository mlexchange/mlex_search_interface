from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from elasticsearch import Elasticsearch, exceptions
from elasticsearch_dsl import Search, Index, Document
from ssl import create_default_context
import json
import requests

#----------Elastic Authentication----------#
cert = create_default_context(cafile = '/app/fastapi/src/certs/ca/ca.crt')
es = Elasticsearch('https://es01:9200',
                    http_auth=('elastic','elastic'),
                    ssl_context=cert)

#----------Global Varibles----------#
API_URL_PREFIX = '/api/v0'
KEYS = ["name", "version", "type", "uri", "application", "reference", "description", "content_type", "content_id", "owner"]
#----------Classes----------#
class NewIndex(BaseModel):
    index: str

class NewDocument(BaseModel):
    name: str
    version: str
    type: str
    uri: str
    application: list
    reference: str
    description: str
    content_type: str
    content_id: str
    owner: str

#----------Fast API Setup----------#
app = FastAPI(  openapi_url ="/api/lbl-mlexchange/openapi.json",
                docs_url    ="/api/lbl-mlexchange/docs",
                redoc_url   ="/api/lbl-mlexchange/redoc",
             )

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
# This part has already been added in content registry
# @app.post(API_URL_PREFIX + '/receiver', status_code=201, tags = ['Webhook'])
# def webhook_receiver(msg: dict):
#     content_id = msg['content_id']
#     content_type = msg['content_type']
#     params = {
#         'index': content_type,
#         'doc_id': content_id}
#     if msg['event'] == 'add_content':
#         content = requests.get(f'http://content-api:8000/api/v0/contents/{content_id}/content').json()
#         content_data = {}
#         for key, value in content.items():
#             if key in KEYS:
#                 content_data[key] = value
#         requests.post('http://search-api:8060/api/v0/index/document', params = params, json = content_data)
#     elif msg['event'] == 'delete_content':
#         requests.delete(f'http://search-api:8060/api/v0/index/{content_type}/document/{content_id}')


@app.post(API_URL_PREFIX + '/index', status_code=201, tags = ['Index'])
def create_index(req: NewIndex):
    '''
    Create a new index for elasticsearch.

    Args:
        req: the name of index waiting for creation. (from request body)

    Return:
        if index being created successfully -> response body 
        if index already exists             -> 400 error
    '''
    try:
        resp = Index(req.index).create(using = es)
    except exceptions.RequestError as e:
        raise HTTPException(status_code = 400, detail = str(e))
    else:
        return resp
    
@app.post(API_URL_PREFIX + '/index/document', status_code=201, tags = ['Document'])
def index_doc(index: str, doc_id: str, doc: NewDocument):
    '''
    Insert a document to the index.

    Args:
        index: category of the document
        doc_id: id of the document
        doc: document content to be ingested

    Return:
        response body, creat/update will be indicated
    '''
    resp = es.index(index = index, id = doc_id, document = dict(doc))
    return resp

#----------PUT----------#


#----------DELETE----------#
@app.delete(API_URL_PREFIX + '/index/{index}', status_code=204, tags = ['Index'])
def delete_index(index: str):
    '''
    Delete an index.

    Args:
        index: the name of index to be deleted

    Return:
        if index being deleted successfully -> response body 
        if index does not exist             -> 404 error
    '''
    try:
        resp = Index(index).delete(using = es)
    except exceptions.NotFoundError as e:
        raise HTTPException(status_code = 404, detail = str(e))
    else:
        return resp

@app.delete(API_URL_PREFIX + '/index/{index}/document/{doc_id}', status_code = 200, tags = ['Document'])
def delete_doc(index: str, doc_id: str):
    '''
    Delete the document within the index.

    Args:
        index: the index where document resides
        doc_id: the id of document to be deleted

    Return:
        if document being deleted successfully -> HTTP 204 Status Code
        if document id or index does not exist -> 404 error
    '''
    try:
        resp = Document().delete(using = es, index = index, id = doc_id)
    except exceptions.NotFoundError as e:
        raise HTTPException(status_code = 404, detail = str(e))
    return print(f'Successfully deleted content_id: {doc_id} within "{index}" category')