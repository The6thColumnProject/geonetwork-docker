from copy import deepcopy

def dict_merge(target, *all_dicts):
    """Merge multiple dictionaries (list in all_dicts) together into target and returns it.
    To merge into new one just call it: dict_merge({}, dict1, dict2, ...)"""
    for some_dict in all_dicts:
        if not isinstance(some_dict, dict):
            return some_dict

        for k, v in some_dict.iteritems():
            if k in target and isinstance(target[k], dict):
                dict_merge(target[k], v)
            else:
                target[k] = deepcopy(v)

    return target

def rename_keys(target, rename_dict):
    """Rename the keys of a dictionary with those from another one"""
    if not isinstance(target, dict):
        return target
    
    for k,v in [(k,v) for k,v in target.iteritems() if k in rename_dict]:
        if k in rename_dict:
            if isinstance(rename_dict[k], dict):
                #recurse
                rename_keys(target[k], rename_dict[k])
            else:
                #rename
                if rename_dict[k] in target:
                    raise Exception("Cannot rename property %s to %s as the later already exists" % (k, rename_dict[k])) 
                target[rename_dict[k]] = target[k]
                del target[k]
    return target 
    
