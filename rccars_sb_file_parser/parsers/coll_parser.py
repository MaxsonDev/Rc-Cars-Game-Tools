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
        # 809Dh(9D80h) - чанк неизвестен. Перемножает 3и значения из 3498h == длина данных. Один чанк данных - 2 байта. Использует HeapAlloc.
        # При каждой итерации значение итерации суммируется с прошлым значением. Сумма дб равна значению из 309Eh.
        # Если сумма не равна значению 309Eh, то выдается ошибка 'Wrong chunk MODB_COLL_STARTVOX length (%i expected, %i read)'. 
        elif self.chunk == 0x809D:
            data = []
            _vars = [v['dec'] for v in self.mod_obj.vars_3498h]
            counter = _vars[0] * _vars[1] * _vars[2]
            control_sum = 0
            control_var = self.mod_obj.var_309Eh['dec']
            for _ in range(counter):
                v = read_ushort(self.fb)
                control_sum += v
                data.append(v)
            if control_sum != control_var:
                raise f'Wrong chunk MODB_COLL_STARTVOX length ({f"0x{pack_uint(control_var).hex()}"} expected, {f"0x{pack_uint(control_sum).hex()}"} read)'
            self.mod_obj.add_new_attribute('data_809Dh', data)
        # 809Ch(9C80h) - чанк неизвестен. Если правильно понял, то делает булевую проверку - есть ли данные в чанке 809Dh. Если данных нет, то выдает ошибку:
        # 'Unexpected chunk MODB_COLL_VOXNMB (MODB_COLL_STARTVOX chunk expec)'. 
        # Если данные в чанке 809Dh есть, то берется значение из чанка 309Eh - оно используется 
        # для итерации данных. Один чанк данных равен 2 байта.
        # UPD1: не понимаю что проверяется. Судя по ошибке ожидается чанк MODB_COLL_STARTVOX, 
        # но судя по коду передается указатель на выделенную память под 809Ch, 
        # но при этом никаких данных в этом блоке нет.
        # СКОРЕЕ ВСЕГО В ЭТОМ ЧАНКЕ ХРАНЯТСЯ ID МЕШЕЙ.
        elif self.chunk == 0x809C:
            # Проверяем наличие чанка 809Dh и есть ли в нем данны.
            try:
                if len(self.mod_obj.data_809Dh) == 0:
                    raise Exception('Unexpected chunk MODB_COLL_VOXNMB (MODB_COLL_STARTVOX chunk expec)')
            except Exception as error:
                raise error
            
            data = []
            control_var = self.mod_obj.var_309Eh['dec']
            for _ in range(control_var):
                i = read_ushort(self.fb)
                d = {
                    'dec': i,
                    'hex': f"0x{pack_ushort(i).hex()}"
                }
                data.append(d)
            self.mod_obj.add_new_attribute('data_809Ch', data)
        # 349Fh(9F34h) - чанк неизвестен. Имеет обязательный DWORD, который сверяется со значением из чанка 309Eh. 
        # Если значения не равны, вызовется ошибка: 'Wrong chunk MODB_COLL_NFACE_PEROBJ size (%i expected, %i read)'. 
        # Данные итерируются обязательным DWORD. Один чанк данных равен 4 байта.
        elif self.chunk == 0x349F:
            control_var = self.mod_obj.var_309Eh['dec']
            dword_var = read_uint(self.fb)
            if dword_var != control_var:
                raise Exception(f'Wrong chunk MODB_COLL_NFACE_PEROBJ size ({f"0x{pack_uint(control_var).hex()}"} expected, {f"0x{pack_uint(dword_var).hex()}"} read)')
            data = []
            for _ in range(dword_var):
                i = read_uint(self.fb)
                d = {
                    'dec': i,
                    'hex': f"0x{pack_uint(i).hex()}"
                }
                data.append(d)
            self.mod_obj.add_new_attribute('data_349Fh', data)
        # 1500h(0015h) - чанк неизвестен. Имеет обязательный DWORD, показывающий длину данных. Длина одного чанка данных 1 байт. 
        # 1. Проводит булевую проверку. Есть ли значения в чанке 349Eh. Если данных нет, то выдает ошибку: 
        # 'Wrong chunk MODB_COLL_PERFACE_INFO nObj info'.
        # 2. Проводит булевую проверку. Есть ли указатель на данные чанка 349Fh. Если данных нет, то выдает ошибку: 
        # 'Wrong chunk MODB_COLL_PERFACE_INFO: MODB_COLL_NFACE_PEROBJ expect'.
        elif self.chunk == 0x1500:
            """
            try:
                # 1я проверка так же булевая. Есть ли чанк 309Eh
                if bool(self.mod_obj.var_309Eh) is False:
                    raise Exception('Wrong chunk MODB_COLL_PERFACE_INFO nObj info')
                # 2я проверка. Проверяем наличие чанка 349Fh и есть ли в нем данны.
                if len(self.mod_obj.data_349Fh) == 0:
                    raise Exception('Wrong chunk MODB_COLL_PERFACE_INFO: MODB_COLL_NFACE_PEROBJ expect')
            except Exception as error:
                raise error
            # соберем данные.
            dword_var = read_uint(self.fb)
            data = []
            for _ in range(dword_var):
                i = read_uint(self.fb)
                d = {
                    'dec': i,
                    'hex': f"0x{pack_uint(i).hex()}"
                }
                data.append(d)
            self.mesh_mod.add_new_attribute('data_1500h', data)
            # Проведем проверку с подробным описанием.
            # Контрольное значение из 309Eh.
            control_var = self.mod_obj.var_309Eh['dec']
            counter_var = 0
            # Зададим контрольную сумму для подсчета каких-то данных..
            control_sum = 0
            # Запустим while цикл с условием остановки control_var == counter_var
            while True:
                item_349Fh = self.mod_obj.var_309Eh[control_sum]
            """
            is_success = False
        # 7099h(9970h) - чанк неизвестен. Вызывает tiohbReadPoint3D. Создает 3D точку.
        elif self.chunk == 0x7099:
            point3D = [read_float(self.fb) for _ in range(3)]
            self.mod_obj.add_new_attribute('data_3DPoint_7099h', point3D)
        # 709Ah(9A70h) - чанк неизвестен. Вызывает tiohbReadPoint3D. Создает 3D точку.
        elif self.chunk == 0x709A:
            point3D = [read_float(self.fb) for _ in range(3)]
            self.mod_obj.add_new_attribute('data_3DPoint_709Ah', point3D)
        else:
            is_success = False
        return is_success