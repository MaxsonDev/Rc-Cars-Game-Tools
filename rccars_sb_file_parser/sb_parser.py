from .sb_enum import MOD
from .sb_mods import get_type_mod
from .sb_utils import read_uint, read_ushort, read_string, read_float, pack_uint
from .parsers import MESH_parser, COLL_parser, HHID_parser

SB_FILE_SIGNATURE = 0x3801


class SBFileParser(object):
    """
    Парсер для .sb файлов игры Rc Cars(Недетские гонки).
    """
    def __init__(self, file_path, debug=False):
        """
        Флаг debug имеет смысл только при запуске .py файла в debug режиме в пошаговой отладке.
        Нужно для того, чтобы для удобства можно было смотреть значения и в hex и dec значениях.
        Не стоит использовать этот флаг при использовании парсера в других скриптах.
        :param file_path: str
            путь к .sb файлу
        :param debug: bool
            флаг для включения debug режима
        """
        if len(file_path) == 0:
            raise RuntimeWarning('Передайте путь к .sb файлу в аргумент file_path.')
        self.file_path = file_path
        self.fb = open(self.file_path, "rb")
        self.debug = debug
        self.mods_hex_list = []
        self.mods_str_list = []
        self.parsing_result = None
        self.root_mod = None
        self.current_MODL = None

    def get_parsing_result(self):
        return self.parsing_result

    def parse_file(self):     
        try:
            signature = read_ushort(self.fb)
            # проверяем правильность сигнатуры и является ли файл .sb файлом 
            if signature != SB_FILE_SIGNATURE and self.file_path[-3:].upper() == ".SB":
                raise RuntimeError(f"Неверная сигнатура файла: 0x{hex(signature)}. Либо выбран не тот файл.")
            self._parse_file_headers()
            chunk_end = read_uint(self.fb)
            new_mod = read_uint(self.fb)
            self.parsing_result = self._parse_mod(new_mod, chunk_end)
        except Exception as ex:
            raise ex
        finally:
            self.fb.close()

    def _parse_file_headers(self):
        """
        Функция парсит заголовки SB файла. Проверяет их целостность.
        Собирает значения MOD в строковом и hex представлении и добавляет
        в списки self.mods_str_list и self.mods_hex_list.
        """
        try:
            new_cursor = read_uint(self.fb)
            self.fb.seek(new_cursor)
            chunk = read_ushort(self.fb)
            # Первым чанком должен быть текстовый заголовок 4802h(**0248h).
            if chunk != 0x4802:
                raise Exception(f"Ошибка. Ожидаемый чанк заголовок 4802h")
            # Данные из чанка 4802h(**0248h) нам не нужны. Пропустим их.
            new_cursor = read_uint(self.fb)
            self.fb.seek(new_cursor)
            # Соберем MODs в заголовках файла
            # MOD инициализируется чанком 9A00h
            while True:
                chunk = read_ushort(self.fb)
                if chunk != 0x9A00:
                    break
                new_cursor = read_uint(self.fb)
                modb = read_uint(self.fb)
                self.mods_hex_list.append(modb)
                self.mods_str_list.append(MOD.get_mod_by_value(modb))
                self.fb.seek(new_cursor)
        except Exception as e:
            raise e
        
    def _parse_mod(self, mod_chunk, mod_end_address):
        """
        Функция парсинга sb файла базируется на оригинальной фунцкии в RcCars.exe файла!
        Т.к. .sb файл имеет древовидную структуру данных, то парсинг происходит в
        "рекурсивном цикле". Т.е. функция _parse_mod вызывает саму себя, если внутри
        MOD находятся новые дочерние MOD.

        Найденный чанк с данными спрева сверяется с общими чанками для всех MOD, такие как 9200h, 3408h, 4003h и т.д.
        Если чанк не является общим, то сверяем чанк с чанками MODа.

        Т.к. не обо всех чанках всё известно, дабы не словить ошибку или поврежденные данные,
        все парсеры возвращают флаг is_success. Стандартное значение флага False.
        Если флаг остается False, то о данных ничего не известно и их надо пропустить,
        прыгнув на конец данных chunk_end.

        ** - отображение чанков в .sb файле. Для более удобного чтения.

        :param mod_chunk: int
            значение MOD в числовом представлении
        :param mod_end_address: int
            указатель на адрес, где данные MOD заканчиваются
        """
        # Возьмем объект MODа
        mod_obj = get_type_mod(mod_chunk)
        # Добавим в self.root_mod корневой мод, если его нет.
        if self.root_mod is None:
            self.root_mod = mod_obj
        # Будем добавлять ссылку на корневой объект во все объекты MOD
        mod_obj.root_mod = self.root_mod
        # зададим start_address - от текущего положения отнимем 10 байт
        mod_obj.start_address = self.fb.tell() - 10
        # зададим end_address
        mod_obj.end_address = mod_end_address
        self._update_mod_counters(mod_obj)
        while True:
            chunk = read_ushort(self.fb)
            chunk_end = read_uint(self.fb)
            # 9200h(**0092h) - создает новый MOD.
            if chunk == 0x9200:
                # рекурсивно запускаем новый self._parse_mod для нового MOD
                new_mod = read_uint(self.fb)
                child_mod = self._parse_mod(new_mod, chunk_end)
                mod_obj.add_child_mod_in_list(child_mod.mod_type, child_mod)
            # 4003h(**0340h) - хранит имя MODа. Не все MOD имеют имя.
            elif chunk == 0x4003:
                # можно потом добавить проверку на максимально допустимую длину строки
                name = read_string(self.fb)
                mod_obj.add_new_attribute('data_4003h', name)
            # 540Bh(**0B54h) - хранит данные о трансформации MODа в 3D пространстве.
            # Положение[3 float], масштаб[3 float], вращение[3 float].
            # Все группы данных из 3х float, УСЛОВНО, хранят информацию об осях в таком порядке: XZY.
            # Имеет статичную контрольную сумму DWORD - 9.
            elif chunk == 0x540B:
                float_count = read_uint(self.fb)
                if float_count != 9:
                    raise Exception('ОШИБКА. Ожидаемое значение 9')
                data = [[read_float(self.fb) for _ in range(3)] for _ in range(3)]
                mod_obj.add_new_attribute('data_540Bh', data)
            # 3408h(**0834h) - хранит аргументы MOD. Всего 5 DWORD(4 байта) аргументов.
            # Это может быть как число, к примеру 1ый DWORD аргумент в MESH и GLTX хранит их ID.
            # Или может быть битовой маской, к примеру 3ий аргумент в MESH, который хранит битовые флаги для включения
            # выключения коллизии, отрисовки и т.д.
            # Имеет статичную контрольную сумму DWORD - 5.
            elif chunk == 0x3408:
                dword_args_length = read_uint(self.fb)
                if dword_args_length != 5:
                    raise Exception('ОШИБКА. Ожидаемое значение 5')
                data = []
                for _ in range(5):
                    var = read_uint(self.fb)
                    if self.debug:
                        d = {
                            'dec': var,
                            'hex': f"0x{pack_uint(var).hex()}"
                        }
                    else:
                        d = var
                    data.append(d)
                mod_obj.add_new_attribute('data_3408h', data)
            else:
                # если чанк не является общим чанком - ищем чанк в чанках MOD.
                is_success = False
                if mod_chunk == MOD.MESH.value:
                    mod_parser = MESH_parser(self.fb, mod_obj, chunk, chunk_end, self.debug)
                    is_success = mod_parser.parse_chunks()
                elif mod_chunk == MOD.COLL.value:
                    mod_parser = COLL_parser(self.fb, mod_obj, chunk, chunk_end, self.debug)
                    is_success = mod_parser.parse_chunks()
                elif mod_chunk == MOD.HHID.value:
                    mod_parser = HHID_parser(self.fb, mod_obj, chunk, chunk_end, self.debug)
                    is_success = mod_parser.parse_chunks()
                if is_success is False:
                    self.fb.seek(chunk_end)
            if mod_end_address == self.fb.tell():
                break
        return mod_obj

    def _update_mod_counters(self, mod_obj):
        """
        Функция обновляет счетчики в MODL.
        Считает общее количество текстур GLTX и мешей MESH.
        В будущем функция будет либо обновлятся, к примеру для подсчета количества кадров ANIM в MESH.
        Или же лучше будет написать отдельную функцию, как в RcCars.exe, которая рекурсивно считает кол-во объектов.
        :param mod_obj: Объект MOD
        :return:
        """
        # сохраним объект MODL в self переменную, чтобы обновлять счетчик MESH и GLTX
        if mod_obj.mod_type == 'MODL':
            self.current_MODL = mod_obj
        elif mod_obj.mod_type == 'MESH':
            self.current_MODL.MESH_count += 1
        elif mod_obj.mod_type == 'GLTX':
            self.current_MODL.GLTX_count += 1
