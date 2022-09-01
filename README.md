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

Note: If you encounter issues elastic server, please make sure the `vm.max_map_count` kernel setting must be set to at least 262144 for production use. To do this:

Linux:
To view the current value for the vm.max_map_count setting, run:
```
grep vm.max_map_count /etc/sysctl.conf
vm.max_map_count=262144
```
To apply the setting on a live system, run:
```
sysctl -w vm.max_map_count=262144
```

To permanently change the value for the vm.max_map_count setting, update the value in /etc/sysctl.conf.

MacOS with Docker for Mac:
The vm.max_map_count setting must be set within the xhyve virtual machine:
```
# From the command line, run:
screen ~/Library/Containers/com.docker.docker/Data/vms/0/tty
# Press enter and use sysctl to configure vm.max_map_count:
sysctl -w vm.max_map_count=262144
#To exit the screen session, type Ctrl a d.
```

Windows and MacOS with Docker Desktop:
The vm.max_map_count setting must be set via docker-machine:
```
docker-machine ssh
sudo sysctl -w vm.max_map_count=262144
```

Windows with Docker Desktop WSL 2 backend:
The vm.max_map_count setting must be set in the docker-desktop container:
```
wsl -d docker-desktop
sysctl -w vm.max_map_count=262144
```

For more details related to this issue, please refer to [[Elasticsearch Guide]](https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html) 

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