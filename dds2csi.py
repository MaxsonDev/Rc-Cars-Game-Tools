import os
from struct import unpack, pack
from typing import Union
from io import BytesIO


DDSPF_STRUCT = {
    "R8G8B8": [24, 0xff0000, 0x00ff00, 0x0000ff, 0],
    "A8R8G8B8": [32, 0x00ff0000, 0x0000ff00, 0x000000ff, 0xff000000],
    "R5G6B5": [16, 0xf800, 0x07e0, 0x001f, 0],
    "A4R4G4B4": [16, 0x0f00, 0x00f0, 0x000f, 0xf000]
}

CSIPF_STRUCT = [
    {'PixelSize': 4, 'FormatSymbolCount': 4, 'Format': [65, 82, 71, 66], 'FormatChannelBitMask': [7960, 5904, 3848, 1792], 'ChannelBitSizeLits': [8, 8, 8, 8]},
    {'PixelSize': 2, 'FormatSymbolCount': 4, 'Format': [65, 82, 71, 66], 'FormatChannelBitMask': [3852, 2824, 1796, 768], 'ChannelBitSizeLits': [4, 4, 4, 4]}, 
    {'PixelSize': 3, 'FormatSymbolCount': 3, 'Format': [82, 71, 66], 'FormatChannelBitMask': [5904, 3848, 1792], 'ChannelBitSizeLits': [8, 8, 8]},
    {'PixelSize': 1, 'FormatSymbolCount': 1, 'Format': [65], 'FormatChannelBitMask': [1792], 'ChannelBitSizeLits': [8]},
    {'PixelSize': 1, 'FormatSymbolCount': 3, 'Format': [82, 71, 66], 'FormatChannelBitMask': [1797, 1026, 256], 'ChannelBitSizeLits': [3, 3, 2]}, 
    {'PixelSize': 2, 'FormatSymbolCount': 3, 'Format': [82, 71, 66], 'FormatChannelBitMask': [3851, 2565, 1024], 'ChannelBitSizeLits': [5, 6, 5]}, 
    {'PixelSize': 2, 'FormatSymbolCount': 4, 'Format': [65, 82, 71, 66], 'FormatChannelBitMask': [3848, 1797, 1026, 256], 'ChannelBitSizeLits': [8, 3, 3, 2]},
    {'PixelSize': 2, 'FormatSymbolCount': 4, 'Format': [65, 82, 71, 66], 'FormatChannelBitMask': [3855, 3594, 2309, 1024], 'ChannelBitSizeLits': [1, 5, 5, 5]},
    {'PixelSize': 1, 'FormatSymbolCount': 1, 'Format': [73], 'FormatChannelBitMask': [1792], 'ChannelBitSizeLits': [8]}, 
    {'PixelSize': 1, 'FormatSymbolCount': 2, 'Format': [65, 73], 'FormatChannelBitMask': [1796, 768], 'ChannelBitSizeLits': [4, 4]},
    {'PixelSize': 2, 'FormatSymbolCount': 2, 'Format': [65, 73], 'FormatChannelBitMask': [3848, 1792], 'ChannelBitSizeLits': [8, 8]}
]


class DDSModel:
    def __init__(self):
        """
        На данный момент, известно, что CSI не использует заголовки:
        dwPitchOrLinearSize
        dwDepth
        """
        self.file_name: str = ""
        self.file_size: int = 0
        self.dds_pixel_format = None
        # DDS_HEADER structure
        self.dwMagic: int = 0x20534444 # b'DDS '
        self.dwSize = 0x7C
        self.dwFlags = 0
        self.dwHeight = 0
        self.dwWidth = 0
        self.dwPitchOrLinearSize = 0
        self.dwDepth = 0
        self.dwMipMapCount = 0
        self.dwReserved1 = 0
        self.ddspf: DDS_PIXELFORMAT = DDS_PIXELFORMAT()
        self.dwCaps = 0
        self.dwCaps2 = 0
        self.dwCaps3 = 0
        self.dwCaps4 = 0
        self.dwReserved2 = 0
        # DATA
        self.data: Union[bytearray, None] = None


class DDS_PIXELFORMAT:
    def __init__(self):
        # DDS_PIXELFORMAT structure
        self.dwSize = 32
        self.dwFlags = 0
        self.dwFourCC = 0
        self.dwRGBBitCount = 0
        self.dwRBitMask = 0
        self.dwGBitMask = 0
        self.dwBBitMask = 0
        self.dwABitMask = 0


class CSIM_Mod:
    def __init__(self):
        self.file_path: Union[None, str] = None
        self.file_size: Union[None, int] = None
        self.file_name: Union[None, str] = None
        self.dds_pixel_format = None
        # HEADERS
        self.hMagic: int = 0x4353494D #CSIM
        self.hWidth: Union[None, int] = None
        self.hHeight: Union[None, int] = None
        self.hPixelSize: Union[None, int] = None
        self.hMipMapCount: Union[None, int] = None
        self.hFormatSymbolCount: Union[None, int] = None
        self.hFormat: Union[None, bytearray] = None
        self.hFormatChannelBitMask: Union[None, list] = None
        # DATA
        self.data: Union[None, bytearray] = None


def tiohrReadByte(fb):
    data = fb.read(1)
    if data == b'' or len(data) != 1:
        return None
    return unpack("B", data)[0]


def tiohrReadWord(fb):
    data = fb.read(2)
    if data == b'' or len(data) != 2:
        return None
    return unpack("H", data)[0]


def tiohrReadDWord(fb):
    data = fb.read(4)
    if data == b'' or len(data) != 4:
        return None
    return unpack("I", data)[0]


def tiohWriteByte(fb, data):
    fb.write(pack("B", data))


def tiohWriteWord(fb, data):
    fb.write(pack("H", data))


def tiohWriteDWord(fb, data):
    fb.write(pack("I", data))


class DDSFileParser:
    def __init__(self, file_path):
        self.file_path: str = file_path
        self.file_size: Union[None, int] = None
        self.file_name: Union[None, str] = None
        self.fb: Union[None, BytesIO] = None
        # HEADERS
        # По итогу аргументы заголовков не используются.
        self.dwWidth = 0
        self.dwHeight = 0
        self.dwMipMapCount = 0
        self.dwRGBBitCount = 0
        self.is_mipmap_count_flag = False
        # MODEL
        self.dds_model: DDSModel = DDSModel()

    def parse_file(self):
        try:
            self.fb = open(self.file_path, "rb")
        except FileNotFoundError as ex:
            raise FileNotFoundError("Неверный путь к DDS файлу или файл отсутствует.") from ex
        try:
            self.dds_model.file_name = os.path.basename(self.file_path)
            self.fb.seek(0, 2)
            self.dds_model.file_size = self.fb.tell()
            self.fb.seek(0)
            self._check_headers()
            self._check_dds_pixel_format()
            self._parse_headers()
            self._parse_data()
        except Exception as ex:
            raise ex
        finally:
            self.fb.close()

    def get_parsing_result(self):
        return self.dds_model

    def _check_headers(self):
        dwMagic = tiohrReadDWord(self.fb)
        if dwMagic != 0x20534444:
            raise Exception(f"Неправильны формат файла dds. Неверная сигнатура: 0x{hex(dwMagic)} Ожидаемая сигнатура файла: 0x20534444(DDS ).")
        self.fb.seek(4)
        dwSize = tiohrReadDWord(self.fb)
        if dwSize == 0x7C:
            self.fb.seek(8)
            dwFlags = tiohrReadDWord(self.fb)
            # проверяем наличие флага DDSD_MIPMAPCOUNT = 0x00020000
            if dwFlags & 0x020000:
                self.is_mipmap_count_flag = True
            self.fb.seek(0xC)
            dwWidth = tiohrReadDWord(self.fb)
            if dwWidth >= 1:
                self.fb.seek(0x10)
                dwHeight = tiohrReadDWord(self.fb)
                if dwHeight >= 1:
                    self.fb.seek(0x1C)
                    dwMipMapCount = tiohrReadDWord(self.fb)
                    if dwMipMapCount <= 0xA:
                        self.fb.seek(0x50)
                        pixelfromat_dwFlag = tiohrReadDWord(self.fb)
                        if (pixelfromat_dwFlag & 0x40) == 0:
                            raise Exception("В заголовкахх DDPF отсутвует флаг DDPF_RGB = 0x40. Данные RGB не должны быть сжатыми.")
                        self.fb.seek(0x58)
                        hFormatChannelBitMask = tiohrReadDWord(self.fb)
                        if hFormatChannelBitMask in [16, 24, 32]:
                            return
                        else:
                            raise Exception(f"Размер заголовка hFormatChannelBitMask не соответсвует известным и используемым в csi. Недопустимое значение: {hFormatChannelBitMask}.")
        raise Exception(f"Заголовки файла {self.file_name} повреждены!!!")

    def _check_dds_pixel_format(self):
        self.fb.seek(0x58)
        pf_arr = [tiohrReadDWord(self.fb) for _ in range(5)]
        for key, value in DDSPF_STRUCT.items():
            if pf_arr == value:
                self.dds_model.dds_pixel_format = key
                return
        raise Exception(f"CSI не поддерживает формат пикселей: {pf_arr}")

    def _parse_headers(self):
        self.fb.seek(4)
        self.dds_model.dwSize = tiohrReadDWord(self.fb)
        self.dds_model.dwFlags = tiohrReadDWord(self.fb)
        self.dds_model.dwHeight = tiohrReadDWord(self.fb)
        self.dds_model.dwWidth = tiohrReadDWord(self.fb)
        self.fb.seek(0x1C)
        self.dds_model.dwMipMapCount = tiohrReadDWord(self.fb)
        self.fb.seek(0x4C)
        self.dds_model.ddspf.dwSize = tiohrReadDWord(self.fb)
        self.dds_model.ddspf.dwFlags = tiohrReadDWord(self.fb)
        self.dds_model.ddspf.dwFourCC = tiohrReadDWord(self.fb)
        self.dds_model.ddspf.dwRGBBitCount = tiohrReadDWord(self.fb)
        self.dds_model.ddspf.dwRBitMask = tiohrReadDWord(self.fb)
        self.dds_model.ddspf.dwGBitMask = tiohrReadDWord(self.fb)
        self.dds_model.ddspf.dwBBitMask = tiohrReadDWord(self.fb)
        self.dds_model.ddspf.dwABitMask = tiohrReadDWord(self.fb)

    def _parse_data(self):
        self.dds_model.data = bytearray()
        self.fb.seek(0x80, 0)
        data_size = self.dds_model.dwWidth * self.dds_model.dwHeight
        mip_map_counter = 0
        while True:
            for _ in range(data_size):
                data_chunk = self.fb.read(self.dds_model.ddspf.dwRGBBitCount // 4)
                [self.dds_model.data.append(new_byte) for new_byte in data_chunk]
            if mip_map_counter == self.dds_model.dwMipMapCount:
                break
            mip_map_counter += 1
            data_size = data_size >> 2


class DDS2CSIConverter:
    def __init__(self, dds_file_path):
        self.dds_file_path = dds_file_path
        self.dds_model: Union[DDSModel, None] = None
        self.csim_mod: Union[CSIM_Mod, None] = None
        self.csi_buffer: Union[BytesIO, None] = None
        # HEADERS
        self.hFormatSymbolCount: Union[None, int] = None
        self.hFormat: Union[None, bytearray] = None
        self.hFormatChannelBitMask: Union[None, list] = None

    def convert_to_file(self, output_path, file_name: Union[str, None] = None):
        if os.path.isdir(output_path) is False:
            raise Exception("Для сохранения CSI файла надо указать ПАПКУ вывода.")
        self._convert()
        if file_name:
            if file_name.find('.csi') == -1:
                file_name += ".csi"
            file_path = os.path.join(output_path, file_name)
        else:
            file_path = os.path.join(output_path, self.csim_mod.file_name)
        byte_array = self.csi_buffer.getvalue()
        with open(file_path, "w+b") as f:
            f.write(byte_array)
        self.csi_buffer.close()

    def convert_to_buffer(self):
        self._convert()
        return self.csi_buffer

    def _convert(self):
        dds_parser = DDSFileParser(self.dds_file_path)
        dds_parser.parse_file()
        self.dds_model = dds_parser.get_parsing_result()
        self._init_csi_model()
        self._set_csi_headers()
        self._write_csi_in_buffer()

    def _init_csi_model(self):
        self.csim_mod = CSIM_Mod()
        dds_file_name = self.dds_model.file_name
        self.csim_mod.file_name = dds_file_name.replace(".dds", ".csi")
        self.csim_mod.data = self.dds_model.data

    def _set_csi_headers(self):
        self.csim_mod.hWidth = self.dds_model.dwWidth
        self.csim_mod.hHeight = self.dds_model.dwHeight
        self.csim_mod.hMipMapCount = self.dds_model.dwMipMapCount
        csi_pf = get_csi_pixel_format_data(self.dds_model.dds_pixel_format)
        if csi_pf is None:
            raise Exception(f"CSI не поддерживает данный формат пикселей DDS: {self.dds_model.dds_pixel_format}")
        self.csim_mod.dds_pixel_format = self.dds_model.dds_pixel_format
        self.csim_mod.hPixelSize = csi_pf["PixelSize"]
        self.csim_mod.hFormatSymbolCount = csi_pf["FormatSymbolCount"]
        self.csim_mod.hFormatChannelBitMask = csi_pf["FormatChannelBitMask"]
        format_arr = bytearray()
        [format_arr.append(i) for i in csi_pf["Format"]]
        self.csim_mod.hFormat = format_arr

    def _write_csi_in_buffer(self):
        self.csi_buffer = BytesIO()
        self._write_headers()
        self._write_data()

    def _write_headers(self):
        try:
            # hMagic
            tiohWriteDWord(self.csi_buffer, self.csim_mod.hMagic)
            # 0x0
            tiohWriteDWord(self.csi_buffer, 0)
            # 2 резервированных заголовка
            [tiohWriteDWord(self.csi_buffer, 0xA0) for _ in range(2)]
            # hWidth
            tiohWriteDWord(self.csi_buffer, self.csim_mod.hWidth)
            # hHeight
            tiohWriteDWord(self.csi_buffer, self.csim_mod.hHeight)
            # hPixelSize
            tiohWriteDWord(self.csi_buffer, self.csim_mod.hPixelSize)
            # hMipMapCount
            tiohWriteDWord(self.csi_buffer, self.csim_mod.hMipMapCount)
            # hFormatSymbolCount
            tiohWriteDWord(self.csi_buffer, self.csim_mod.hFormatSymbolCount)
            # hFormat занимает 8 байт
            for i in range(8):
                if i < self.csim_mod.hFormatSymbolCount:
                    tiohWriteByte(self.csi_buffer, self.csim_mod.hFormat[i])
                else:
                    tiohWriteByte(self.csi_buffer, 0)
            # FormatChannelBitMask занимает 8 байт
            for i in range(4):
                if i < self.csim_mod.hFormatSymbolCount:
                    tiohWriteWord(self.csi_buffer, self.csim_mod.hFormatChannelBitMask[i])
                else:
                    tiohWriteWord(self.csi_buffer, 0)
            # 27 пустых заголовков
            [tiohWriteDWord(self.csi_buffer, 0) for _ in range(27)]
        except Exception as ex:
            raise ex

    def _write_data(self):
        dds_buffer = BytesIO(self.dds_model.data)
        data_size = self.csim_mod.hWidth * self.csim_mod.hHeight
        mip_map_counter = 0
        while True:
            for _ in range(data_size):
                data_chunk = dds_buffer.read(self.csim_mod.hPixelSize)
                self.csi_buffer.write(data_chunk)
            if mip_map_counter == self.csim_mod.hMipMapCount:
                break
            mip_map_counter += 1
            data_size = data_size >> 2
        dds_buffer.close()


def get_csi_pixel_format_data(dds_pixel_format: str):
    # 1. Разделим формат на символы и размеры каналов.
    format_symbol_list = []
    format_bit_size_list = []
    is_symbol = True
    for char in dds_pixel_format:
        if is_symbol:
            format_symbol_list.append(ord(char))
            is_symbol = False
        else:
            format_bit_size_list.append(int(char))
            is_symbol = True
    csi_pixel_format = None
    # 2. Найдем pixel_format CSI по полученным разделенным данным
    for pf in CSIPF_STRUCT:
        pf_format = pf["Format"]
        pf_bit_size = pf["ChannelBitSizeLits"]
        if pf_format == format_symbol_list and pf_bit_size == format_bit_size_list:
            csi_pixel_format = pf
            break
    return csi_pixel_format
