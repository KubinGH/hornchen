import _random

"""
Cython module cyrandom
Wraps _random.Random and provides functions
that should replicate those of module random
"""

_inst = _random.Random()
getrandbits = _inst.getrandbits
random = _inst.random

cdef int c_randbelow(int n):
    cdef int k, r
    if n == 0: return 0
    k = n.bit_length()
    r = getrandbits(k)
    while r >= n:
        r = getrandbits(k)
    return r

cdef int c_randint(int a, int b):
    return c_randbelow(b) + a            

cdef void c_shuffle(list x):
    cdef int i, j
    for i in reversed(range(1, len(x))):
        j = c_randbelow(i+1)
        x[i], x[j] = x[j], x[i]