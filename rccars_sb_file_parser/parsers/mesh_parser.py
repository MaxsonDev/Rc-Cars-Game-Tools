from ..sb_utils import read_uint, read_float, read_ushort, pack_uint, pack_float


class MESH_parser:
    def __init__(self, fb, mod_obj, chunk, chunk_end, debug):
        self.fb = fb
        self.mod_obj = mod_obj
        self.chunk = chunk
        self.chunk_end = chunk_end
        self.debug = debug

        self.face_list = []
        self.data_8218h = None

    def parse_chunks(self):
        is_success = True
        # 7411h(**1174h) - хранит информацию о вершинах(VERTEX) меша.
        # Имеет обязательный DWORD, хранящий количество вершин.
        # Каждая вершина состоит из 3 FLOAT (XZY - координаты).
        if self.chunk == 0x7411:
            vertex_count = read_uint(self.fb)
            vertex_list = [[read_float(self.fb) for _ in range(3)] for _ in range(vertex_count)]
            self.mod_obj.add_new_attribute('data_7411h', vertex_list)
        # 7413h(1374h) - хранит информацию о UV разверстке.
        # Имеет обязательный DWORD, указывающий количество координат развертки.
        # Каждая координата состоит из 2 FLOAT.
        elif self.chunk == 0x7413:
            tex_coords_count = read_uint(self.fb)
            tex_coords_list = [[read_float(self.fb) for _ in range(2)] for _ in range(tex_coords_count)]
            self.mod_obj.add_new_attribute('data_7413h', tex_coords_list)
        # 7414h(1474h) - чанк вызывает tiohbReadPoint3D. Создает две 3D точки Point3D.
        elif self.chunk == 0x7414:
            # Пропускаем обязательный DWORD, указывающее кол-во Point3D. Значение всегда равно 2.
            self.fb.read(4)
            point3D_list = [[read_float(self.fb) for _ in range(3)] for _ in range(2)]
            self.mod_obj.add_new_attribute('data_7414h', point3D_list)
        # 0617h(1706h) - чанк инициализирует группу блоков данных полигонов(FACE).
        # Имеет обязательный DWORD, хранящий количество блоков данных полигонов.
        elif self.chunk == 0x0617:
            face_count = read_uint(self.fb)
            for _ in range(face_count):
                chunk = read_ushort(self.fb)
                if chunk != 0x8218:
                    # оригинальная ошибка
                    raise Exception("Wrong SB file: MODB_FACE_ENTRY chunk expected 0x8218.")
                self.parse_face_data()
            self.mod_obj.add_new_attribute('data_0617h', self.face_list)
        # 7029h(2970h) - чанк вызывает tiohbReadPoint3D. Создает 3D точку Point3D.
        elif self.chunk == 0x7029:
            point3D = [read_float(self.fb) for _ in range(3)]
            self.mod_obj.add_new_attribute('data_7029h', point3D)
        # 7030h(3070h) - чанк вызывает tiohbReadPoint3D. Создает 3D точку Point3D.
        elif self.chunk == 0x7030:
            point3D = [read_float(self.fb) for _ in range(3)]
            self.mod_obj.add_new_attribute('data_7030h', point3D)
        # 5438h(3854h) - чанк неизвестен. Есть обязательный DWORD == 9.
        # Скорее всего связан с трансформацией объекта, судя по похожей структуре на чанк 540Bh.
        elif self.chunk == 0x5438:
            float_count = read_uint(self.fb)
            if float_count != 9:
                # оригинальная ошибка
                raise Exception('Chunk 0x%08X: wrong length (9 expected, recive %i)')
            data = [[read_float(self.fb) for _ in range(3)] for _ in range(3)]
            self.mod_obj.add_new_attribute('data_5438h', data)
        # 302Eh(2E30h) - чанк неизвестен. Вызывает tiohbReadDWord. Читает 4 байта данных.
        elif self.chunk == 0x302E:
            var = read_uint(self.fb)
            if self.debug:
                d = {
                    'dec': var,
                    'hex': f"0x{pack_uint(var).hex()}"
                }
            else:
                d = var
            self.mod_obj.add_new_attribute('data_302Eh', d)
        # 302Fh(2F30h) - чанк неизвестен. Вызывает tiohbReadDWord. Читает 4 байта данных.
        elif self.chunk == 0x302F:
            var = read_uint(self.fb)
            if self.debug:
                d = {
                    'dec': var,
                    'hex': f"0x{pack_uint(var).hex()}"
                }
            else:
                d = var
            self.mod_obj.add_new_attribute('data_302Fh', d)
        # 3031h(3130h) - чанк неизвестен. Вызывает tiohbReadDWord. Читает 4 байта данных.
        elif self.chunk == 0x3031:
            var = read_uint(self.fb)
            if self.debug:
                d = {
                    'dec': var,
                    'hex': f"0x{pack_uint(var).hex()}"
                }
            else:
                d = var
            self.mod_obj.add_new_attribute('data_3031h', d)
        # 8215h(1582h) - чанк хранит вершины невидимой геометрической фигуры,
        # которая является "зоной отрисовки" меша. Если фигуру переместить или переместить меш за пределы фигуры,
        # то меш будет исчезать при приближении. При этом, если переместить и куб и меш далеко от станадртного положения,
        # то, меш исчезает. Скорее всего из-за того, что выходит за границу триггера-вокселя HHID.
        # Чанк вызывает tiohbReadFloat. Читает 10 раз FLOAT значения.
        # Первые 2 FLOAT - это 2е Z координаты: Zв - верхняя и Zн - нижняя точки.
        # Вторые 4 по 2 FLOAT - X и Y координаты. Из каждой группы XY вместе c Z значениями создаются координаты
        # "верхнего и нижнего ряда" вершин. Т.е. X1ZвY1, X1ZнY1 X2ZвY2, X2ZнY2, X3ZвY3, X3ZнY3, X4ZвY4, X4ZнY4.
        # Из этих точек и создается "геометрическая фигура". По этим координатам рассчитывается отображение меша.
        elif self.chunk == 0x8215:
            data = []
            for _ in range(10):
                var = read_float(self.fb)
                if self.debug:
                    d = {
                        'dec': var,
                        'hex': f"0x{pack_float(var).hex()}"
                    }
                else:
                    d = var
                data.append(d)
            self.mod_obj.add_new_attribute('data_8215h', data)                
        # 8216h(1682h) - чанк хранит невидимый куб, который является "зоной коллизии". Если куб переместить 
        # или переместить меш за пределы куба, то коллизия исчезает. Если сместить куб немного в сторону от меша,
        # то та часть, которая попадает в куб, будет иметь коллизию, а другая часть нет.
        # Чанк читает tiohbReadFloat, потом tiohbReadPoint3D.
        # FLOAT является масштабом куба по всем осям масштабирования. Point3D является центральной точкой куба.
        elif self.chunk == 0x8216:
            data = read_float(self.fb)
            point3D = [read_float(self.fb) for _ in range(3)]
            d = {
                'float': data,
                '3DPoint': point3D
            }
            self.mod_obj.add_new_attribute('data_8216h', d)
        else:
            # может быть "баг". В неизвестные чанки может добавить неизвестный чанк из общих неизвестных чанков.
            try:
                self.mod_obj.__getattribute__('unknown_chunk')
            except Exception:
                self.mod_obj.__setattr__('unknown_chunk', list())
            self.mod_obj.__getattribute__('unknown_chunk').append(self.chunk)
            is_success = False
        return is_success
    
    def parse_face_data(self):
        face_data = {}
        face_data_end_address = read_uint(self.fb)
        self.data_8218h = read_uint(self.fb)
        while True:
            chunk = read_ushort(self.fb)
            # *пропустим 4 байта адреса
            self.fb.read(4)
            # 3419h(1934h) - хранит индексы вершин(VERTEX) для отрисовки 1го полигона.
            if chunk == 0x3419:
                face_coords_count = read_uint(self.fb)
                if self.data_8218h != face_coords_count:
                    raise Exception("ОШИБКА. Количество вершин у полигона не равно значению в self.data_8218h.")
                face_data["data_3419h"] = [read_uint(self.fb) for _ in range(face_coords_count)]
            # 741Ah(1A74h) - чанк неизвестен. Есть обязательный DWORD. Сверяется с DWORD чанка 8218h(self.self.data_8218h)
            elif chunk == 0x741A:
                dword_741Ah = read_uint(self.fb)
                if self.data_8218h != dword_741Ah:
                    raise Exception("ОШИБКА. Количество вершин у полигона не равно значению в self.data_8218h.")
                face_data['data_741Ah'] = [[read_float(self.fb) for _ in range(3)] for _ in range(dword_741Ah)]
            # 3020h(2030h) - чанк неивестен. Только вызывает tiohbReadDWord. Читает 4 байта данных.
            elif chunk == 0x3020:
                var = read_uint(self.fb)
                if self.debug:
                    d = {
                        'dec': var,
                        'hex': f"0x{pack_uint(var).hex()}"    
                    }
                else:
                    d = var
                face_data['data_3020h'] = d
            # 3025h(2530h) - чанк неивестен. Только вызывает tiohbReadDWord. Читает 4 байта данных.
            elif chunk == 0x3025:
                var = read_uint(self.fb)
                if self.debug:
                    d = {
                        'dec': var,
                        'hex': f"0x{pack_uint(var).hex()}"    
                    }
                else:
                    d = var
                face_data['data_3025h'] = d
            # 3022h(2230h) - чанк неивестен. Вызывает tiohbReadDWord. Читает 4 байта данных.
            elif chunk == 0x3022:
                var = read_uint(self.fb)
                if self.debug:
                    d = {
                        'dec': var,
                        'hex': f"0x{pack_uint(var).hex()}"    
                    }
                else:
                    d = var
                face_data['data_3022h'] = d
            # 7027h(2770h) - чанк вызывает tiohbReadPoint3D. Создает 3D точку Point3D.
            elif chunk == 0x7027:
                point3D = [read_float(self.fb) for _ in range(3)]
                face_data['data_7027h'] = point3D
            # 063Ah(3A06h) - чанк хранит группу данных. Хранит внутри себя чанки 023Bh.
            # Есть обязательный DWORD, который хранит количество блоков данных.
            elif chunk == 0x063A:
                list_023Bh = []
                dword_063Ah = read_uint(self.fb)
                for _ in range(dword_063Ah):
                    _chunk = read_ushort(self.fb)
                    if _chunk != 0x023B:
                        raise Exception("ОШИБКА в чанке MESH_063Ah")
                    data_023Bh = self.parse_data_group_023Bh()
                    list_023Bh.append(data_023Bh)
                face_data['data_063Ah'] = list_023Bh
            if face_data_end_address == self.fb.tell():
                break
        self.face_list.append(face_data)

    def parse_data_group_023Bh(self):
        chunk_end_023Bh = read_uint(self.fb)
        data = {}
        while True:
            chunk = read_ushort(self.fb)
            # *пропустим 4 байта адреса
            self.fb.read(4)
            # 303Ch(3C30h) - чанк неивестен. Только вызывает tiohbReadDWord. Читает 4 байта данных.
            if chunk == 0x303C:
                var = read_uint(self.fb)
                if self.debug:
                    d = {
                        'dec': var,
                        'hex': f"0x{pack_uint(var).hex()}"
                    }
                else:
                    d = var
                data['data_303Ch'] = d
            # 303Dh(3D30h) - чанк неивестен. Вызывает tiohbReadDWord. Читает 4 байта данных.
            elif chunk == 0x303D:
                var = read_uint(self.fb)
                if self.debug:
                    d = {
                        'dec': var,
                        'hex': f"0x{pack_uint(var).hex()}"
                    }
                else:
                    d = var
                data['data_303Dh'] = d
            # 303Eh(3E30h) - чанк неивестен. Вызывает tiohbReadDWord. Читает 4 байта данных.
            elif chunk == 0x303E:
                var = read_uint(self.fb)
                if self.debug:
                    d = {
                        'dec': var,
                        'hex': f"0x{pack_uint(var).hex()}"
                    }
                else:
                    d = var
                data['data_303Eh'] = d
            # 343Fh(3F34h) - чанк неивестен. Имеет обязательный DWORD. Сверяется с DWORD чанка 8218h(self.self.data_8218h).
            # DWORD показывает сколько INT значений в чанке. DWORD * 4 байта.
            elif chunk == 0x343F:
                dword_343Fh = read_uint(self.fb)
                if dword_343Fh != self.data_8218h:
                    # оригинальная ошибка
                    raise Exception("Wrong number of vertices in MODB_FACE_TEX_UVIND entry")
                d = [read_uint(self.fb) for _ in range(dword_343Fh)]
                data['data_343Fh'] = d

            if chunk_end_023Bh == self.fb.tell():
                break
        return data
    
