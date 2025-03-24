import os
# import time

from struct import unpack
from sb_enum import MOD
from sb_types import get_type_mod
from sb_utils import read_uint, read_ushort, read_string, read_float, pack_ushort, pack_uint
from parsers.mesh_parser import MESH_parser

FILE_PATH = "/home/max/Рабочий стол/RcCarsParser/RCCarsDB/AIChars.sb"
SB_FILE_SIGNATURE = 0x3801
# log_file = open(f'log_{time.time()}.txt', 'w')


class SBFileParser(object):
    def __init__(self, file_path):
        self.file_path = file_path
        self.file_size = None
        self.file_cursor = None
        self.mods_hex_list = []
        self.mods_str_list = []
        self.models_list = []

    def parse_file(self):
        self.init_file()        
        try:
            signa = read_ushort(self.fb)
            # проверяем правильность сигнатуры и является ли файл .sb файлом 
            if signa != SB_FILE_SIGNATURE and self.file_path[-3:].upper() == ".SB":
                # raise RuntimeError("Invalid file signature: %08d" % (magic))
                raise RuntimeError("Неверная сигнатура файла: %08d. Либо выбран не тот файл." % (signa))
            # спарсили заголовки
            self.parse_file_headers()
            # возьмем чанк адреса окончания MOD
            chunk_end = read_uint(self.fb)
            # возьмем DESC чанк
            new_mod = read_uint(self.fb)
            SB_DATA = self.parse_mod(new_mod, chunk_end)
        except Exception as ex:
            raise ex
        finally:
            self.fb.close()

    def init_file(self):
        self.fb = open(self.file_path, "rb")
        self.file_size = self.fb.seek(0, os.SEEK_END)
        self.file_cursor = 1
        self.fb.seek(0)

    def parse_file_headers(self):
        try:
            # По идее заголовки закономерны, но стоит проверить на целосттность. Малоли длина байт разная.
            # Поэтому можно пошагово прописать функцию. 
            # читаем адрес следующего чанка и преходим к нему
            new_cursor = read_uint(self.fb)
            self.fb.seek(new_cursor)
            # следующим чанком должен быть 4802h(**0248h). Текстовый заголовок. Проверям.
            chunk = read_ushort(self.fb)
            if chunk != 0x4802:
                raise Exception({"invalid_chunk": "0x4802"})
            # чанк совпал. пропустим его. он не важен. берем указатель на следующий чанк и переходим.
            new_cursor = read_uint(self.fb)
            self.fb.seek(new_cursor)
            # вот тут уже надо собрать все MOD, чтобы знать какие моды используются в файле и проводить с ними проверку,
            # дабы не прочесть что-то не так по ошибке при парсинге.
            # MOD - непонятно что подразумевается под MOD, поэтом называю модуль.
            # Пример MOD: MOD_MESH, MOD_CAMERA и т.д.
            # 9A00h(**009Ah) чанк инициализации модуля .
            # собирем MODs
            while True:
                chunk = read_ushort(self.fb)
                if chunk != 0x9A00:
                    break
                    # raise Exception({"invalid_chunk": "0x9A00"})
                new_cursor = read_uint(self.fb)
                # modb = read_uint(self.fb)
                modb = self.fb.read(4)
                self.mods_hex_list.append(unpack("I", modb)[0])
                # для просмотра при дебаге. можно убрать этот список
                self.mods_str_list.append(modb[::-1].decode('cp437'))
                # проверим следующий чанк.
                # если не равен 9A00h, значит все MOD собраны
                self.fb.seek(new_cursor)
           # откатим курсор файла назад на 2 байта и зададим нашему контрольному курсору последнюю позицию
            '''cur = self.fb.tell() - 2
            self.fb.seek(cur)
            self.file_cursor = cur'''
        except Exception as e:
            raise e
        
    def parse_mod(self, mod_chunk, mod_end_addres):
        """
        Основная логика чтения чанков взята из оригинальной логики файла exe.
        """
        # возьмем объект MOD
        mod = get_type_mod(mod_chunk)
        while True:
            # берём чанк и сверяем с одним из общих чанков
            chunk = read_ushort(self.fb)
            # берем адрес конца чанка
            chunk_end = read_uint(self.fb)
            # 9200h(**0092h) - чанк инициализирует новый MOD.
            if chunk == 0x9200:
                # если чанк == 9200, то запускаем новый parse_mod для нового чанка
                new_mod = read_uint(self.fb)
                # для логов
                # log_file.write("=" * 20 + "\n")
                # log_file.write(f"MOD: {MOD.get_mod_by_value(new_mod)}\n")
                # log_file.write(f"Chunk: 0x{pack_ushort(chunk).hex()}\n")
                # log_file.write(f"End address: 0x{pack_uint(chunk_end).hex()}\n")
                # print(MOD.get_mod_by_value(new_mod))
                # if new_mod in [MOD.DESC.value, MOD.MODL.value, MOD.MESH.value]:
                child_mod = self.parse_mod(new_mod, chunk_end)
                # пока непонятно как группируются данные, но у них есть структура вложенности
                # ANIM может быть вложен в MESH, а MESH в MESH(возможно это кости?),
                # в свою очередь все MESH вкладываются в MODL, а MODL в DESC.
                # поэтому дочерние элементы будут вкладываться в родительские элементы в списки по модам.
                mod.add_child_mod_in_list(f"{child_mod.mod_type}_mods_list", child_mod)
            # 4003h(**0340h) - чанк хранит имя MODа. Есть моды, без имен.
            elif chunk == 0x4003:
                mod.name = read_string(self.fb)
            # 540Bh(**0B54h) - чанк хранит данные о трансформации MODа в 3D пространстве.
            # Положение[3 float], масштаб[3 float], вращение[3 float]. Все группы данных из 3х float хранят информацию об осях 
            # в таком порядке: XZY.
            elif chunk == 0x540B:
                # читаем общее количество флоат. Дб 9.
                float_count = read_uint(self.fb)
                if float_count != 9:
                    raise 'ОШИБКА. Ожидаемое значение 9'
                d = {}
                d["location"] = [read_float(self.fb) for _ in range(3)]
                d["scale"] = [read_float(self.fb) for _ in range(3)]
                d["rotation"] = [read_float(self.fb) for _ in range(3)]
                mod.transform = d
            # 3408h(**0834h) - чанк хранит аргументы мода. Обязательный чанк количества DWORD аргументов - 5.
            elif chunk == 0x3408:
                dword_args_length = read_uint(self.fb)
                if dword_args_length != 5:
                    raise 'ОШИБКА. Ожидаемое значение 5'
                mod.dword_args_list = [read_uint(self.fb) for _ in range(5)]
            else:
                # если чанк не является общим чанком - ищем чанк в чанках мода.
                # каждый парсер возвращает флаг is_success. Если чанк спаршен, то чанк возвращает флаг True.
                is_success = False
                if mod_chunk == MOD.MESH.value:
                    is_success = MESH_parser(self.fb, mod, chunk)
                # если чанк не спаршен(еще не добавлен), то флаг возвращает False.
                # Если False, то пропускаем чанк и перемещаем указатель файла в конец чанка
                # log_file.write(f"Chunk: 0x{pack_ushort(chunk).hex()}\n")
                # log_file.write(f"End address: 0x{pack_uint(chunk_end).hex()}\n")
                if is_success is False:
                    self.fb.seek(chunk_end)

            # если данные мода закончились, то останавливаем цикл.
            if mod_end_addres == self.fb.tell():
                break
        return mod


def work(file_path):
    if len(file_path) == 0:
        raise RuntimeWarning('Укажи путь к .sb файлу в переменную FILE_PATH.')
    sb_parser = SBFileParser(file_path)
    sb_parser.parse_file()


if __name__ == "__main__":
    work(FILE_PATH)
    # log_file.close()