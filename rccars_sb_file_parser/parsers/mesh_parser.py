from ..sb_utils import read_uint, read_float, read_ushort, pack_uint


class MESH_parser:
    """
    chunk и chunk_end передаются из метода SBFileParser.parse_mod()
    """
    def __init__(self, fb, mesh_mod, chunk, chunk_end):
        self.fb = fb
        self.mesh_mod = mesh_mod
        self.chunk = chunk
        self.chunk_end = chunk_end
        # for face
        self.face_list = []
        self.data_8218h = None

    def parse_chunks(self):
        is_success = True
        # 7411h(1174h) - чанк хранит информацию о вершинах(VERTEX). Имеет обязательный DWORD, указывающий количесвто вершин. 
        # Каждая вершина состоит из 3 FLOAT (XZY - координаты).
        if self.chunk == 0x7411:
            vertex_count = read_uint(self.fb)
            self.mesh_mod.vertex_count = vertex_count
            self.mesh_mod.vertex_list = [[read_float(self.fb) for _ in range(3)] for _ in range(vertex_count)]
        # 7413h(1374h) - чанк хранит информацию о UV разверстке. Имеет обязательный DWORD, указывающий 
        # количесвто координат развертки. Каждая координата состоит из 2 FLOAT. 
        elif self.chunk == 0x7413:
            tex_coords_count = read_uint(self.fb)
            self.mesh_mod.tex_coords_count = tex_coords_count
            self.mesh_mod.tex_coords_list = [[read_float(self.fb) for _ in range(2)] for _ in range(tex_coords_count)]
        # 0617h(1706h) - чанк инициализирует группу данных полигонов(FACE). 
        # Имеет обязательный DWORD, указывающий количество полигонов.
        elif self.chunk == 0x0617:
            face_count = read_uint(self.fb)
            self.mesh_mod.face_count = face_count
            for _ in range(face_count):
                chunk = read_ushort(self.fb)
                if chunk != 0x8218:
                    # оставлю оригиналньую ошибку
                    raise "Wrong SB file: MODB_FACE_ENTRY chunk expected 0x8218."
                self.parse_face_data()
            self.mesh_mod.face_list = self.face_list
        # 7029h(2970h) - чанк неизвестен. Вызывает tiohbReadPoint3D. Создает 3D точку.
        elif self.chunk == 0x7029:
            point3D = [read_float(self.fb) for _ in range(3)]
            self.mesh_mod.add_new_attribute('data_3DPoint_7029h', point3D)
        # 7030h(3070h) - чанк неизвестен. Вызывает tiohbReadPoint3D. Создает 3D точку.
        elif self.chunk == 0x7030:
            point3D = [read_float(self.fb) for _ in range(3)]
            self.mesh_mod.add_new_attribute('data_3DPoint_7030h', point3D)
        # 5438h(3854h) - чанк неизвестен. Есть обяязательный DWORD == 9.
        # Скорее всего связан с трансформацией объекта, судя по похожей структуре на чанк 540Bh.
        # Но на практике это не доказано. Ничего не меняется при изменении данных.
        elif self.chunk == 0x5438:
            # читаем общее количество флоат. Дб 9.
            float_count = read_uint(self.fb)
            if float_count != 9:
                raise 'Chunk 0x%08X: wrong length (9 expected, recive %i)'
            data = [[read_float(self.fb) for _ in range(3)] for _ in range(3)]
            self.mesh_mod.add_new_attribute('data_5438h', data)
        # 302Eh(2E30h) - чанк неизвестен. Вызывает tiohbReadDWord. Читает 4 байта данных.
        elif self.chunk == 0x302E:
            data = read_uint(self.fb)
            d = {
                'dec': data,
                'hex': f"0x{pack_uint(data).hex()}"
            }
            self.mesh_mod.add_new_attribute('data_302Eh', d)
        # 302Fh(2F30h) - чанк неизвестен. Вызывает tiohbReadDWord. Читает 4 байта данных.
        elif self.chunk == 0x302F:
            data = read_uint(self.fb)
            d = {
                'dec': data,
                'hex': f"0x{pack_uint(data).hex()}"
            }
            self.mesh_mod.add_new_attribute('data_302Fh', d)
        # 3031h(3130h) - чанк неизвестен. Вызывает tiohbReadDWord. Читает 4 байта данных.
        elif self.chunk == 0x3031:
            data = read_uint(self.fb)
            d = {
                'dec': data,
                'hex': f"0x{pack_uint(data).hex()}"
            }
            self.mesh_mod.add_new_attribute('data_3031h', d)
        else:
            is_success = False
        return is_success
    
    def parse_face_data(self):
        face_data = {}
        face_data_end_address = read_uint(self.fb)
        # количесвто вершин полигона?
        self.data_8218h = read_uint(self.fb)
        while True:
            chunk = read_ushort(self.fb)
            # *пропустим 4 байта адреса
            self.fb.read(4)
            # chunk_end = read_uint(self.fb)
            # 3419h(1934h) - чанк хранит точки("координаты") для отрисовки рёбер 1го полигона.
            if chunk == 0x3419:
                face_coords_count = read_uint(self.fb)
                if self.data_8218h != face_coords_count:
                    raise "ОШИБОЧКА. Количество вершин у полигона не равно значению в self.self.data_8218h."
                face_data["face_coords"] = [read_uint(self.fb) for _ in range(face_coords_count)]
            # 741Ah(1A74h) - чанк неизвестен. Есть обязательный DWORD. Сверяется с DWORD чанка 8218h(self.self.data_8218h)
            elif chunk == 0x741A:
                dword_741Ah = read_uint(self.fb)
                if self.data_8218h != dword_741Ah:
                    raise "ОШИБОЧКА. Количество вершин у полигона не равно значению в self.self.data_8218h."
                face_data['data_741Ah'] = [[read_float(self.fb) for _ in range(3)] for _ in range(dword_741Ah)]
            # 3020h(2030h) - чанк неивестен. Только вызывает tiohbReadDWord. Читает 4 байта данных.
            elif chunk == 0x3020:
                data = read_uint(self.fb)
                face_data['data_3020h'] = {
                    'dec': data,
                    'hex': f"0x{pack_uint(data).hex()}"
                }
            # 3025h(2530h) - чанк неивестен. Только вызывает tiohbReadDWord. Читает 4 байта данных.
            elif chunk == 0x3025:
                data = read_uint(self.fb)
                face_data['data_3025h'] = {
                    'dec': data,
                    'hex': f"0x{pack_uint(data).hex()}"
                }
            # 3022h(2230h) - чанк неивестен. Вызывает tiohbReadDWord. Читает 4 байта данных.
            elif chunk == 0x3022:
                data = read_uint(self.fb)
                face_data['data_3022h'] = {
                    'dec': data,
                    'hex': f"0x{pack_uint(data).hex()}"
                }
            # 7027h(2770h) - чанк неивестен. Вызывает tiohbReadPoint3D. Создает 3D точку. 3 FLOAT.
            elif chunk == 0x7027:
                point3D = [read_float(self.fb) for _ in range(3)]
                face_data['point3D_3DPoint_7027h'] = point3D
            # 063Ah(3A06h) - чанк неивестен. Хранит внутри себя другие чанки: 023Bh. Есть обязательный DWORD.
            elif chunk == 0x063A:
                list_023Bh = []
                dword_063Ah = read_uint(self.fb)
                for _ in range(dword_063Ah):
                    _chunk = read_ushort(self.fb)
                    if _chunk != 0x023B:
                        raise "ОШИБОЧКА"
                    data_023Bh = self.parse_data_group_023Bh()
                    list_023Bh.append(data_023Bh)
                face_data['data_063Ah'] = list_023Bh
                # face_data['data_063Ah'] = self.parse_data_group_023Bh()
                # face_data['group_data_063Ah']
            if face_data_end_address == self.fb.tell():
                break
        self.face_list.append(face_data)

    def parse_data_group_023Bh(self):
        chunk_end_023Bh = read_uint(self.fb)
        d = {}
        while True:
            chunk = read_ushort(self.fb)
            # *пропустим 4 байта адреса
            self.fb.read(4)
            # 303Ch(3C30h) - чанк неивестен. Только вызывает tiohbReadDWord. Читает 4 байта данных.
            if chunk == 0x303C:
                data = read_uint(self.fb)
                d['data_303Ch'] = {
                    'dec': data,
                    'hex': f"0x{pack_uint(data).hex()}"
                }
            # 303Dh(3D30h) - чанк неивестен. Только вызывает tiohbReadDWord. Читает 4 байта данных.
            elif chunk == 0x303D:
                data = read_uint(self.fb)
                d['data_303Dh'] = {
                    'dec': data,
                    'hex': f"0x{pack_uint(data).hex()}"
                }
            # 303Eh(3E30h) - чанк неивестен. Вызывает tiohbReadDWord. Читает 4 байта данных.
            elif chunk == 0x303E:
                data = read_uint(self.fb)
                d['data_303Eh'] = {
                    'dec': data,
                    'hex': f"0x{pack_uint(data).hex()}"
                }
            # 343Fh(3F34h) - чанк неивестен. Имеет обязательный DWORD. Сверяется с DWORD чанка 8218h(self.self.data_8218h).
            # DWORD показывает сколько INT значений в чанке. DWORD * 4 байта.
            elif chunk == 0x343F:
                dword_343Fh = read_uint(self.fb)
                if dword_343Fh != self.data_8218h:
                    raise "Wrong number of vertices in MODB_FACE_TEX_UVIND entry"
                data = [read_uint(self.fb) for _ in range(dword_343Fh)]
                d['data_343Fh'] = data

            if chunk_end_023Bh == self.fb.tell():
                break
        return d
    