from ..sb_utils import read_char, read_uint, read_float, read_ushort, pack_uint, pack_ushort, pack_float


class COLL_parser:
    def __init__(self, fb, mod_obj, chunk, chunk_end, debug):
        self.fb = fb
        self.mod_obj = mod_obj
        self.chunk = chunk
        self.chunk_end = chunk_end
        self.debug = debug

    def parse_chunks(self):
        is_success = True
        # 3498h(**9834h) - хранит разрешение матрицы COLL. 3 значения - количество вокселей на каждую ось XZY.
        if self.chunk == 0x3498:
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
            self.mod_obj.add_new_attribute('data_3498h', data)
        # 309Eh(**9E30h) - хранит общее количество пересечений вокселями мешей.
        # Является суммой всех пересечений из чанка 809Dh и контрольной суммой для 809Ch и 349Fh.
        # Пример: допустим 456 воксель пересекается с 3 MESH. 457 воксель персекается с 1 MESH. Всего пересечений 4.
        # По такому принципу 309Eh хранит сумму пересечений ВСЕХ вокселей с MESH.
        elif self.chunk == 0x309E:
            var = read_uint(self.fb)
            if self.debug:
                d = {
                    'dec': var,
                    'hex': f"0x{pack_uint(var).hex()}"
                }
            else:
                d = var
            self.mod_obj.add_new_attribute('data_309Eh', d)
        # 809Dh(**9D80h) - хранит матрицу вокселей в линейном представлении.
        # Работает в связке с чанками 809Ch, 349Fh, 1500h. Каждый чанк хранит информацию о вертексе.
        # Как работает:
        # Допустим это линейная матрица 809Dh:
        # [0, 0, 0, 0, 1, 1, 0, 1, 2, 2, 2, ...].
        # Допустим это список MESH_ID 809Ch:
        # [0x91(145), 0x91(145), 0x91(145), 0x91(145), 0x34(52), 0x4(4), 0x34(52) ...]
        # Допустим это список фэйсов каждого MESH(MESH_FACE_COUNT) 349Fh:
        # [0x14(20), 0x14(20), 0x14(20), 0x14(20), 0x7(7), 0x78(120), 0x7(7) ...]
        # Допустим это список битовых масок 1500h:
        # [0x43, 0x0, 0x0, 0x2, 0x0, 0x0, 0x0, ...]
        # 1. В 809Dh первые 4 вокселя равны нулю. Они не пересекаются ни с одним MESH. 5ый воксель пересекается с 1 MESH.
        # По порядку от старта это первый воксель, у которого есть коллизия!!! Не смотря на то, что воксель с коллизией
        # находится на 5й позиции, он 1й, который имеет коллизию. Соответсвенно если он первый, то первые значения из
        # чанков 809Ch, 349Fh относится к вокселю на 5 позиции.
        # Значит 5ый воксель это MESH с ID 145(в 16-ой ситсеме 0x91) и количество его полигонов(FACE) равно 20(0x14).
        # 2. Если посмотреть на все ID 145 в 809Ch, то видно, что и следующие воксели пересекают MESH с ID 145.
        # Значит воксели 5, 6, 8, 9 пересекаются с MESH, у которого ID 145. Тоже самое и с MESH_FACE_COUNT в чанке 809Ch.
        # Так же 9ый воксель пересекает 2а MESH. По известной логике значит, что 9ый воксель
        # пересекает MESH с MESH_ID 145 и 52, у которых MESH_FACE_COUNT 20 и 7 соответственно.
        # 3. Такой же принцип работа с 1500h с небольшим отличием.
        # Чанк 1500h хранит битовые маски для включения коллизии у FACE. Что значит битовая маска?
        # Один бит это 0 - выкл коллизию или 1 - вкл коллизию. Один байт это восемь бит. Т.е. 1 байт == 0000 0000 бит.
        # Получается 1 байт может хранить информацию о коллизии от 0 до 8 FACE максимум.
        # За пример возьмем воксель 5 и MESH, который он пересекает. MESH имеет ID 145 и FACE_COUNT 20.
        # Считаем сколько байт занимает информацию о 20 FACE по формуле: (FACE_COUNT - 1) // 8 + 1
        # Получаем (20 - 1) // 8 + 1 == 3 байта.
        # Значит первые 3 значения(байта) [0x43, 0x0, 0x0] хранят информацию о всех FACE для MESH в 1ом вокселе.
        # Теперь переводим значения в битовую маску. Переведем число из 16-ой системы в 2-ый: 0x43 == 0100 0011.
        # Т.к. данные в .sb файле записаны "зеркально", то значение надо будет "отзеркалить".
        # Очевидно остальные 2 нуля равны нулям. Получаем: 1100 0010 0000 0000 0000 0000. Получили 24 битовых флага.
        # 4 последних бита "мертвые" и не учитываются, т.к. FACE имеет всего 20.
        # 24 флага получается потому что так работает математика. По итогу битовая маска хранит информацию о всех FACE.
        # Считаем индексы FACE слева направо. Исходя из примера, если машинка въедет в зону 5го вокселя,
        # то коллизия включится у 3х FACE с индексом: 0, 1, 6.
        # 4. Можно обратить внимание, что 6ой воксель является тем же MESH с тем же ID и тем же FACE_COUNT, но маска
        # будет иметь уже другие значения! А именно, зная что информация о 20 FACE занимает 3 байта,
        # то теперь маска для следующего вокселя будет такой: [0x2, 0x0, 0x0].
        # Переведем 2 в двоичную систему: 0x2 == 0000 0010. Не забудем "отзеркалить".
        # Маска: 0100 0000 0000 0000 0000 0000. Получается, когда машинка пересекает 6ой воксель, то у MESH с ID 145
        # уже будет включаться коллизия на полигоне(face) с индексом 1.
        elif self.chunk == 0x809D:
            if self.debug:
                _vars = [v['dec'] for v in self.mod_obj.data_3498h]
                control_var = self.mod_obj.data_309Eh['dec']
            else:
                _vars = self.mod_obj.data_3498h
                control_var = self.mod_obj.data_309Eh
            data = []
            counter = _vars[0] * _vars[1] * _vars[2]
            control_sum = 0
            for _ in range(counter):
                v = read_ushort(self.fb)
                control_sum += v
                data.append(v)
            if control_sum != control_var:
                # оригинальная ошибка
                raise Exception(f'Wrong chunk MODB_COLL_STARTVOX length ({f"0x{pack_uint(control_var).hex()}"} expected, {f"0x{pack_uint(control_sum).hex()}"} read)')
            self.mod_obj.add_new_attribute('data_809Dh', data)
        # 809Ch(9C80h) - хранит список MESH_ID. Подробнее об этом чанке смотри в 809Dh.
        elif self.chunk == 0x809C:
            try:
                if len(self.mod_obj.data_809Dh) == 0:
                    # оригинальная ошибка
                    raise Exception('Unexpected chunk MODB_COLL_VOXNMB (MODB_COLL_STARTVOX chunk expec)')
            except Exception as error:
                raise error
            data = []
            if self.debug:
                control_var = self.mod_obj.data_309Eh['dec']
            else:
                control_var = self.mod_obj.data_309Eh
            for _ in range(control_var):
                var = read_ushort(self.fb)
                if self.debug:
                    d = {
                        'dec': var,
                        'hex': f"0x{pack_ushort(var).hex()}"
                    }
                else:
                    d = var
                data.append(d)
            self.mod_obj.add_new_attribute('data_809Ch', data)
        # 349Fh(9F34h) - хранит список MESH_FACE_COUNT. Подробнее об этом чанке смотри в 809Dh.
        elif self.chunk == 0x349F:
            if self.debug:
                control_var = self.mod_obj.data_309Eh['dec']
            else:
                control_var = self.mod_obj.data_309Eh
            dword_var = read_uint(self.fb)
            if dword_var != control_var:
                # оригинальная ошибка
                raise Exception(f'Wrong chunk MODB_COLL_NFACE_PEROBJ size ({f"0x{pack_uint(control_var).hex()}"} expected, {f"0x{pack_uint(dword_var).hex()}"} read)')
            data = []
            for _ in range(dword_var):
                var = read_uint(self.fb)
                if self.debug:
                    d = {
                        'dec': var,
                        'hex': f"0x{pack_uint(var).hex()}"
                    }
                else:
                    d = var
                data.append(d)
            self.mod_obj.add_new_attribute('data_349Fh', data)
        # 1500h(0015h) - хранит список битовых масок для каждого FACE. Подробнее об этом чанке смотри в 809Dh.
        elif self.chunk == 0x1500:
            try:
                if bool(self.mod_obj.data_309Eh) is False:
                    # оригинальная ошибка
                    raise Exception('Wrong chunk MODB_COLL_PERFACE_INFO nObj info')
                if len(self.mod_obj.data_349Fh) == 0:
                    # оригинальная ошибка
                    raise Exception('Wrong chunk MODB_COLL_PERFACE_INFO: MODB_COLL_NFACE_PEROBJ expect')
            except Exception as error:
                raise error
            dword_var = read_uint(self.fb)
            data = []
            for _ in range(dword_var):
                var = read_char(self.fb)
                if self.debug:
                    d = {
                        'dec': var,
                        'hex': f"0x{pack_uint(var).hex()}"
                    }
                else:
                    d = var
                data.append(d)
            self.mod_obj.add_new_attribute('data_1500h', data)
            if self.debug:
                return
            # Берем контрольное значение из 309Eh
            var_309Eh = self.mod_obj.data_309Eh
            # Берем массив данных их 349Fh.
            data_349Fh = self.mod_obj.data_349Fh
            # создадим counter
            counter = 0
            # создадим control_sum
            control_sum = 0
            while True:
                # берет элемент из массива 349Fh
                el_349Fh = data_349Fh[counter]
                # отнимаем 1
                el_349Fh -= 1
                # делаем смещение(shr - ассемблер) на 3
                el_349Fh = el_349Fh >> 3
                # суммируем результат с суммой и прибавляем 1
                control_sum = control_sum + el_349Fh + 1
                # обновляем счетчик
                counter += 1
                if var_309Eh == counter:
                    break
            if control_sum != dword_var:
                # оригинальная ошибка
                raise Exception(f"Wrong chunk MODB_COLL_PERFACE_INFO length ({dword_var} expected, {control_sum} read)")
        # 7099h(9970h) - чанк неизвестен. Вызывает tiohbReadPoint3D. Создает 3D точку.
        # Является стартовой точкой для создания матрицы.
        # Вместе с 709Ah создает зону для расчета машинки в пространстве матрицы.
        elif self.chunk == 0x7099:
            point3D = [read_float(self.fb) for _ in range(3)]
            self.mod_obj.add_new_attribute('data_7099h', point3D)
        # 709Ah(9A70h) - чанк неизвестен. Вызывает tiohbReadPoint3D. Создает 3D точку.
        # Вместе с 7099h создает зону для расчета машинки в пространстве матрицы.
        elif self.chunk == 0x709A:
            point3D = [read_float(self.fb) for _ in range(3)]
            self.mod_obj.add_new_attribute('data_709Ah', point3D)
        else:
            # может быть "баг". В неизвестные чанки может добавить неизвестный чанк из общих неизвестных чанков.
            try:
                self.mod_obj.__getattribute__('unknown_chunk')
            except Exception:
                self.mod_obj.__setattr__('unknown_chunk', list())
            self.mod_obj.__getattribute__('unknown_chunk').append(self.chunk)
            is_success = False
        return is_success
from ..sb_utils import read_uint, read_float, read_ushort, pack_uint, pack_ushort, pack_float


class COLL_parser:
    """
    chunk и chunk_end передаются из метода SBFileParser.parse_mod()
    """
    def __init__(self, fb, mod_obj, chunk, chunk_end):
        self.fb = fb
        self.mod_obj = mod_obj
        self.chunk = chunk
        self.chunk_end = chunk_end

    def parse_chunks(self):
        is_success = True
        # 3498h(9834h) - чанк неизвестен. Вызывает tiohbReadDWord 3 раза. Хранит 3 "переменные", которые используются в последубщих чанках.
        if self.chunk == 0x3498:
            # пропустим обязательный DWORD
            self.fb.read(4)
            _vars = []
            for _ in range(3):
                var = read_uint(self.fb)
                d = {
                    'dec': var,
                    'hex': f"0x{pack_uint(var).hex()}"
                }
                _vars.append(d)
            self.mod_obj.add_new_attribute('vars_3498h', _vars)
        # 309Eh(9E30h) - чанк неизвестен. Вызывает tiohbReadDWord. Хранит количесвто едениц для коллизий? VOX - воксели?
        elif self.chunk == 0x309E:
            var = read_uint(self.fb)
            d = {
                'dec': var,
                'hex': f"0x{pack_uint(var).hex()}"
            }
            self.mod_obj.add_new_attribute('var_309Eh', d)
        return is_success
