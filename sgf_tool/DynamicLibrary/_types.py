import numpy as np
import ctypes


class types:

    def __init__(self, name, type_mapping, callback):
        self.name = name
        self.type_mapping = type_mapping
        self.callback = callback

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def __call__(self, *args):
        return self.callback(*args)


c_void_p = ctypes.c_void_p
c_char_p = ctypes.c_char_p
c_bool = ctypes.c_bool
c_int8 = ctypes.c_int8
c_int16 = ctypes.c_int16
c_int32 = ctypes.c_int32
c_int64 = ctypes.c_int64
c_uint8 = ctypes.c_uint8
c_uint16 = ctypes.c_uint16
c_uint32 = ctypes.c_uint32
c_uint64 = ctypes.c_uint64
c_float = ctypes.c_float
c_double = ctypes.c_double

ct_int8_p = ctypes.POINTER(c_int8)
ct_int16_p = ctypes.POINTER(c_int16)
ct_int32_p = ctypes.POINTER(c_int32)
ct_int64_p = ctypes.POINTER(c_int64)
ct_uint8_p = ctypes.POINTER(c_uint8)
ct_uint16_p = ctypes.POINTER(c_uint16)
ct_uint32_p = ctypes.POINTER(c_uint32)
ct_uint64_p = ctypes.POINTER(c_uint64)
ct_float_p = ctypes.POINTER(c_float)
ct_double_p = ctypes.POINTER(c_double)

npint8arr = types('npint8arr', ct_int8_p,
                  lambda x: x.ctypes.data_as(ct_int8_p))
npint16arr = types('npint16arr', ct_int16_p,
                   lambda x: x.ctypes.data_as(ct_int16_p))
npint32arr = types('npint32arr', ct_int32_p,
                   lambda x: x.ctypes.data_as(ct_int32_p))
npint64arr = types('npint64arr', ct_int64_p,
                   lambda x: x.ctypes.data_as(ct_int64_p))
npuint8arr = types('npuint8arr', ct_uint8_p,
                   lambda x: x.ctypes.data_as(ct_uint8_p))
npuint16arr = types('npuint16arr', ct_uint16_p,
                    lambda x: x.ctypes.data_as(ct_uint16_p))
npuint32arr = types('npuint32arr', ct_uint32_p,
                    lambda x: x.ctypes.data_as(ct_uint32_p))
npuint64arr = types('npuint64arr', ct_uint64_p,
                    lambda x: x.ctypes.data_as(ct_uint64_p))
npfloatarr = types('npfloatarr', ct_float_p,
                   lambda x: x.ctypes.data_as(ct_float_p))
npdoublearr = types('npdoublearr', ct_double_p,
                    lambda x: x.ctypes.data_as(ct_double_p))

int8_p = types('int8*', ct_int8_p, lambda x: (c_int8 * len(x)).from_buffer(x))
uint8_p = types('uint8*', ct_uint8_p,
                lambda x: (c_uint8 * len(x)).from_buffer(x))

char_p = types('char*', c_char_p, c_char_p)
bool = types('bool', c_bool, c_bool)
int8 = types('int8', c_int8, c_int8)
int16 = types('int16', c_int16, c_int16)
int32 = types('int32', c_int32, c_int32)
int64 = types('int64', c_int64, c_int64)
uint8 = types('uint8', c_uint8, c_uint8)
uint16 = types('uint16', c_uint16, c_uint16)
uint32 = types('uint32', c_uint32, c_uint32)
uint64 = types('uint64', c_uint64, c_uint64)
float = types('float', c_float, c_float)
double = types('double', c_double, c_double)

void = types('void', None, None)
void_p = types('void*', c_void_p, c_void_p)
