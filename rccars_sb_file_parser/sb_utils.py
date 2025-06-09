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


def pack_float(data):
    return pack(">f", data)


def write_float(fb, data):
    fb.write(pack("f", data))


def write_uint(fb, data):
    fb.write(pack("I", data))


def write_char(fb, data):
    fb.write(pack("B", data))
    

def write_ushort(fb, data):
    fb.write(pack("H", data))


class ModPath:
    """
    Класс для создания пути для MOD в древе данных.
    Путь может быть строкой или списком MOD объектов.
    """
    def __init__(self, path_type):
        """
        Если path_type == "obj_list", то будет возвращаться путь в виде списка объектов.
        Если path_type == "string", то будет возвращаться строка.
        Пример: DESC -> MODL -> MESH 
        Стрелки можно заменить на '/' в path_delimiter, но мне так больше нравится! Лучше читается.
        :param: path_type: тип может быть "obj_list" или "string".
        """
        if path_type not in ["obj_list", "string"]:
            raise Exception(f"Недопустимое значение аргумента path_type! Ожидаемые значения: 'obj_list' или 'string'. Получено значение: '{path_type}'")
        self.path_type = path_type
        self.path_delimiter = ' -> '

        self.mod_obj = None
        self.mod_type = None
        self.MODL_name = None
        self.mod_id = None
        self.cur_MODL_name = None

        self.path_list = None

        self.search_by_obj = True
        self.is_path_find = False

    def mod_path_by_object(self, mod_obj):
        """
        Создает путь для переданного объекта MOD.
        :param mod_obj:
        :return:
        """
        return self._get_path_mod(mod_obj)
    
    def mod_path_by_params(self, mod_obj, mod_type, MODL_name, mod_id):
        """
        Создает путь для объекта по аргументам. Т.к., к примеру, некоторые имена у MESH объектов могут быть одинаковы.
        Или же надо найти конкретный MESH в конкретном MODL по ID. Для этого подойдет данная функция, чтобы искать
        дочерние объекты в родительском MODL по аргументам.
        :param mod_obj:
        :param mod_type:
        :param MODL_name:
        :param mod_id:
        :return:
        """
        if type(MODL_name) != str:
            raise Exception(f'Тип аргумента MODL_name должен быть str, а не {type(MODL_name).__name__}.')
        if type(mod_id) != int:
            raise Exception(f'Тип аргумента mod_id должен быть int, а не {type(mod_id).__name__}.')
        self.search_by_obj = False
        return self._get_path_mod(mod_obj, mod_type, MODL_name, mod_id)

    def _get_path_mod(self, mod_obj, mod_type=None, MODL_name=None, mod_id=None):
        self.mod_obj = mod_obj
        self.mod_type = mod_type
        self.mod_id = mod_id
        self.MODL_name = MODL_name

        root_mod = mod_obj.root_mod
        el_count = 0
        path_list = []
        self._open_all_children(root_mod, el_count, path_list)
        if self.is_path_find:
            if self.path_type == "obj_list":
                return self.path_list
            return self._get_path_string()
        else:
            return None
    
    def _get_path_string(self):
        path_txt = ''
        for i, mod_obj in enumerate(self.path_list):
            mod_path_name = self._build_name(mod_obj)
            path_txt += mod_path_name
            if i + 1 != len(self.path_list):
                path_txt += self.path_delimiter
        return path_txt
    
    def _build_name(self, mod_obj):
        name = ""
        name += mod_obj.mod_type
        obj_name = mod_obj.get_mod_name()
        if obj_name is not None:
            name += f"_{obj_name}"
        return name

    def _open_all_children(self, mod_obj, el_count, path_list):
        path_list.insert(el_count, mod_obj)
        el_count += 1
        
        if self.search_by_obj:
            if id(self.mod_obj) == id(mod_obj):
                self.path_list = path_list
                self.is_path_find = True
        else:
            # будем обновлять имя для MODL, если объект является MODL.
            if mod_obj.mod_type == 'MODL':
                self.cur_MODL_name = mod_obj.get_mod_name()

            if mod_obj.mod_type == self.mod_type and self.cur_MODL_name == self.MODL_name and mod_obj.get_mod_id() == self.mod_id:
                self.path_list = path_list
                self.is_path_find = True
        
        for attr in mod_obj.__dir__():
            if self.is_path_find:
                return
            if attr.find('_mods_list') == -1:
                continue
            mod_type = attr.replace('_mods_list', '')
            child_mod_list = mod_obj.get_child_mod_list(mod_type)
            for child_mod in child_mod_list:
                if self.is_path_find:
                    return
                new_el_count = el_count
                new_path_list = path_list.copy()
                self._open_all_children(child_mod, new_el_count, new_path_list)                
