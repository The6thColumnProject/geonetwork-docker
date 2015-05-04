#!/usr/bin/env python

import sys, os
import json
import logging

import utils
from publisher import SimplePathParser, NetCDFFileHandler, SetEncoder
from es_api import ESFactory, ES


def process(meta, elasticsearch, global_att, show=True, rename_dict={}):
    """meta :=  the complete metadata dictionary that will be stored
    elasticsearch := some es connection or None
    global_att := global attributes to extend the original ones
    show := if the json craeted will get displayed to STDOUT
    rename_dict := a dict used for renaming keys"""
    meta['global'].update(global_att)
    
    #rename properties as required:
    utils.rename_keys(meta, rename_dict)

    meta_json = json.dumps(meta, indent=2, cls=SetEncoder)
    if show:
        print meta_json
    if elasticsearch:
        #trying some workaround because of serialization
        elasticsearch.publish(json.loads(meta_json))

def main(orig_args=sys.argv[1:]):
    
    #work around for handling attributes
    args = []
    attr_follows = False
    global_att = {}
    for arg in orig_args:
        if attr_follows:
            items = arg.split('=',1)
            if len(items) == 1:
                global_att[items[0]] = 'true'
            else:
                global_att[items[0]] = items[1]
            attr_follows = False
        elif arg == '--global':
            attr_follows = True
        else:
            args.append(arg)

    import argparse
    parser = argparse.ArgumentParser(description='Extracts metadata from Netcdf files')
    parser.add_argument('files', metavar="FILE/DIR", nargs=1)
    parser.add_argument('-d', '--debug', action='store_true', help='show debug info')
    parser.add_argument('--log-level', help='set some specific log level')
    parser.add_argument('--show', action='store_true', help='show produced json')
    parser.add_argument('--dry-run', action='store_true', help="Don't publish anything")
    parser.add_argument('--json_dump_dir', help='Dump the generated json files to this dir (generate same directory structure as real path)')
    parser.add_argument('-n', metavar='CONTAINER', help='Contair name with an elasticsearch instance running in it where we will be publishing')
    parser.add_argument('-p', '--port', type=int, help='Elastic search port (default 9200)', default=9200)
    #This is not used here, but used by the calling script. Still we want to show a single help.
    parser.add_argument('--host', help='Elastic search host')
    parser.add_argument('--global', help='Adds some gobal attribute using "=" as separator (e.g. --global institute=AWI). Can be used multiple times.')
    parser.add_argument('--dir-structure', help='Metadata directory structure (e.g. /*/institute/model/realm so /a/b/c/d/e -> institute=b, model=c,realm=d) ')
    parser.add_argument('--file-structure', help='Metadata File structure. (e.g. institute_model_realm so ABC_mod1_atmos_blah.nc -> institute=ABC, model=mod1,realm=atmos) ')
    parser.add_argument('--file-structure-sep', help='Separator used in the filename for structuring data (default "_")', default='_')
    parser.add_argument('--exclude-crawl', help='Exclude the given regular expression while crawling')
    parser.add_argument('--include-crawl', help='Include only the given regular expression while  crawling')

    pargs = parser.parse_args(args)
    

    if pargs.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif pargs.log_level:
        numeric_level = getattr(logging, pargs.log_level.upper(), None)
        if not isinstance(numeric_level, int):
                raise ValueError('Invalid log level: %s' % loglevel)
        logging.basicConfig(level=numeric_level)
    
    #make sure we have some default logger or configure one.
    if not logging.getLogger().handlers:
        logging.basicConfig()

    #handle input properly
    if pargs.dir_structure is not None or pargs.file_structure is not None:
        path_parser = SimplePathParser(dir_structure=pargs.dir_structure,
                                        file_structure=pargs.file_structure,
                                        file_sep=pargs.file_structure_sep)
    else:
        path_parser = None
    handler = NetCDFFileHandler(path_parser=path_parser, json_dump_dir=pargs.json_dump_dir)

    exclude = []
    include = None
    if pargs.exclude_crawl:
        import re
        exclude.append(re.compile(pargs.exclude_crawl))
    if pargs.include_crawl:
        import re
        include = [re.compile(pargs.include_crawl)]

    if pargs.host:
        es = ESFactory.basicConnector(pargs.host, port=pargs.port)
    elif not pargs.dry_run:
        es = ESFactory.fromDockerEnvironment()
    else:
        es = None

    for filename in pargs.files:
        if os.path.isdir(filename):
            for file_meta in handler.crawl_dir(filename, exclude=exclude, include=include):
                process(file_meta, es, global_att, show=pargs.show)
        elif os.path.isfile(filename):
            file_meta = handler.get_metadata(filename)
            process(file_meta, es, global_att, show=pargs.show)
        else:
            print "%s is not a file/dir. skipping" % filename
if __name__ == '__main__':
    main()

