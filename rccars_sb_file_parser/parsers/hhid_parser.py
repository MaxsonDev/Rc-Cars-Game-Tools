from ..sb_utils import read_char, read_uint, read_float, read_ushort, pack_uint, pack_ushort, pack_float


class HHID_parser:
    def __init__(self, fb, mod_obj, chunk, chunk_end, debug):
        self.fb = fb
        self.mod_obj = mod_obj
        self.chunk = chunk
        self.chunk_end = chunk_end
        self.debug = debug

    def parse_chunks(self):
        is_success = True
        # 3490h(**9034h) - хранит разрешение матрицы HHID. 3 значения - количество вокселей на каждую ось XZY.
        if self.chunk == 0x3490:
            # пропустим обязательный DWORD
            self.fb.read(4)
            data = []
            for _ in range(3):
                var = read_uint(self.fb)
                if self.debug:
                    d = {
                        'dec': var,
                        'hex': f"0x{pack_uint(var).hex()}"
                    }
                else:
                    d = var
                data.append(d)
            self.mod_obj.add_new_attribute('data_3490h', data)
        # 3093h(**9330h) - хранит общее количество MESH для расчета данных HHID.
        elif self.chunk == 0x3093:
            var = read_uint(self.fb)
            if self.debug:
                d = {
                    'dec': var,
                    'hex': f"0x{pack_uint(var).hex()}"
                }
            else:
                d = var
            self.mod_obj.add_new_attribute('data_3093h', d)
        # 8094h(**9480h) - весь MOD HHID состоит из большого количества чанков 8094h, поэтому будут храниться в списке.
        # Структура чанка:
        # 1. Первые 3 WORD(2 байта) - индексы("координаты") вокселя в матрице.
        # 2. Битовая маска. Длина битовой маски одинакова для всех 8094h, но отличается на разных картах в зависимости
        # от общего количества мешей. Длина данных рассчитывается по формуле: 3093h(MESH_COUNT) // 8 + 1
        # О принципе работы битовой маски можно посмотреть в coll_parser.py. Только вместо индексов полигонов(face),
        # битовая маска хранит биты для MESH. Значения: 1 - меш отображается, 0 - отключен.
        # P.S. Для справки, если какой мододел будет менять что-то с отрисовкой. Стоит учитывать, что работа
        # маски влияет и на дочерние MESH. Т.е., к примеру, у всех моделей есть родительский MESH с ID 0. Он главный и
        # в битовой маске занимает 1ое место. Если поменять 1ое значение маски с 1 на 0, то, при наезде на воксель,
        # вся карта будет исчезать, т.к. отключается родитель - отключаются дочерние,
        # и не важно какие у них значения 1 или 0.
        elif self.chunk == 0x8094:
            # берем индексы вокселя
            x_vox = read_ushort(self.fb)
            z_vox = read_ushort(self.fb)
            y_vox = read_ushort(self.fb)
            # берем макс длину вокселей по всем осям
            x_vox_length = self.mod_obj.data_3490h[0]['dec'] if self.debug else self.mod_obj.data_3490h[0]
            z_vox_length = self.mod_obj.data_3490h[1]['dec'] if self.debug else self.mod_obj.data_3490h[1]
            y_vox_length = self.mod_obj.data_3490h[2]['dec'] if self.debug else self.mod_obj.data_3490h[2]
            # Сверяем с условием
            if (x_vox >= 0 and x_vox < x_vox_length and \
                z_vox >= 0 and z_vox < z_vox_length and \
                y_vox >= 0 and y_vox < y_vox_length) is False:
                raise Exception(f"Wrong voxel index: {x_vox} {z_vox} {y_vox} (skip)")
            try:
                self.mod_obj.__getattribute__('data_8094h')
            except Exception:
                self.mod_obj.__setattr__('data_8094h', list())
            # так работает расчет длины данных для меша в оригинале.
            if self.debug:
                mesh_count = self.mod_obj.get_data_by_chunk('3093h')['dec'] // 8 + 1
            else:
                mesh_count = self.mod_obj.get_data_by_chunk('3093h') // 8 + 1
            data = [read_char(self.fb) for _ in range(mesh_count)]
            hhid_data = {
                "xzy_vox_point": [x_vox, z_vox, y_vox],
                "data": data
            }
            self.mod_obj.__getattribute__('data_8094h').append(hhid_data)
        # 7091h(**9170h) - чанк вызывает tiohbReadPoint3D. Создает 3D точку Point3D
        elif self.chunk == 0x7091:
            point3D = [read_float(self.fb) for _ in range(3)]
            self.mod_obj.add_new_attribute('data_7091h', point3D)
        # 7092h(**9270h) - чанк вызывает tiohbReadPoint3D. Создает 3D точку Point3D.
        elif self.chunk == 0x7092:
            point3D = [read_float(self.fb) for _ in range(3)]
            self.mod_obj.add_new_attribute('data_7092h', point3D)
        else:
            # может быть "баг". В неизвестные чанки может добавить неизвестный чанк из общих неизвестных чанков.
            try:
                self.mod_obj.__getattribute__('unknown_chunk')
            except Exception:
                self.mod_obj.__setattr__('unknown_chunk', list())
            self.mod_obj.__getattribute__('unknown_chunk').append(self.chunk)
            is_success = False
        return is_success
    