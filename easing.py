import math

print("Load easing")

def ease_linear(time, start_value, value_increase, total_time):
    return value_increase * (time / total_time) + start_value

def ease_in_out_cubic(time, start_value, value_increase, total_time):
    time /= total_time / 2
    if time < 1:
        return value_increase / 2 * time**3 + start_value
    else:
        return value_increase / 2 * ((time - 2)**3 + 2) + start_value

def ease_quintic_out(time, start_value, value_increase, total_time):
    return value_increase * ((time / total_time - 1) ** 5 + 1) + start_value

def ease_circular_in(time, start_value, value_increase, total_time):
    return -value_increase * (math.sqrt(1 - (time / total_time) ** 2) - 1) + start_value

def ease_value_sum(ease, start_value, value_increase, total_time):
    result = 0
    for time in range(total_time + 1):
        if ease == ease_quintic_out:
            result += max_value - value_increase * ((time / total_time - 1) ** 5 + 1) + start_value
        else:
            result += ease(time, start_value, value_increase, total_time)
    return result

def ease_value_sum_fm(ease, max_value, start_value, value_increase, total_time, app=1):
    result = 0
    for time in range(1, total_time + 1, app):
        if ease == ease_quintic_out:
            result += max_value - value_increase * ((time / total_time - 1) ** 5 + 1) + start_value
        else:
            result += max_value - ease(time, start_value, value_increase, total_time)
    return result * app

try:
    from libraries.easing import cyeasing
except ImportError:
    optimized = None
    print("[easing]::Failed to import Cython easing")
else:
    print("[easing]::Imported Cython easing, optimizing: ", end="")
    optimized = {}
    for k in dir(cyeasing):
        if k.startswith("_"): continue
        print(k, end=", ")
        optimized[k] = locals()[k]
        locals()[k] = getattr(cyeasing, k)
    print("Done")