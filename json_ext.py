from json import *
import zipopen

if zipopen.enable_resource_zip:
    open = zipopen.open

print("Load JSON parser")

_load = load
json_cache = {}
def load(file, arrays_to_tuples=True):
    params = (file, arrays_to_tuples)
    if params not in json_cache:
        this = _load(file)
        stack = [this]
        while stack:
            current = stack.pop()
            if isinstance(current, dict):
                for key in current:
                    if isinstance(current[key], dict):
                        stack.append(current[key])
                    elif isinstance(current[key], list):
                        if arrays_to_tuples:
                            current[key] = tuple(current[key])
        json_cache[params] = this
    return json_cache[params]

def loadf(filename, arrays_to_tuples=True):
    return load(open(filename, "r"), arrays_to_tuples)