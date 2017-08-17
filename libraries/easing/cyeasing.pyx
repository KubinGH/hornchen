import math


cpdef double ease_linear(double time, double start_value, double value_increase, double total_time) except *:
     return value_increase * (time / total_time) + start_value

cpdef double ease_in_out_cubic(double time, double start_value, double value_increase, double total_time) except *:
    time /= total_time / 2
    if time < 1:
        return value_increase / 2 * time**3 + start_value
    else:
        return value_increase / 2 * ((time - 2)**3 + 2) + start_value

cpdef double ease_quintic_out(double time, double start_value, double value_increase, double total_time) except *:
    return value_increase * ((time / total_time - 1) ** 5 + 1) + start_value

cpdef double ease_circular_in(double time, double start_value, double value_increase, double total_time) except *:
    return -value_increase * (math.sqrt(1 - (time / total_time) ** 2) - 1) + start_value

cpdef double ease_value_sum(object ease, double start_value, double value_increase, int total_time) except *:
    cdef double result = 0
    for time in range(total_time + 1):
        result += ease(time, start_value, value_increase, total_time)
    return result

cpdef double ease_value_sum_fm(object ease, double max_value, double start_value, double value_increase, int total_time, int app=1) except *:
    cdef double result = 0
    for time in range(1, total_time + 1, app):
        result += max_value - ease(time, start_value, value_increase, total_time)
    return result * app