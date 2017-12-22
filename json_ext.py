import json
import zipopen
import ast

from pygame import Rect # for encoding/decoding

from utils import Register

if zipopen.enable_resource_zip:
    open = zipopen.open

print("Load JSON parser")

json_cache = {}
def loads(string, arrays_to_tuples=True, register_aware=True, **kwargs):
    params = (string, arrays_to_tuples)
    if params not in json_cache:
        this = json.loads(string, **kwargs)
        # Analyze the input and apply fixes
        stack = [this]
        arrays_to_convert = [] # arrays to tuples memo
        while stack:
            current = stack.pop()
            if isinstance(current, (tuple, list)):
                citer = range(len(current))
            else:
                citer = current
                # Convert all keys to integers (if possible), tuples etc.
                # since JSON doesn't allow number keys - only strings
                for k, v in current.items():
                    try:
                        ast.literal_eval(k)
                    except (ValueError, SyntaxError):
                        pass
                    else:
                        del current[k]
                        current[ast.literal_eval(k)] = v
            for key in citer:
                if isinstance(current[key], dict):
                    if register_aware and "register_name" in current[key] and "name" in current[key]:
                        rname, name = current[key]["register_name"], current[key]["name"]
                        current[key] = Register.registers[rname][name]
                    else:
                        stack.append(current[key])
                elif isinstance(current[key], (tuple, list)):
                    if arrays_to_tuples:
                        arrays_to_convert.append((current, key))
                    stack.append(current[key])

        for a, b in arrays_to_convert:
            a[b] = tuple(a[b])
        json_cache[params] = this
    return json_cache[params]

def load(file, **kwargs):
    return loads(file.read(), **kwargs)

def loadf(filename, **kwargs):
    return load(open(filename, "r"), **kwargs)


# Used to encode types to their name and the name of the
# utils.Register to which the belong.
class JSONExtEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, type):
            return {"register_name": obj.in_register_name, "name": obj.__name__}
        else:
            return super().default(obj)

def dumps(dictionary, type_to_register_id=True, **kwargs):
    stack = [dictionary]
    while stack:
        current = stack.pop()
        for key, value in current.items():
            # Convert lists/tuples to their string represantations
            if isinstance(key, (list, tuple)):
                del current[key]
                current[str(key)] = value
            if isinstance(value, dict):
                stack.append(value)
    return json.dumps(dictionary, cls=JSONExtEncoder, **kwargs)

def dump(file, **kwargs):
    return dumps(file.read(), **kwargs)

def dumpf(filename, **kwargs):
    return dump(open(filename, "r"), **kwargs)