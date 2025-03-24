from sb_utils import read_uint, read_float


def MESH_parser(fb, mesh_mod, chunk):
    is_success = True
    # 7411h(**1174h) - чанк хранит координаты вершин меша.
    if chunk == 0x7411:
        vertex_count = read_uint(fb)
        mesh_mod.vertex_count = vertex_count
        mesh_mod.vertex_list = [[read_float(fb) for _ in range(3)] for _ in range(vertex_count)]
    else:
        is_success = False
    return is_success

