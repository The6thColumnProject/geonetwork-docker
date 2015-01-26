#!/usr/bin/env python

from netCDF4 import Dataset
import os
import logging
import utils
import datetime

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
    CONTAINER_DATA_DIR = '/data/'
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

    def __get_id(self, meta):
        "The id is build from the hostname (if present) + ':' + the file path"
        return '%s:%s' % (meta[NetCDFFileHandler.EXTRA].get('hostname'), meta[NetCDFFileHandler.EXTRA]['original_path'])

    def __extract_from_filename(self, filename):
        
        realpath = os.path.abspath(filename)
        if realpath.startswith(NetCDFFileHandler.CONTAINER_DATA_DIR):
            realpath = os.path.join(os.getenv(NetCDFFileHandler.HOST_DATA_DIR_VAR),
                                    realpath[len(NetCDFFileHandler.CONTAINER_DATA_DIR):])
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

    def crawl_dir(self, path, exclude=[], include=None):
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
                        yield self.get_metadata(current)
                    except Exception as e:
                        logging.log(logging.ERROR, "Could not process %s (%s)" % (f, e)) 

    def get_metadata(self, filename):
        meta = utils.dict_merge({}, self.default, self.__extract_from_filename(filename))
        with Dataset(filename, 'r') as f:
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
        return meta
    
