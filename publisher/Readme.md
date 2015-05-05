Publisher
=========

Basics
------
* Have [docker installed](https://docs.docker.com/reference/#installation)

Installation
------

```
%> curl -o ./geo-publisher -s https://raw.githubusercontent.com/the6thcolumnproject/geonetwork-docker/master/publisher/etc/geo-publisher
%> chmod 755 ./geo-publisher
%> ./geo-publisher
```

This will:

* perform a docker <i>pull</i> from the docker repository.
* download the helper publishing scripts (nc2es nc2geonetwork nc2json query run) [default install location: /usr/local/bin]

Note
------
The container is automatically built.  The build resides in the docker registry as [geo-publisher](https://registry.hub.docker.com/u/the6thcolumnproject/geo-publisher/)

* Fetch the container from the registry:

```
%> docker pull the6thcolumnproject/geo-publisher
```

* Or, as is the usual case with our distributions, you may build it yourself with our script:

```
%> git clone https://github.com/The6thColumnProject/geonetwork-docker.git
%> cd geonetwork-docker/publisher
%> ./build
```

Then you can test it by generating a json file from an nc one:
```
%> bin/nc2json some/where/some_file.nc
```

nc2json
-------

This script is used for generating json metadata to STDOUT. To view all options use --help:
```
$ bin/nc2json --help
usage: to_json.py [-h] [--show] [--dry-run] [--dir-structure DIR_STRUCTURE]
                  [--file-structure FILE_STRUCTURE]
                  [--file-structure-sep FILE_STRUCTURE_SEP]
                  [--exclude-crawl EXCLUDE_CRAWL]
                  [--include-crawl INCLUDE_CRAWL] [-p PORT] [--host HOST]
                  files [files ...]

Extracts metadata from Netcdf files

positional arguments:
  files

optional arguments:
  -h, --help            show this help message and exit
  --show                show produced json
  --dry-run             Don't publish anything
  --dir-structure DIR_STRUCTURE
                        Metadata directory structure (e.g.
                        /*/institute/model/realm so /a/b/c/d/e -> institute=b,
                        model=c,realm=d)
  --file-structure FILE_STRUCTURE
                        Metadata File structure. (e.g. institute_model_realm
                        so ABC_mod1_atmos_blah.nc -> institute=ABC,
                        model=mod1,realm=atmos)
  --file-structure-sep FILE_STRUCTURE_SEP
                        Separator used in the filename for structuring data
                        (default "_")
  --exclude-crawl EXCLUDE_CRAWL
                        Exclude the given regular expression while crawling
  --include-crawl INCLUDE_CRAWL
                        Include only the given regular expression while
                        crawling
  -p PORT, --port PORT  Elastic search port (default 9200)
  --host HOST           Elastic search host
```
`nc2json` is a convenience script that already defines `--show` `--dry-run`. There's
no point in definin elast search parameters but you may define the rest.

A more elaborate example:
```bash
$> bin/nc2json --dir-structure '/*/*/*/model/*/institute' \
    --file-structure 'simulation_*_ensemble' \
    --include-crawl '.*\.nc$' \
    --exclude-crawl '.*/test/.*' \
    /some/dir
```

The previous example crawls `/some/dir` looking for files ending in `.nc` and
skipping anything that has _test_ as some parent directory.
Besides the file metadata, there are four more metadata entries being extracted,
two from the full path (model and institute) and two from the file name (simulation
and ensemble).
So if a file is located at:
`/some/path/trans/moly/dolly/a/b/c/one_two_three_four.nc`
The resulting file metadata will be enriched with:
```json
{
  "model": "moly",
  "institute": "a",
  "simulation": "one",
  "ensemble": "three",
  ...
}
```

nc2es
-----

This script is used like the nc2json (same logic underneath) but its objective
is to push the json file into some elastic search instance.

For this there are two main usages:

1. For connecting to some container instance:

    ```bash
    $> bin/nc2es -n some_container [options like nc2json]
    ```

2. For connecting to some external instance (be warn that this is run within a container, so it might not see what you think)

    ```bash
    $> bin/nc2es --host elasticsearch.host -p 9200 [options like nc2json]
    ```

### Debugging

As usual you can get an into the container itself by running it interactively:
```bash
$> ./run -i -D .
```
The `-D` flag is sharing the given directory and mounting it in /data inside the container.


query
-----

Used for searching in elastic search. Be warned that this script runs within a container,
i.e. the network you see is not the same this container will see.

Usage similar to nc2es. Here an example:
```bash
$> bin/query -n t1 -q '*:*'
```
Searches for all documents in the t1 container.

Query (using RESTful API)
-----

Here is a RESTful query to match againt "experiment_id" returning the data for the "original_path" for all the hits:

```bash
$> curl -s -X GET http://10.0.0.238:9200/_search -d '{"fields" : ["__extra.original_path"], "query" : {"match":{"global.experiment_id": "1pctCO2"}}}' | python -m json.tool

{
    "_shards": {
        "failed": 0,
        "successful": 5,
        "total": 5
    },
    "hits": {
        "hits": [
            {
                "_id": "/home/553/gmb553/geonetwork-docker/publisher/help/gridspec_seaIce_fx_GFDL-ESM2M_1pctCO2_r0i0p0.nc",
                "_index": "geonetwork",
                "_score": 0.30685282000000003,
                "_type": "file",
                "fields": {
                    "__extra.original_path": [
                        "/home/553/gmb553/geonetwork-docker/publisher/help/gridspec_seaIce_fx_GFDL-ESM2M_1pctCO2_r0i0p0.nc"
                    ]
                }
            }
        ],
        "max_score": 0.30685282000000003,
        "total": 1
    },
    "timed_out": false,
    "took": 4
}
```

Here is a query using the RESTful API to get 4 fields from the data
matching the _id query term:

```bash
$> curl -s -X GET http://10.0.0.238:9200/_search -d
   '{"fields" :
   ["__extra.original_path","global.institute_id","global.title","globa.variables"],
   "query" : {"term":{"_id": "/home/553/gmb553/geonetwork-docker/publisher/help/gridspec_seaIce_fx_GFDL-ESM2M_1pctCO2_r0i0p0.nc"}}}' | python -m json.tool
{
    "_shards": {
        "failed": 0,
        "successful": 5,
        "total": 5
    },
    "hits": {
        "hits": [
            {
                "_id": "/home/553/gmb553/geonetwork-docker/publisher/help/gridspec_seaIce_fx_GFDL-ESM2M_1pctCO2_r0i0p0.nc",
                "_index": "geonetwork",
                "_score": 1.0,
                "_type": "file",
                "fields": {
                    "__extra.original_path": [
                        "/home/553/gmb553/geonetwork-docker/publisher/help/gridspec_seaIce_fx_GFDL-ESM2M_1pctCO2_r0i0p0.nc"
],
                    "global.institute_id": [
                        "NOAA GFDL"
                    ],
                    "global.title": [
                        "NOAA GFDL GFDL-ESM2M, 1 percent per year CO2 experiment output for CMIP5 AR5"
                    ]
                }
            }
        ],
        "max_score": 1.0,
        "total": 1
    },
    "timed_out": false,
    "took": 4
}
```

Here is a query, using a wildcard and getting prescirbed fields.  It shows the nomenclature for traversing the tree structure of keys to expose particular fields.


```
curl -s -X GET http://10.0.0.238:9200/_search -d '{"fields":["__extra.original_path","global.frequency","variables.height.axis"], "query":{"wildcard":{"global.frequency":"mo*"}}}' | python -m json.tool
{
    "_shards": {
        "failed": 0,
        "successful": 5,
        "total": 5
    },
    "hits": {
        "hits": [
            {
                "_id": "/home/553/gmb553/uas_Amon_bcc-csm1-1_historical_r1i1p1_185001-201212.nc",
                "_index": "geonetwork",
                "_score": 1.0,
                "_type": "file",
                "fields": {
                    "__extra.original_path": [
                        "/home/553/gmb553/uas_Amon_bcc-csm1-1_historical_r1i1p1_185001-201212.nc"
                    ],
                    "global.frequency": [
                        "mon"
                    ],
                    "variables.height.axis": [
                        "Z"
                    ]
                }
            }
        ],
        "max_score": 1.0,
        "total": 1
    },
    "timed_out": false,
    "took": 5
}
```

The installer and the docker container have in place [elsticserach-head](http://mobz.github.io/elasticsearch-head/) for viewing your cluster and [elasticsearch-inquisitor](https://github.com/polyfractal/elasticsearch-inquisitor) for building queries over your data.

See:
<ul>
<li> <a href="http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/index.html">Elasticsearch reference</a>
<li> <a href="http://okfnlabs.org/blog/2013/07/01/elasticsearch-query-tutorial.html">Good primer article</a>
<li> <a href="http://joelabrahamsson.com/elasticsearch-101/">Elasticsearch 101</a>
<li> <a href="https://chrome.google.com/webstore/detail/sense-beta/lhjgkmllcaadmopgmanpapmpjgmfcfig/related?hl=en">Sense</a> - A Very nice Chrome pluggin for dealing with JSON querying
<li> <a href="http://www.elasticsearch.org/guide/en/elasticsearch/client/community/current/front-ends.html">Front Ends</a>
</ul>

Container
-----
This software is provided as a Docker container located here:
<https://registry.hub.docker.com/u/the6thcolumnproject/geo-publisher/>

Cluster Sanity Check
-----
To check on the local node:

```
%> curl http://10.0.0.228:9200/
```
Resultant Output:

```
{
  "status" : 200,
  "name" : "Wundarr the Aquarian",
  "version" : {
    "number" : "1.3.4",
    "build_hash" : "a70f3ccb52200f8f2c87e9c370c6597448eb3e45",
    "build_timestamp" : "2014-09-30T09:07:17Z",
    "build_snapshot" : false,
    "lucene_version" : "4.9"
  },
  "tagline" : "You Know, for Search"
}
```

To minimally check on the cluster:

```
%> curl http://10.0.0.228:9200/_cluster/health?pretty=true
```

Resultant Output:

```
{
  "cluster_name" : "moya-search",
  "status" : "green",
  "timed_out" : false,
  "number_of_nodes" : 3,
  "number_of_data_nodes" : 3,
  "active_primary_shards" : 5,
  "active_shards" : 10,
  "relocating_shards" : 0,
  "initializing_shards" : 0,
  "unassigned_shards" : 0
}
```
<hr>

Basic Use Case
-----

<<<<<<< HEAD
* Publish all .nc's linked in /g/data/ua6/drstree/CMIP5/GCM/CSIRO-BOM/ACCESS1-3

```
%>
```
* Find all data with frequency=mon, variable=tos

```
%>
```
=======
* Publish all .nc's linked in /g/data/ua6/drstree/CMIP5/GCM/CSIRO-BOM/ACCESS1-0/...

	(without stipulating dir structure meta data info)

```
%> ./bin/nc2es --host 10.0.0.238 -p 9200 --include-crawl '.*.nc$' --log-level info --json_dump_dir /tmp/json_dumps /g/data1/ua6/drstree/CMIP5/GCM/CSIRO-BOM/ACCESS1-0/historical/mon/ocean/thetao/r1i1p1
```
```
INFO:ES:Publishing es.novalocal:/g/data1/ua6/drstree/CMIP5/GCM/CSIRO-BOM/ACCESS1-0/historical/mon/ocean/thetao/r1i1p1/thetao_Omon_ACCESS1-0_historical_r1i1p1_195001-195412.nc
INFO:urllib3.connectionpool:Starting new HTTP connection (1): 10.0.0.238
INFO:elasticsearch:PUT http://10.0.0.238:9200/geonetwork/file/es.novalocal%3A%2Fg%2Fdata1%2Fua6%2Fdrstree%2FCMIP5%2FGCM%2FCSIRO-BOM%2FACCESS1-0%2Fhistorical%2Fmon%2Focean%2Fthetao%2Fr1i1p1%2Fthetao_Omon_ACCESS1-0_historical_r1i1p1_195001-195412.nc [status:200 request:0.015s]
INFO:elasticsearch.trace:curl -XPUT 'http://localhost:9200/geonetwork/file/es.novalocal%3A%2Fg%2Fdata1%2Fua6%2Fdrstree%2FCMIP5%2FGCM%2FCSIRO-BOM%2FACCESS1-0%2Fhistorical%2Fmon%2Focean%2Fthetao%2Fr1i1p1%2Fthetao_Omon_ACCESS1-0_historical_r1i1p1_195001-195412.nc?pretty' -d '{
  "__extra": {
    "created": "2015-05-04T23:04:06.752535",
    "host_ip": "172.17.42.1",
    "hostname": "es.novalocal",
    "original_path": "/g/data1/ua6/drstree/CMIP5/GCM/CSIRO-BOM/ACCESS1-0/historical/mon/ocean/thetao/r1i1p1/thetao_Omon_ACCESS1-0_historical_r1i1p1_195001-195412.nc"
  },
  "dimensions": {
    "bnds": {
      "size": 2,
      "unlimited": false
    },
    "i": {
      "size": 360,
      "unlimited": false
    },
    "j": {
      "size": 300,
      "unlimited": false
    },
    "lev": {
      "size": 50,
      "unlimited": false
    },
    "time": {
      "size": 60,
      "unlimited": true
    },
    "vertices": {
      "size": 4,
      "unlimited": false
    }
  },
  "global": {
    "Conventions": "CF-1.4",
    "branch_time": 109207.0,
    "cmor_version": "2.8.0",
    "contact": "The ACCESS wiki: http://wiki.csiro.au/confluence/display/ACCESS/Home. Contact Tony.Hirst@csiro.au regarding the ACCESS coupled climate model. Contact Peter.Uhe@csiro.au regarding ACCESS coupled climate model CMIP5 datasets.",
    "creation_date": "2012-01-15T15:59:38Z",
    "experiment": "historical",
    "experiment_id": "historical",
    "forcing": "GHG, Oz, SA, Sl, Vl, BC, OC, (GHG = CO2, N2O, CH4, CFC11, CFC12, CFC113, HCFC22, HFC125, HFC134a)",
    "frequency": "mon",
    "history": "CMIP5 compliant file produced from raw ACCESS model output using the ACCESS Post-Processor and CMOR2. 2012-01-15T15:59:38Z CMOR rewrote data to comply with CF standards and CMIP5 requirements.",
    "initialization_method": "1",
    "institute_id": "CSIRO-BOM",
    "institution": "CSIRO (Commonwealth Scientific and Industrial Research Organisation, Australia), and BOM (Bureau of Meteorology, Australia)",
    "model_id": "ACCESS1-0",
    "modeling_realm": "ocean",
    "parent_experiment": "pre-industrial control",
    "parent_experiment_id": "piControl",
    "parent_experiment_rip": "r1i1p1",
    "physics_version": "1",
    "product": "output",
    "project_id": "CMIP5",
    "realization": "1",
    "references": "See http://wiki.csiro.au/confluence/display/ACCESS/ACCESS+Publications",
    "source": "ACCESS1-0 2011. Atmosphere: AGCM v1.0 (N96 grid-point, 1.875 degrees EW x approx 1.25 degree NS, 38 levels); ocean: NOAA/GFDL MOM4p1 (nominal 1.0 degree EW x 1.0 degrees NS, tripolar north of 65N, equatorial refinement to 1/3 degree from 10S to 10 N, cosine dependent NS south of 25S, 50 levels); sea ice: CICE4.1 (nominal 1.0 degree EW x 1.0 degrees NS, tripolar north of 65N, equatorial refinement to 1/3 degree from 10S to 10 N, cosine dependent NS south of 25S); land: MOSES2 (1.875 degree EW x 1.25 degree NS, 4 levels",
    "table_id": "Table Omon (27 April 2011) 694b38a3f68f18e58ba80230aa4746ea",
    "title": "ACCESS1-0 model output prepared for CMIP5 historical",
    "tracking_id": "3609a266-6ae8-4f95-9b02-1b825521c61f",
    "version_number": "v20120115"
  },
  "variables": {
    "i": {
      "dimensions": [
        "i"
      ],
      "long_name": "cell index along first dimension",
      "units": "1"
    },
    ...

```
(In the above command we stated that the JSON intermediate representaiton should be put under /tmp/json_dump.  For each nc file posted there is a corresponding *.nc.json file)

```
%> find /tmp/json_dumps/
/tmp/json_dumps/
/tmp/json_dumps/g
/tmp/json_dumps/g/data1
/tmp/json_dumps/g/data1/ua6
/tmp/json_dumps/g/data1/ua6/drstree
/tmp/json_dumps/g/data1/ua6/drstree/CMIP5
/tmp/json_dumps/g/data1/ua6/drstree/CMIP5/GCM
/tmp/json_dumps/g/data1/ua6/drstree/CMIP5/GCM/CSIRO-BOM
/tmp/json_dumps/g/data1/ua6/drstree/CMIP5/GCM/CSIRO-BOM/ACCESS1-0
/tmp/json_dumps/g/data1/ua6/drstree/CMIP5/GCM/CSIRO-BOM/ACCESS1-0/historical
/tmp/json_dumps/g/data1/ua6/drstree/CMIP5/GCM/CSIRO-BOM/ACCESS1-0/historical/mon
/tmp/json_dumps/g/data1/ua6/drstree/CMIP5/GCM/CSIRO-BOM/ACCESS1-0/historical/mon/ocean
/tmp/json_dumps/g/data1/ua6/drstree/CMIP5/GCM/CSIRO-BOM/ACCESS1-0/historical/mon/ocean/thetao
/tmp/json_dumps/g/data1/ua6/drstree/CMIP5/GCM/CSIRO-BOM/ACCESS1-0/historical/mon/ocean/thetao/r1i1p1
/tmp/json_dumps/g/data1/ua6/drstree/CMIP5/GCM/CSIRO-BOM/ACCESS1-0/historical/mon/ocean/thetao/r1i1p1/thetao_Omon_ACCESS1-0_historical_r1i1p1_185501-185912.nc.json
/tmp/json_dumps/g/data1/ua6/drstree/CMIP5/GCM/CSIRO-BOM/ACCESS1-0/historical/mon/ocean/thetao/r1i1p1/thetao_Omon_ACCESS1-0_historical_r1i1p1_191501-191912.nc.json
/tmp/json_dumps/g/data1/ua6/drstree/CMIP5/GCM/CSIRO-BOM/ACCESS1-0/historical/mon/ocean/thetao/r1i1p1/thetao_Omon_ACCESS1-0_historical_r1i1p1_198001-198412.nc.json
/tmp/json_dumps/g/data1/ua6/drstree/CMIP5/GCM/CSIRO-BOM/ACCESS1-0/historical/mon/ocean/thetao/r1i1p1/thetao_Omon_ACCESS1-0_historical_r1i1p1_195001-195412.nc.json
/tmp/json_dumps/g/data1/ua6/drstree/CMIP5/GCM/CSIRO-BOM/ACCESS1-0/historical/mon/ocean/thetao/r1i1p1/thetao_Omon_ACCESS1-0_historical_r1i1p1_198501-198912.nc.json
/tmp/json_dumps/g/data1/ua6/drstree/CMIP5/GCM/CSIRO-BOM/ACCESS1-0/historical/mon/ocean/thetao/r1i1p1/thetao_Omon_ACCESS1-0_historical_r1i1p1_187501-187912.nc.json
/tmp/json_dumps/g/data1/ua6/drstree/CMIP5/GCM/CSIRO-BOM/ACCESS1-0/historical/mon/ocean/thetao/r1i1p1/thetao_Omon_ACCESS1-0_historical_r1i1p1_196001-196412.nc.json
/tmp/json_dumps/g/data1/ua6/drstree/CMIP5/GCM/CSIRO-BOM/ACCESS1-0/historical/mon/ocean/thetao/r1i1p1/thetao_Omon_ACCESS1-0_historical_r1i1p1_187001-187412.nc.json
/tmp/json_dumps/g/data1/ua6/drstree/CMIP5/GCM/CSIRO-BOM/ACCESS1-0/historical/mon/ocean/thetao/r1i1p1/thetao_Omon_ACCESS1-0_historical_r1i1p1_188001-188412.nc.json
/tmp/json_dumps/g/data1/ua6/drstree/CMIP5/GCM/CSIRO-BOM/ACCESS1-0/historical/mon/ocean/thetao/r1i1p1/thetao_Omon_ACCESS1-0_historical_r1i1p1_186501-186912.nc.json
/tmp/json_dumps/g/data1/ua6/drstree/CMIP5/GCM/CSIRO-BOM/ACCESS1-0/historical/mon/ocean/thetao/r1i1p1/thetao_Omon_ACCESS1-0_historical_r1i1p1_189501-189912.nc.json
...
```


* Get the count of what is in the index

```
%>curl -s -X POST 'http://10.0.0.238:9200/_count?pretty' -d '{"query" : {"match_all":{}}}'
```
```
{
  "count" : 32,
  "_shards" : {
    "total" : 5,
    "successful" : 5,
    "failed" : 0
  }
}
```
* Search query (plush grepp'ing around) to show *.nc files

```
%> curl -s -X POST 'http://10.0.0.238:9200/_search?size=50000' -d '{"query" : {"match_all":{}}}' | python -m json.tool | grep _id | grep '.nc'
```
```
"_id": "es.novalocal:/g/data1/ua6/drstree/CMIP5/GCM/CSIRO-BOM/ACCESS1-0/historical/mon/ocean/thetao/r1i1p1/thetao_Omon_ACCESS1-0_historical_r1i1p1_195001-195412.nc",
"_id": "es.novalocal:/g/data1/ua6/drstree/CMIP5/GCM/CSIRO-BOM/ACCESS1-0/historical/mon/ocean/thetao/r1i1p1/thetao_Omon_ACCESS1-0_historical_r1i1p1_194001-194412.nc",
"_id": "es.novalocal:/g/data1/ua6/drstree/CMIP5/GCM/CSIRO-BOM/ACCESS1-0/historical/mon/ocean/thetao/r1i1p1/thetao_Omon_ACCESS1-0_historical_r1i1p1_186501-186912.nc",
"_id": "es.novalocal:/g/data1/ua6/drstree/CMIP5/GCM/CSIRO-BOM/ACCESS1-0/historical/mon/ocean/thetao/r1i1p1/thetao_Omon_ACCESS1-0_historical_r1i1p1_191501-191912.nc",
```


General Operations
------

* Delete an index

```
%> curl -s -X DELETE 'http://10.0.0.238:9200/geonetwork'
```

### Notes n' Links

<a href="http://cmip-pcmdi.llnl.gov/cmip5/docs/cmip5_data_reference_syntax.pdf">DRS syntax document</a>
