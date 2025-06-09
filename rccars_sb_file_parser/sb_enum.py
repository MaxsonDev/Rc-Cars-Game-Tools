from enum import Enum


class MOD(Enum):
    OOOO = 0x30303030
    DESC = 0x44455343
    MESH = 0x4d455348
    LITD = 0x4c495444
    CAMR = 0x43414d52
    TEXR = 0x54455852
    MATR = 0x4d415452
    GLTX = 0x474c5458
    HHID = 0x48484944
    COLL = 0x434f4c4c
    EMPT = 0x454d5054
    INST = 0x494e5354
    MARK = 0x4d41524b
    ASEQ = 0x41534551
    ANIM = 0x414e494d
    SPLN = 0x53504c4e
    DYNM = 0x44594e4d
    CNST = 0x434e5354
    CVOL = 0x43564f4c
    EVOL = 0x45564f4c
    SCRI = 0x53435249
    MODL = 0x4d4f444c
    MSHD = 0x4d534844
    FOLD = 0x464f4c44
    SOND = 0x534f4e44
    SNCH = 0x534e4348

    @classmethod
    def get_mod_by_value(cls, value):
        for mod in cls.__iter__():
            if mod.value == value:
                return mod.name

    @classmethod
    def get_value_by_mod(cls, mod_name):
        if mod_name == 0000 or mod_name == "OOOO":
            return cls.OOOO.value
        for mod in cls.__iter__():
            if mod.name == mod_name:
                return mod.value
        return None
