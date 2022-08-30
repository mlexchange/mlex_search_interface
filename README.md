# MLExchange Search API

The Search API provides text and image searching tools for MLExchange platform. The purpose of this API is to help user nevigate through different apps and workflows within the platform, providing smooth user experience.

## Installation

Current version of the Search API has been dockerized. To use:

1. Install Docker and [[Docker Desktop]](https://www.docker.com/products/docker-desktop/) 

2. Navigate to the root directory of this repo

```bash
cd mlex_search_api
```

3. Build the container using docker-compose

```bash
docker-compose up --build
```

4. Wait until the process finish, you should see 6 containers under the 'mlex_search_api' container:

- Dash-Fronty (frontend)
- search-api (backend)
- Mining (initial data ingestion, this container will exit upon succesful execution)
- mlex_search_api_es01_1 (multinode search engine leveraged from elasticsearch)
- mlex_search_api_es02_1 (search engine node #2)
- mlex_search_api_es03_1 (search engine node #3)
- mlex_search_api_kibana_1 (visualization tool for elasticsearch cluster)
- mlex_search_api_setup_1 (security setup for elasticsearch engine, this will exit upon succesful execution)


## Usage

There are two approaches to launch the dash interface:

- Navigate to 'Dash-Fronty' container in Docker Desktop, click first button 'open in browser'
- Open a new browser, navigate to 'localhost:8061'

Two searching methods has been enabled:

- Text search: search for contents from content registry
- Image search: similarity search using PyCBIR backend. To use, you need to download and dockerize [[mlex_pyCBIR]](https://github.com/mlexchange/mlex_pyCBIR).


## API Calls
Search API uses FastAPI as the backend, current available calls:

http://localhost:8060/api/lbl-mlexchange/docs


## Contribution
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.


## License
MLExchange Copyright (c) 2021, The Regents of the University of California,
through Lawrence Berkeley National Laboratory (subject to receipt of
any required approvals from the U.S. Dept. of Energy). All rights reserved. For details navigate to LICENSE.txt.