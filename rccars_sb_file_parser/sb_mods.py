import re

from .sb_enum import MOD
from .sb_utils import ModPath


class SuperMod:
    """
    Родительский супер класс для других классов.
    Нужен для общих методов для всех дочерних классов.
    """
    def __init__(self):
        self.start_address = None
        self.end_address = None
        self.root_mod = None

    def add_child_mod_in_list(self, mod_type: str, child_mod: object):
        """
        Добавляет в список дочерние MOD.
        :param mod_type: str
            тип MODа
        :param child_mod: object
            дочерний объект MOD
        :return:
        """
        list_name = f"{mod_type}_mods_list"
        try:
            self.__getattribute__(list_name).append(child_mod)
        except Exception:
            self.__setattr__(list_name, list())
            self.__getattribute__(list_name).append(child_mod)

    def get_child_mod_list(self, mod_type: str):
        """
        Возвращает список c дочерними MOD.
        :param mod_type: str
            тип MODа
        :return: list || None
            возвращает список или None при отсутствии списка
        """
        try:
            return self.__getattribute__(f"{mod_type}_mods_list")
        except Exception:
            return None

    def add_new_attribute(self, attr, data):
        """
        Много неизвестных чанков. По мере нахождения их значений, будет сложно
        уследить за принадлежностью атрибутов в каждом объекте.. Проще их добавлять при нахождении.
        :param attr:
        :param data:
        """
        try:
            self.__getattribute__(attr)
        except Exception:
            self.__setattr__(attr, data)
    
    def get_data_by_chunk(self, chunk: str):
        """
        Функция берет данные чанков из self по его значению data_{chunk}.
        Значение должно быть строкой! Не числом!
        При отсутсвии чанка возвращает None.
        :param: chunk: str
            Значение чанка. Пример: 709Ah, 1500h, 7215h и т.д.
        :returns:
            data_cnunk:
                данные чанка
            None:
                при отсутсnвии данных
        """
        if re.match(r"[0-9A-F]{4}h", chunk):
            try:
                return self.__getattribute__(f'data_{chunk}')
            except Exception:
                return None
        else:
            raise Exception("Неправильное значение чанка. Чанк должен быть 4х символьным hex числом в строковом представлении с постфиксом h. Пример правильного значения: '720Ah'.")
    
    def set_chunk_data(self, chunk: str, data):
        """
        Задает данные чанкам.
        :param chunk: str
        :param data:
        """
        if re.match(r"[0-9A-F]{4}h", chunk):
            self.__setattr__(f'data_{chunk}', data)
        else:
            raise Exception("Неправильное значение чанка. Чанк должен быть 4х символьным hex числом в строковом представлении с постфиксом h. Пример правильного значения: '720Ah'.")

    def is_chunk_exist(self, chunk: str):
        """
        Функция проверяет существует ли чанк и возвращает булевое значение.
        :param chunk: str
        :return: bool
        """
        if re.match(r"[0-9A-F]{4}h", chunk):
            try:
                self.__getattribute__(f'data_{chunk}')
                return True
            except Exception:
                return False
        else:
            raise Exception("Неправильное значение чанка. Чанк должен быть 4х символьным hex числом в строковом представлении с постфиксом h. Пример правильного значения: '720Ah'.")

    def get_mod_name(self):
        """
        Функция возвращает имя MODа, которое хранится в чанке 4003h.
        Не все MOD имеют имя. В таких случаях возвращается None.
        """
        if self.is_chunk_exist('4003h'):
            return self.data_4003h
        else:
            return None
    
    def get_mod_id(self):
        """
        3408h - хранит аргументы MOD. Всего 5 DWORD(4 байта) аргументов.
        Судя по наблюдениям, первый аргумент хранит id MODa.
        В частности ID для GLTX и MESH.
        :return:
        """
        return self.data_3408h[0]
        
    def get_transform_data(self):
        """
        540Bh - хранит данные о трансформации MODа в 3D пространстве.
        Положение[3 float], масштаб[3 float], вращение[3 float].
        Не все MOD имеют трансформацию. В таких случаях возвращается None
        :return:
        """
        if self.is_chunk_exist('540Bh'):
            data = {
                "location": self.data_540Bh[0],
                "scale": self.data_540Bh[1],
                "rotation": self.data_540Bh[2]
            }
            return data
        else:
            return None
        
    def find_parent_MODL(self):
        """
        Ищет родительский объект MODL.
        1.С помощью функции build_mod_path_objects_list строится путь списком от корневого MOD до текущего MOD.
        2. В цикле for ищем MODL. Если его нету, то возвращаем None.
        :return:
            возвращает объект MODL или None
        """
        path_obj = self.build_mod_path_objects_list()
        for mod in path_obj:
            if mod.mod_type == 'MODL':
                return mod
        return None
    
    def build_mod_path_objects_list(self):
        """
        Возвращает путь от корневого MOD к текущему MOD в виде списка объектов.
        :return: list
        """
        return self._build_mod_path("obj_list")

    def build_mod_path_string(self):
        """
        Возвращает путь от корневого MOD к текущему MOD в виде строки.
        :return: str
        """
        return self._build_mod_path("string")
        
    def _build_mod_path(self, path_type: str, mod_type=None, MODL_name=None, mod_id=None):
        """
        Корневая функция build_path для всех методов создания пути.
        Принимает аргументы в "двух режимах".
        1. Принимает только self объекта MOD для создания пути этого объекта.
        2. Принимает ВСЕ 3 опциональных аргумента для поиска MOD по его ID внутри конкретного MODL.
        Т.к., к примеру, некоторые имена у MESH могут повторяться.
        Поэтому для поиска лучше искать по ID в конкретном MODL.
        :path_type: str
            принимает ключевые слова:
            'obj_list' - для создания списка из объектов
            'string' - для создания пути в виде строки. Пример: 'DESC -> MODL -> MESH'
        :mod_type: str
            тип MODа для его поиска внутри MODL
        :MODL_name:
            имя MODL, в котором будем искать дочерний MOD
        :mod_id:
            id искомого объекта
        """
        mod_path = ModPath(path_type)
        if mod_type and MODL_name and mod_id or mod_id == 0:
            return mod_path.mod_path_by_params(self, mod_type, MODL_name, mod_id)
        else:
            return mod_path.mod_path_by_object(self)
    
    def _get_vox_matrix_resolution(self, chunk: str, axis_point=None):
        """
        Функция возвразает размер матрицы в виде списка. Для нахождения данных надо передать 
        правильный чанк: 3498h для COLL и 3490h для HHID.
        Если передать указатель на ось(axis_point), то можно получить значения по отдельности.
        :chunk: str
            чанк хранящий рамер матрицы
        :axis_point: int
            указатель на список осей матрицы, если нужна одна ось
        :return:
            matrix_size
        """
        matrix_resolution = self.get_data_by_chunk(chunk)
        if matrix_resolution is None:
            if chunk not in ['3498h', '3490h']:
                raise Exception("Неправильное значение чанка, хранящего размер матрицы. Ожидаемые чанки: '3498h', '3490h'.")
            raise Exception(f"В {self.mod_type}_Mod отсутствует обязательный чанк {chunk}")
        
        if axis_point is not None and axis_point not in [0, 1, 2] and type(axis_point) != int:
            raise Exception("Получен неправильный указателя на список осей матрицы. Ожидаемые значения для получения X: 0, Z: 1, Y: 2. Или же передать None для получения всех осей списком.")
        
        if axis_point is None:
            return matrix_resolution
        else:
            return matrix_resolution[axis_point]
        
    def _calculate_voxel_size(self, matrix_resolution: list, point3D_1: list, point3D_2: list):
        """
        Рассчитывает размер одного вокселя в матрицах COLL и HHID.
        :matrix_resolution: list
            размер матрицы по 3 осям
        :point3D_1: list
            координаты 1ой 3D точки
        :point3D_2: list
        координаты 2ой 3D точки
        :return:
            возвращает список с размером вокселя
        """
        x_vox_length, z_vox_length, y_vox_length = matrix_resolution
        x_size = (abs(point3D_1[0]) + abs(point3D_2[0])) / x_vox_length
        z_size = (abs(point3D_1[1]) + abs(point3D_2[1])) / z_vox_length
        y_size = (abs(point3D_1[2]) + abs(point3D_2[2])) / y_vox_length
        return [x_size, z_size, y_size]
    

class OOOO_Mod(SuperMod):
    def __init__(self):
        super().__init__()
        self.mod_type = '0000'


class DESC_Mod(SuperMod):
    def __init__(self):
        super().__init__()
        self.mod_type = 'DESC'


class MESH_Mod(SuperMod):
    def __init__(self):
        super().__init__()
        self.mod_type = 'MESH'
    
    def get_vertex_list(self):
        """
        Возвращает список координат вершин(vertexes) MESH.
        Если данных нет - вернет None.
        :return:
        """
        if self.is_chunk_exist('7411h'):
            return self.data_7411h
        else:
            return None

    def get_face_indexes_list(self):
        """
        Возвращает индексы вершин(vertex) для отрисовки полигонов(face) MESH.
        Если данных нет - вернет None.
        :return:
        """
        if self.is_chunk_exist('0617h'):
            face_indexes_list = []
            for face_data in self.data_0617h:
                face_indexes = face_data['data_3419h']
                face_indexes_list.append(face_indexes)
            return face_indexes_list
        else:
            return None
    
    def get_face_count(self):
        """
        Возвращает число полигонов(face) у MESH.
        :return:
        """
        if self.is_chunk_exist('0617h'):
            return len(self.data_0617h)
        else:
            return 0

    def get_mesh_collision_box_transform_data(self):
        """
        # 8216h(1682h) - чанк хранит невидимый куб, который является "зоной коллизии".
        Функция преобразует данные чанка в данные трансформации в 3D пространстве для визульного отображения
        "технического меша" в 3D редакторе.
        :return:
        """
        if self.is_chunk_exist('8216h'):
            transform_data = {
                "location": self.data_8216h['3DPoint'],
                "scale": [self.data_8216h['float'] for _ in range(3)],
                "rotation": None
            }
            return transform_data
        else:
            return None
        
    def get_mesh_visual_box_vertex_coords(self):
        """
        8215h - чанк хранит вершины невидимой геометрической фигуры, которая является "зоной отрисовки" MESH.
        Функция преобразует данные чанка в список координат вершин(vertexes) для визульного создания
        "технической фигуры" в 3D редакторе.
        :return:
        """
        if self.is_chunk_exist('8215h'):
            vertex_list = []
            z_axsi = self.data_8215h[:2]
            step = 2
            for _ in range(4):
                xy_axsi = self.data_8215h[step: step + 2]
                vertex_list.append([xy_axsi[0], z_axsi[0], xy_axsi[1]])
                vertex_list.append([xy_axsi[0], z_axsi[1], xy_axsi[1]])
                step += 2
            return vertex_list
        else:
            return None
        

class LITD_Mod(SuperMod):
    def __init__(self):
        super().__init__()
        self.mod_type = 'LITD'


class CAMR_Mod(SuperMod):
    def __init__(self):
        super().__init__()
        self.mod_type = 'CAMR'


class TEXR_Mod(SuperMod):
    def __init__(self):
        super().__init__()
        self.mod_type = 'TEXR'


class MATR_Mod(SuperMod):
    def __init__(self):
        super().__init__()
        self.mod_type = 'MATR'


class GLTX_Mod(SuperMod):
    def __init__(self):
        super().__init__()
        self.mod_type = 'GLTX'


class HHID_Mod(SuperMod):
    def __init__(self):
        super().__init__()
        self.mod_type = 'HHID'

    def get_hhid_x_vox_length(self):
        """
        Возвращает длину HHID матрицы в вокселях по оси X
        :return:
        """
        return self._get_vox_matrix_resolution('3490h', 0)

    def get_hhid_z_vox_length(self):
        """
        Возвращает длину HHID матрицы в вокселях по оси Z
        :return:
        """
        return self._get_vox_matrix_resolution('3490h', 1)
    
    def get_hhid_y_vox_length(self):
        """
        Возвращает длину HHID матрицы в вокселях по оси Y
        :return:
        """
        return self._get_vox_matrix_resolution('3490h', 2)

    def get_hhid_vox_matrix_resolution(self):
        """
        Возвращает размер HHID матрицы по всем осям XZY.
        :return:
        """
        return self._get_vox_matrix_resolution('3490h')
    
    def calculate_hhid_voxel_size(self):
        """
        Рассчитывает размер вокселя для HHID матрицы.
        :return:
        """
        if self.is_chunk_exist('3490h') and self.is_chunk_exist('7091h') and self.is_chunk_exist('7092h'):
            return self._calculate_voxel_size(self.get_hhid_vox_matrix_resolution(), self.get_data_by_chunk('7091h'), self.get_data_by_chunk('7092h'))
        else:
            raise Exception("Отсутсвуют данные для рассчета размера вокселя HHID матрицы. Для рассчета нужны данные: размер матрицы(3490h) и две 3D точки(7091h и 7091h).")

    def get_voxel_hhid_info_by_vox_indexes(self, x_vox, z_vox, y_vox):
        """
        Функция по передаваемым индексам("координатам") ищет данные о вокселе среди чанков 8094h.
        Данными являются индексы("координаты") и битовая маска. Битовая маска отвечает за включение выключение
        мешей. Если машинка находится в зоне вокселя,то MESH со значением 1 отображаются, а со значением 0 исчезают.
        Если данные вокселя не найдутся по передаваемым индексам, значит такого вокселя нет - возвращаем None.
        :param x_vox:
        :param z_vox:
        :param y_vox:
        :return:
        """
        data_8094h_list = self.get_data_by_chunk('8094h')
        for data_8094h in data_8094h_list:
            point = data_8094h['xzy_vox_point']
            if x_vox - 1 == point[0] and z_vox - 1 == point[1] and y_vox - 1 == point[2]:
                return data_8094h
        return None
        
    def test_search_vox_data_by_id(self, x_vox, z_vox, y_vox):
        """
        Тестовая функция
        :param x_vox:
        :param z_vox:
        :param y_vox:
        :return:
        """
        data_8094h_list = self.get_data_by_chunk('8094h')
        for data_8094h in data_8094h_list:
            point = data_8094h['xzy_vox_point']
            if x_vox - 1 == point[0] and z_vox - 1 == point[1] and y_vox - 1 == point[2]:
                return data_8094h
        return None


class COLL_Mod(SuperMod):
    def __init__(self):
        super().__init__()
        self.mod_type = 'COLL'

    def get_coll_x_vox_length(self):
        """
        Возвращает длину COLL матрицы в вокселях по оси X
        :return:
        """
        return self._get_vox_matrix_resolution('3498h', 0)

    def get_coll_z_vox_length(self):
        """
        Возвращает длину COLL матрицы в вокселях по оси Z
        :return:
        """
        return self._get_vox_matrix_resolution('3498h', 1)
    
    def get_coll_y_vox_length(self):
        """
        Возвращает длину COLL матрицы в вокселях по оси Y
        :return:
        """
        return self._get_vox_matrix_resolution('3498h', 2)

    def get_coll_vox_matrix_resolution(self):
        """
        Возвращает размер COLL матрицы по всем осям XZY.
        :return:
        """
        return self._get_vox_matrix_resolution('3498h')
        
    def calculate_coll_voxel_size(self):
        """
        Рассчитывает размер вокселя для COLL матрицы.
        :return:
        """
        if self.is_chunk_exist('3498h') and self.is_chunk_exist('7099h') and self.is_chunk_exist('709Ah'):
            return self._calculate_voxel_size(self.get_coll_vox_matrix_resolution(), self.get_data_by_chunk('7099h'), self.get_data_by_chunk('709Ah'))
        else:
            raise Exception("Отсутсвуют данные для рассчета размера вокселя COLL матрицы. Для рассчета нужны данные: размер матрицы(3498h) и две 3D точки(7099h и 709Ah).")

    def create_pointer_list_on_matrix_data(self):
        """
        Функция из матрицы 809Dh создает указатели на данные чанков 809Ch и 349Fh.
        Подробней о работе с данными коллизии читать в coll_parser.py
        :return:
        """
        data = []
        count_sum = 0
        for i in self.data_809Dh:
            data.append(count_sum)
            count_sum += i
        return data

    def calculate_meshes_face_size_in_byte(self):
        """
        Функция рассчитывает из количества полигонов(face) длину байт для битовой маски.
        Рассчитываются все MESH. Подробней о работе с данными коллизии читать в coll_parser.py
        :return:
        """
        data = []
        MODL = self.find_parent_MODL()
        mesh_count = MODL.MESH_count
        for mod_id in range(mesh_count):
            MESH = MODL.find_MESH_by_id(mod_id)
            face_count = MESH.get_face_count()
            if face_count == 0:
                data.append(1)
            else:
                d = (face_count - 1) // 8 + 1
                data.append(d)
        return data

    def create_pointer_list_on_face_bit_mask_list(self):
        """
        Функция рассчитывает указатели на битовые маски в чанке 1500h исходя из данных о полигонах(face),
        хранящихся в чанке 349Fh.
        Подробней о работе с данными коллизии читать в coll_parser.py
        :return:
        """
        pointer_list = []
        count_v12 = 0
        global_dword = 0
        i = 0
        while i < self.data_309Eh:
            pointer_list.insert(i, count_v12)
            # v14 = (self.data_349Fh[i] - 1) >> 3
            v14 = (self.data_349Fh[i] - 1) // 8
            i += 1
            count_v12 = global_dword + v14 + 1
            global_dword = count_v12
        return pointer_list


class EMPT_Mod(SuperMod):
    def __init__(self):
        super().__init__()
        self.mod_type = 'EMPT'


class INST_Mod(SuperMod):
    def __init__(self):
        super().__init__()
        self.mod_type = 'INST'


class MARK_Mod(SuperMod):
    def __init__(self):
        super().__init__()
        self.mod_type = 'MARK'


class ASEQ_Mod(SuperMod):
    def __init__(self):
        super().__init__()
        self.mod_type = 'ASEQ'


class ANIM_Mod(SuperMod):
    def __init__(self):
        super().__init__()
        self.mod_type = 'ANIM'


class SPLN_Mod(SuperMod):
    def __init__(self):
        super().__init__()
        self.mod_type = 'SPLN'


class DYNM_Mod(SuperMod):
    def __init__(self):
        super().__init__()
        self.mod_type = 'DYNM'


class CNST_Mod(SuperMod):
    def __init__(self):
        super().__init__()
        self.mod_type = 'CNST'


class CVOL_Mod(SuperMod):
    def __init__(self):
        super().__init__()
        self.mod_type = 'CVOL'


class EVOL_Mod(SuperMod):
    def __init__(self):
        super().__init__()
        self.mod_type = 'EVOL'


class SCRI_Mod(SuperMod):
    def __init__(self):
        super().__init__()
        self.mod_type = 'SCRI'


class MODL_Mod(SuperMod):
    def __init__(self):
        super().__init__()
        self.mod_type = 'MODL'
        self.MESH_count = 0
        self.GLTX_count = 0

    def create_MESH_list(self):
        """
        Создает список всех MESH, которые есть в MODL.
        :return:
        """
        mesh_list = []
        for i in range(self.MESH_count):
            mesh_list.append(self.find_MESH_by_id(i))
        return mesh_list

    def find_MESH_by_id(self, mod_id):
        """
        Ищет MESH по его ID в MODL
        :param mod_id:
        :return:
        """
        return self._find_mod_by_id("MESH", mod_id)

    def find_GLTX_by_id(self, mod_id):
        """
        Ищет GLTX по его ID в MODL
        :param mod_id:
        :return:
        """
        return self._find_mod_by_id("GLTX", mod_id)

    def _find_mod_by_id(self, mod_type, mod_id):
        """
        Ищет дочерние MOD по их типу и ID в родительском MODL
        :param mod_type:
        :param mod_id:
        :return:
        """
        mod_path = self._build_mod_path("obj_list", mod_type, self.get_mod_name(), mod_id)
        if mod_path is None:
            return None
        return mod_path[-1]


class MSHD_Mod(SuperMod):
    def __init__(self):
        super().__init__()
        self.mod_type = 'MSHD'


class FOLD_Mod(SuperMod):
    def __init__(self):
        super().__init__()
        self.mod_type = 'FOLD'


class SOND_Mod(SuperMod):
    def __init__(self):
        super().__init__()
        self.mod_type = 'SOND'


class SNCH_Mod(SuperMod):
    def __init__(self):
        super().__init__()
        self.mod_type = 'SNCH'


def get_type_mod(value):
    if value == MOD.OOOO.value:
        new_mod = OOOO_Mod()
    elif value == MOD.DESC.value:
        new_mod = DESC_Mod()
    elif value == MOD.MESH.value:
        new_mod = MESH_Mod()
    elif value == MOD.LITD.value:
        new_mod = LITD_Mod()
    elif value == MOD.CAMR.value:
        new_mod = CAMR_Mod()
    elif value == MOD.TEXR.value:
        new_mod = TEXR_Mod()
    elif value == MOD.MATR.value:
        new_mod = MATR_Mod()
    elif value == MOD.GLTX.value:
        new_mod = GLTX_Mod()
    elif value == MOD.HHID.value:
        new_mod = HHID_Mod()
    elif value == MOD.COLL.value:
        new_mod = COLL_Mod()
    elif value == MOD.EMPT.value:
        new_mod = EMPT_Mod()
    elif value == MOD.INST.value:
        new_mod = INST_Mod()
    elif value == MOD.MARK.value:
        new_mod = MARK_Mod()
    elif value == MOD.ASEQ.value:
        new_mod = ASEQ_Mod()
    elif value == MOD.ANIM.value:
        new_mod = ANIM_Mod()
    elif value == MOD.SPLN.value:
        new_mod = SPLN_Mod()
    elif value == MOD.DYNM.value:
        new_mod = DYNM_Mod()
    elif value == MOD.CNST.value:
        new_mod = CNST_Mod()
    elif value == MOD.CVOL.value:
        new_mod = CVOL_Mod()
    elif value == MOD.EVOL.value:
        new_mod = EVOL_Mod()
    elif value == MOD.SCRI.value:
        new_mod = SCRI_Mod()
    elif value == MOD.MODL.value:
        new_mod = MODL_Mod()
    elif value == MOD.MSHD.value:
        new_mod = MSHD_Mod()
    elif value == MOD.FOLD.value:
        new_mod = FOLD_Mod()
    elif value == MOD.SOND.value:
        new_mod = SOND_Mod()
    else:
        new_mod = SNCH_Mod()
    return new_mod
