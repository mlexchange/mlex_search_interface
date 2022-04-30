# MLExchange Search API

The Search API provides text and image searching tools for MLExchange platform. The purpose of this API is to help user nevigate through different apps and workflows within the platform, providing smooth user experience.

## Installation

Current version of the Search API has been dockerized. To use:

1. Install Docker and Docker Desktop(https://www.docker.com/products/docker-desktop/) 

2. Navigate to the root directory of this repo

```bash
cd mlex_search_api
```

3. Build the container using docker-compose

```bash
docker-compose up --build
```

4. Wait until the process finish, you should see 5 containers under the 'mlex_search_api' container:

- Dash-Fronty (frontend)
- FastAPI (backend)
- mlex_search_api_elasticsearch_1 (search engine)
- mlex_search_api_kibana_1 (visualization tool for elasticsearch cluster)
- mlex_search_api_setup_1 (security setup for elasticsearch engine)


## Usage

There are two approaches to launch the dash interface:

- Navigate to 'Dash-Fronty' container in Docker Desktop, click first button 'open in browser'
- Open a new browser, navigate to 'localhost:8061'


## API Calls
Search API uses FastAPI as the backend, current available calls:

- GET /search/{keyword}
- GET /create-index/{index}
- GET /create-doc/{index}/{doc} (under development)
- GET /delete-doc/{index}/{keyword}
- GET /delete-index/{index}

## Contribution
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.


## License
MLExchange Copyright (c) 2021, The Regents of the University of California,
through Lawrence Berkeley National Laboratory (subject to receipt of
any required approvals from the U.S. Dept. of Energy). All rights reserved. For details navigate to LICENSE.txt.