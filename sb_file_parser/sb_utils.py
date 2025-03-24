from struct import unpack, pack


def read_char(fb):
    data = fb.read(1)
    if data == b'' or len(data) != 1:
        return None
    return unpack("B", data)[0]


def read_uint(fb):
    data = fb.read(4)
    if data == b'' or len(data) != 4:
        return None
    return unpack("I", data)[0]


def read_float(fb):
    data = fb.read(4)
    if data == b'' or len(data) != 4:
        return None
    return unpack("f", data)[0]


def read_ushort(fb):
    data = fb.read(2)
    print(f"0x{data.hex()}")
    if data == b'' or len(data) != 2:
        return None
    return unpack("H", data)[0]


def read_string(fb):
    str = b''
    while True:
        c = fb.read(1)
        if c == b'\0' or c == b'':
            return str.decode('cp437')
        else:
            str += c


def pack_uint(data):
    return pack(">I", data)


def pack_ushort(data):
    return pack(">H", data)
