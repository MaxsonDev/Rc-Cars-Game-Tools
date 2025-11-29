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


class DDSModel:
    def __init__(self):
        """
        На данный момент, известно, что CSI не использует заголовки:
        dwPitchOrLinearSize
        dwDepth
        """
        self.file_name = None
        # DDS_HEADER structure
        self.dwMagic: int = 0x20534444 # b'DDS '
        self.dwSize = 0x7C
        self.dwFlags = None
        self.dwHeight = None
        self.dwWidth = None
        self.dwPitchOrLinearSize = 0
        self.dwDepth = 0
        self.dwMipMapCount = None
        self.dwReserved1 = None
        self.ddspf = DDS_PIXELFORMAT()
        self.dwCaps = None
        self.dwCaps2 = None
        self.dwCaps3 = None
        self.dwCaps4 = None
        self.dwReserved2 = None
        # DATA
        self.data: Union[bytearray, None] = None


class DDS_PIXELFORMAT:
    def __init__(self):
        # DDS_PIXELFORMAT structure
        self.dwSize = 32
        self.dwFlags = None
        self.dwFourCC = None
        self.dwRGBBitCount = None
        self.dwRBitMask = None
        self.dwGBitMask = None
        self.dwBBitMask = None
        self.dwABitMask = None


class CSIM_Mod:
    def __init__(self):
        self.file_path: Union[None, str] = None
        self.file_size: Union[None, int] = None
        self.file_name: Union[None, str] = None
        self.dds_pixel_format = None
        # HEADERS
        self.hWidth: Union[None, int] = None
        self.hHeight: Union[None, int] = None
        self.hPixelSize: Union[None, int] = None
        self.hMipMapCount: Union[None, int] = None
        self.hFormatCharCount: Union[None, int] = None
        self.hFormat: Union[None, bytearray] = None
        self.hFormatChannelBitCounts: Union[None, list] = None
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


def tiohrWriteByte(fb, data):
    fb.write(pack("B", data))


def tiohWriteWord(fb, data):
    fb.write(pack("H", data))


def tiohbWriteDWord(fb, data):
    fb.write(pack("I", data))


class CSIFileParser:
    def __init__(self, file_path):
        self.file_path: str = file_path
        self.file_size: Union[None, int] = None
        self.file_name: Union[None, str] = None
        self.fb: Union[None, BytesIO] = None
        self.dds_pixel_format = None
        self.is_file_parsed = False
        # HEADERS
        self.hWidth: Union[None, int] = None
        self.hHeight: Union[None, int] = None
        self.hPixelSize: Union[None, int] = None
        self.hMipMapCount: Union[None, int] = None
        self.hFormatCharCount: Union[None, int] = None
        self.hFormat: Union[None, bytearray] = None
        self.hFormatChannelBitCounts: Union[None, list] = None
        # DATA
        self.data: Union[None, bytearray] = None

    def parse_file(self):
        try:
            self.fb = open(self.file_path, "rb")
        except FileNotFoundError:
            raise Exception("Неверный путь к CSI файлу или файл отсутствует.")
        try:
            self.file_name = os.path.basename(self.file_path)
            self.fb.seek(0, 2)
            self.file_size = self.fb.tell()
            if self.file_size <= 0xA0:
                raise Exception(f"Файл {self.file_name} критически поврежден!!!")
            self._parse_headers()
            self._parse_data()
            self._create_csim_mod()
        except Exception as ex:
            raise ex
        finally:
            self.fb.close()

    def get_parsing_result(self):
        return self.csim_mod

    def _parse_headers(self):
        self._check_headers()
        self.fb.seek(0x10, 0)
        self.hWidth = tiohrReadDWord(self.fb)
        self.fb.seek(0x14, 0)
        self.hHeight = tiohrReadDWord(self.fb)
        self.fb.seek(0x18, 0)
        self.hPixelSize = tiohrReadDWord(self.fb)
        self.fb.seek(0x1C, 0)
        self.hMipMapCount = tiohrReadDWord(self.fb)
        self.fb.seek(0x20, 0)
        self.hFormatCharCount = tiohrReadDWord(self.fb)
        self.fb.seek(0x24, 0)
        format_byte_array = bytearray()
        for _ in range(self.hFormatCharCount):
            char_byte = tiohrReadByte(self.fb)
            format_byte_array.append(char_byte)
        self.hFormat = format_byte_array
        self.hFormatChannelBitCounts = self._parse_hFormatChannelBitCounts()
        self.dds_pixel_format = self._create_dds_pixel_format_string()

    def _parse_hFormatChannelBitCounts(self):
        ch_bit_list = []
        self.fb.seek(0x2C, 0)
        for _ in range(self.hFormatCharCount):
            chunk = tiohrReadWord(self.fb)
            if chunk == 0xFF:
                ch_bit_list.append(0)
                continue
            chunk &= 0xfffff
            hibyte = chunk >> 8
            lobyte = chunk & 0xFF
            b_size = hibyte - lobyte + 1
            ch_bit_list.append(b_size)
        return ch_bit_list

    def _create_dds_pixel_format_string(self):
        string = ""
        for i in range(self.hFormatCharCount):
            char_byte = self.hFormat[i]
            bit_size = self.hFormatChannelBitCounts[i]
            string += f"{chr(char_byte)}{str(bit_size)}"
        return string

    def _check_headers(self):
        self.fb.seek(0, 0)
        magic = tiohrReadDWord(self.fb)
        # 0x4353494D == CSIM
        if magic != 0x4353494D:
            raise Exception(f"Неправильный формат файла csi. Неверная сигнатура: 0x{hex(magic)} Ожидаемая сигнатура файла: 0x4353494D(CSIM).")
        # обязательное значение заголовка = 0xA0
        self.fb.seek(8, 0)
        dwHeaderLength = tiohrReadDWord(self.fb)
        if dwHeaderLength == 0xA0:
            # неизвестный заголовок
            self.fb.seek(0xC, 0)
            ukn_header = tiohrReadDWord(self.fb)
            if ukn_header >= 0xA0:
                # width текстуры >= 1
                self.fb.seek(0x10, 0)
                dwWidth = tiohrReadDWord(self.fb)
                if dwWidth >= 1:
                    # height >= 1
                    self.fb.seek(0x14, 0)
                    dwHeight = tiohrReadDWord(self.fb)
                    if dwHeight >= 1:
                        self.fb.seek(0x18, 0)
                        dwPixelSize = tiohrReadDWord(self.fb)
                        if dwPixelSize >= 1:
                            self.fb.seek(0x1C, 0)
                            dwMipMapCount = tiohrReadDWord(self.fb)
                            if dwMipMapCount <= 0xA:
                                return
        raise Exception(f"Заголовки файла {self.file_name} повреждены!!!")

    def _parse_data(self):
        self.data = bytearray()
        self.fb.seek(0xA0, 0)
        data_size = self.hWidth * self.hHeight
        mip_map_counter = 0
        while True:
            for _ in range(data_size):
                data_chunk = self.fb.read(self.hPixelSize)
                [self.data.append(new_byte) for new_byte in data_chunk]
            if mip_map_counter == self.hMipMapCount:
                break
            mip_map_counter += 1
            data_size = data_size >> 2

    def _create_csim_mod(self):
        self.csim_mod = CSIM_Mod()
        self.csim_mod.file_path = self.file_path
        self.csim_mod.file_name = self.file_name
        self.csim_mod.dds_pixel_format = self.dds_pixel_format
        self.csim_mod.hWidth = self.hWidth
        self.csim_mod.hHeight = self.hHeight
        self.csim_mod.hPixelSize = self.hPixelSize
        self.csim_mod.hMipMapCount = self.hMipMapCount
        self.csim_mod.hFormatCharCount = self.hFormatCharCount
        self.csim_mod.hFormat = self.hFormat
        self.csim_mod.hFormatChannelBitCounts = self.hFormatChannelBitCounts
        self.csim_mod.data = self.data


class CSI2DDSConverter:
    def __init__(self, csi_file_path):
        self.csi_file_path = csi_file_path
        self.csim_mod: Union[CSIM_Mod, None] = None
        self.dds_model: Union[DDSModel, None] = None
        self.dds_buffer: Union[BytesIO, None] = None

    def convert_to_file(self, output_path, file_name: Union[str, None] = None):
        if os.path.isdir(output_path) is False:
            raise Exception("Для сохранения DDS файла надо указать ПАПКУ вывода.")
        self._convert()
        if file_name:
            if file_name.find('.dds') == -1:
                file_name += ".dds"
            file_path = os.path.join(output_path, file_name)
        else:
            file_path = os.path.join(output_path, self.dds_model.file_name)
        byte_array = self.dds_buffer.getvalue()
        with open(file_path, "w+b") as f:
            f.write(byte_array)
        self.dds_buffer.close()

    def convert_to_buffer(self):
        self._convert()
        return self.dds_buffer

    def _convert(self):
        csi_parser = CSIFileParser(self.csi_file_path)
        csi_parser.parse_file()
        self.csim_mod = csi_parser.get_parsing_result()
        if self.csim_mod is None:
            raise Exception("Poch None0")
        self._init_dds_model()
        self._set_dds_headers()
        self._write_dds_in_buffer()

    def _init_dds_model(self):
        self.dds_model = DDSModel()
        csi_file_name = self.csim_mod.file_name
        self.dds_model.file_name = csi_file_name.replace(".csi", ".dds")
        self.dds_model.data = self.csim_mod.data

    def _write_dds_in_buffer(self):
        self.dds_buffer = BytesIO()
        self._write_headers()
        self._write_data()

    # SET HEADERS BLOCK
    def _set_dds_headers(self):
        # dwFlags
        self._set_dds_header_dwFlags()
        # dwHeight
        self.dds_model.dwHeight = self.csim_mod.hHeight
        # dwWidth
        self.dds_model.dwWidth = self.csim_mod.hWidth
        # dwMipMapCount
        self.dds_model.dwMipMapCount = self.csim_mod.hMipMapCount
        # DDS_PIXELFORMAT
        self._set_dds_pixelformat_headers()
        # dwCaps
        self._set_dds_header_dwCaps()

    def _set_dds_header_dwFlags(self):
        # UKNOWN_FLAG = 0x7 - не знаю что за флаг. Гении на Майкрософт не дают информацию в документации
        # DDSD_PIXELFORMAT = 0x1000 - флаг говорит, что DDS использует заголовки PIXELFORMAT.
        # upd: DDS_HEADER_FLAGS_TEXTURE = 0x00001007 - флаг текстуры, вместо DDSD_PIXELFORMAT и UNKNOWN. Найден в исходника d8x8 на гитхабе.
        DDS_HEADER_FLAGS_TEXTURE = 0x00001007
        # DDSD_MIPMAPCOUNT = 0x00020000 - флаг говорит, что DDS использует MIPMAP.
        DDSD_MIPMAPCOUNT = 0x00020000
        dwFlags = 0
        dwFlags |= DDS_HEADER_FLAGS_TEXTURE
        if self.csim_mod.hMipMapCount > 0:
            # Указывать DDSD_MIPMAPCOUNT, если csi использует MipMap
            dwFlags |= DDSD_MIPMAPCOUNT
        self.dds_model.dwFlags = dwFlags

    def _set_dds_header_dwCaps(self):
        # DDSCAPS_TEXTURE = 0x1000 - обязательный флаг.
        DDSCAPS_TEXTURE = 0x1000
        # DDS_SURFACE_FLAGS_MIPMAP = 0x00400008 - флаг включается, если есть MIP MAP
        # Старое название флагов DDSCAPS_MIPMAP = 0x400000 и DDSCAPS_COMPLEX = 0x8
        DDS_SURFACE_FLAGS_MIPMAP = 0x00400008
        dwCaps = 0
        dwCaps |= DDSCAPS_TEXTURE
        if self.csim_mod.hMipMapCount > 0:
            dwCaps |= DDS_SURFACE_FLAGS_MIPMAP
        self.dds_model.dwCaps = dwCaps

    def _set_dds_pixelformat_headers(self):
        self._set_dds_pixelformat_header_dwFlags()
        # dwRGBBitCount
        (
            self.dds_model.ddspf.dwRGBBitCount,
            self.dds_model.ddspf.dwRBitMask,
            self.dds_model.ddspf.dwGBitMask,
            self.dds_model.ddspf.dwBBitMask,
            self.dds_model.ddspf.dwABitMask
        ) = DDSPF_STRUCT[self.csim_mod.dds_pixel_format]

    def _set_dds_pixelformat_header_dwFlags(self):
        # DDPF_RGB = 0x40 - флаг говорит, что DDS содержит несжатые данные RGB.
        DDPF_RGB = 0x40
        # DDPF_ALPHAPIXELS = 0x01 - флаг говорит, что текстура содержит альфа-данные.
        DDPF_ALPHAPIXELS = 0x01
        dwFlags = 0
        dwFlags |= DDPF_RGB
        # Проверим есть ли альфа-канал в CSI. Если есть, то добавим флаг DDPF_ALPHAPIXELS
        for i in range(self.csim_mod.hFormatCharCount):
            char_byte = self.csim_mod.hFormat[i]
            # проверим есть ли в (A)RGB байт 0x41(A)
            if char_byte == 0x41:
                dwFlags |= DDPF_ALPHAPIXELS
                break
        self.dds_model.ddspf.dwFlags = dwFlags

    # WRITE HEADERS BLOCK
    def _write_headers(self):
        try:
            # dwMagic
            tiohbWriteDWord(self.dds_buffer, self.dds_model.dwMagic)
            # dwSize
            tiohbWriteDWord(self.dds_buffer, self.dds_model.dwSize)
            # dwFlags
            tiohbWriteDWord(self.dds_buffer, self.dds_model.dwFlags)
            # dwHeight
            tiohbWriteDWord(self.dds_buffer, self.dds_model.dwHeight)
            # dwWidth
            tiohbWriteDWord(self.dds_buffer, self.dds_model.dwWidth)
            # csi не имеет dwPitchOrLinearSize и dwDepth. Записываем пустые значения
            [tiohbWriteDWord(self.dds_buffer, 0) for _ in range(2)]
            # dwMipMapCount
            tiohbWriteDWord(self.dds_buffer, self.dds_model.dwMipMapCount)
            # dwReserved1[11] по 4 байт зарезервированы DDS
            [tiohbWriteDWord(self.dds_buffer, 0) for _ in range(11)]
            # ddspf.dwSize
            tiohbWriteDWord(self.dds_buffer, self.dds_model.ddspf.dwSize)
            # ddspf.dwFlags
            tiohbWriteDWord(self.dds_buffer, self.dds_model.ddspf.dwFlags)
            # ddspf.dwFourCC в csi отсутсвует?
            tiohbWriteDWord(self.dds_buffer, 0)
            # ddspf.dwRGBBitCount
            tiohbWriteDWord(self.dds_buffer, self.dds_model.ddspf.dwRGBBitCount)
            # ddspf.dwRBitMask
            tiohbWriteDWord(self.dds_buffer, self.dds_model.ddspf.dwRBitMask)
            # ddspf.dwGBitMask
            tiohbWriteDWord(self.dds_buffer, self.dds_model.ddspf.dwGBitMask)
            # ddspf.dwBBitMask
            tiohbWriteDWord(self.dds_buffer, self.dds_model.ddspf.dwBBitMask)
            # ddspf.dwABitMask
            tiohbWriteDWord(self.dds_buffer, self.dds_model.ddspf.dwABitMask)
            # dwCaps
            tiohbWriteDWord(self.dds_buffer, self.dds_model.dwCaps)
            # dwCaps2 в csi отсутствует? dwCaps3, dwCaps4, dwReserved2 - в резерве
            [tiohbWriteDWord(self.dds_buffer, 0) for _ in range(4)]
        except Exception as ex:
            raise ex

    def _write_data(self):
        csim_fb = BytesIO(self.csim_mod.data)
        data_size = self.dds_model.dwWidth * self.dds_model.dwHeight
        mip_map_counter = 0
        while True:
            for _ in range(data_size):
                data_chunk = csim_fb.read(self.csim_mod.hPixelSize)
                self.dds_buffer.write(data_chunk)
            if mip_map_counter == self.csim_mod.hMipMapCount:
                break
            mip_map_counter += 1
            data_size = data_size >> 2
        csim_fb.close()