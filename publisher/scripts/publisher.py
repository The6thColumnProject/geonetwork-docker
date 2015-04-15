#!/usr/bin/env python

from netCDF4 import Dataset
import os, sys
import logging
import utils
import datetime
import json


class SetEncoder(json.JSONEncoder):
    "This is just used for setting up the json parser to do it's best"
    def default(self, obj):
        try:
            return json.JSONEncoder.default(self, obj)
        except:
            return str(obj)

class SimplePathParser(object):
    """Simple directory parser strategy that is initialized with a string of the form:
        /*/*/*/model/institute/*/variable
        
        When passed a path like: /data/project1/something/mymodel/ABCD/production/ps
        produces a map: {'model': 'mymodel, 'institute':'ABCD', 'variable':ps}"""
    SKIP = '*'
    
    @staticmethod
    def parse_structure(structure, separator):
        metadict = {}
        if structure is not None and len(structure) > 0:
            position = 0
            for value in structure.split(separator):
                if len(value) > 0 and value != SimplePathParser.SKIP:
                    metadict[position] = value
                position += 1
        return metadict

    def __init__(self, dir_structure=None, dir_sep=os.sep, file_structure=None, file_sep='_'):
        """The separators are used for splitting the directory and file parts. 
        In the case of directories is only used for parsing the structure, the real separator will be
        read from the OS."""
        self.file_sep = file_sep
        if dir_structure and dir_structure[0] != '/':
            dir_structure = '/' + dir_structure 
        self.dir_metadict = SimplePathParser.parse_structure(dir_structure, dir_sep)
        self.file_metadict = SimplePathParser.parse_structure(file_structure, file_sep)

    def extract(self, path):
        "Extracts metadata from the path and file name"
        meta = {}
        parts = os.path.dirname(path).split(os.sep)
        for pos, name in self.dir_metadict.items():
            meta[name] = parts[pos]
        
        parts = os.path.basename(path).split(self.file_sep)
        if '.' in parts[-1]:
            parts[-1] = parts[-1][:parts[-1].rfind('.')]
        for pos, name in self.file_metadict.items():
            meta[name] = parts[pos]
        return meta
            

class NetCDFFileHandler(object):
    """This file runs in a docker container and has no access to the complete files system.
    The user defines a directory from which we will be crawling. We passed the relative
    path to it in an environmental variable and started crawling from there.
    This is sadly not enough for symlinks as they might point somewhere else.
    We will be assuming the file is within bounds, which means both the target and the source are accessible from the same
    root directory."""
    CONTAINER_DATA_ROOT = '/data_root/'
    HOST_DATA_DIR_VAR = 'DATA_PATH'
    EXTRA = '__extra'
    REMOTE_ENV = dict(DOCKER_LOCALIP='host_ip',
                    DOCKER_LOCALHOSTNAME='hostname')

    def __init__(self, path_parser = None):
        self.path_parser = path_parser
        self.default = {}
        self.default[NetCDFFileHandler.EXTRA] = {'created' : datetime.datetime.utcnow().isoformat()}
        for env_name, prop_name in NetCDFFileHandler.REMOTE_ENV.items():
            if env_name in os.environ:
                self.default[NetCDFFileHandler.EXTRA][prop_name] = os.environ[env_name]
        self._realpath = os.getenv(NetCDFFileHandler.HOST_DATA_DIR_VAR)
        self._localpath = os.path.join(NetCDFFileHandler.CONTAINER_DATA_ROOT, *self._realpath.split('/')[2:])

    def __get_id(self, meta):
        "The id is build from the hostname (if present) + ':' + the file path"
        return '%s:%s' % (meta[NetCDFFileHandler.EXTRA].get('hostname'), meta[NetCDFFileHandler.EXTRA]['original_path'])

    def __extract_from_filename(self, realpath):
        "The filename must be absolute"
        if self.path_parser is not None:
            meta = self.path_parser.extract(realpath)
        else:
            meta = {}
        meta[NetCDFFileHandler.EXTRA] = dict(original_path = realpath)
        return meta
        
    def __extract_variable(self, netcdfVar):
        "Extracts metadata from the given variable."
        meta = {}
        #basic metadata
        meta['dimensions'] = netcdfVar.dimensions
        #extract variable attributes
        for att in netcdfVar.ncattrs():
            meta[att] = netcdfVar.getncattr(att)
        return meta

    def __extract_dimension(self, dim):
        "Extracts metadata from the given dimension"
        meta = {}
        meta['size'] = len(dim)
        meta['unlimited'] = dim.isunlimited()
        return meta

    def crawl_dir(self, path, exclude=[], include=None, store=False):
        for root, subdirs, files in os.walk(path):
            for f in files:
                skip = False
                current = os.path.join(root, f)
                for e in exclude:
                    if e.match(current):
                        skip = True
                        break
                if include is not None and not skip:
                    for i in include:
                        if not i.match(current):
                            skip = True
                            break
                if not skip:
                    try:
                        yield self.get_metadata(current, store=store)
                    except Exception as e:
                        logging.log(logging.ERROR, "Could not process %s (%s)" % (f, e)) 
    def _get_final_path(self, filename):
        "returns the path behind which a file can be read, i.e. resolved from all links"
        if os.path.islink(filename):
            #read the link (the real path) and convert it to local so we can read it from within the container.
            realpath = os.readlink(filename)
            return realpath.replace(self._realpath, self._localpath, 1)
        return filename

    def get_metadata(self, filename, store=False):
        "Extracts the metadata from the given local file (might be symlink, or non canonical)"
        #absolute local path (local is within container)
        localpath = os.path.abspath(filename)
        #the complete realpath on the host (non resolved in case of symlink)
        realpath = localpath.replace(self._localpath, self._realpath, 1)

        meta = utils.dict_merge({}, self.default, self.__extract_from_filename(realpath))
        #we should read the real file, which might be something completely different as a target of a symlink
        #basically we get the metadata from the link and the data from the target
        with Dataset(self._get_final_path(localpath), 'r') as f:
            meta['global'] = {}
            for g_att in f.ncattrs():
                meta['global'][str(g_att)] = getattr(f, g_att)
            meta['variables'] = {}
            for var in f.variables:
                meta['variables'][var] = self.__extract_variable(f.variables[var])
            meta['dimensions'] = {}
            for dim in f.dimensions:
                meta['dimensions'][dim] = self.__extract_dimension(f.dimensions[dim])

        #the id will be removed when publishing and used as such
        meta[NetCDFFileHandler.EXTRA]['_id'] = self.__get_id(meta)
        if store:
            meta_json = json.dumps(meta, indent=2, cls=SetEncoder)
            try:
                with open(localpath + '.json', 'w') as f:
                    f.write(meta_json)
            except Exception as e:
                #we try to write in localpath and report the error in realpath... that is sadly intentional
                #as the localpath is the internal representation of the realpath, which is the only thing the user
                #will ever see.
                sys.stderr.write('Could not write file %s: %s\n' % (realpath, e))
                sys.stderr.flush()
        return meta
    
