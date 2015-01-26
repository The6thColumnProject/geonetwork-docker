from copy import deepcopy

def dict_merge(target, *all_dicts):
    for some_dict in all_dicts:
        if not isinstance(some_dict, dict):
            return some_dict

        for k, v in some_dict.iteritems():
            if k in target and isinstance(target[k], dict):
                dict_merge(target[k], v)
            else:
                target[k] = deepcopy(v)

    return target
