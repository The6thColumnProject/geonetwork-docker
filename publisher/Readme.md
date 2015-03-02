
Publisher
=========

Basics
------
* Have [docker installed](https://docs.docker.com/reference/#installation)

The container is automatically built.  The build resides in the docker registry as [geo-publisher](https://registry.hub.docker.com/u/the6thcolumnproject/geo-publisher/)

* Fetch the container from the registry:

```
%> docker pull the6thcolumnproject/geo-publisher
```

* Or, as is the usual case with our distributions, you may build it yourself with our script:

```
%> ./build
```

Then you can test it by generating a json file from an nc one:
```
bin/nc2json some/where/some_file.nc
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
The installer and the docker container have in place [elsticserach-head](http://mobz.github.io/elasticsearch-head/) for viewing your cluster and [elasticsearch-inquisitor](https://github.com/polyfractal/elasticsearch-inquisitor) for building queries over your data.

See:
<ul>
<li> <a href="http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/index.html">Elasticsearch reference</a>
<li> <a href="http://okfnlabs.org/blog/2013/07/01/elasticsearch-query-tutorial.html">Good primer article</a>
<li> <a href="http://www.elasticsearch.org/client/community/current/front-ends.html">Front Ends</a>
</ul>

Container
-----
This software is provided as a Docker container located here:
<https://registry.hub.docker.com/u/the6thcolumnproject/geo-publisher/>
