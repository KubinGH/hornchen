def ease_in_out_cubic(time, start_value, value_increase, total_time):
    time /= total_time / 2
    if time < 1:
        return value_increase / 2 * time**3 + start_value
    else:
        return value_increase / 2 * ((time - 2)**3 + 2) + start_value

def ease_quintic_out(time, start_value, value_increase, total_time):
    time /= total_time
    return value_increase * ((time - 1) ** 5 + 1) + start_value