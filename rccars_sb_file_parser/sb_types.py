from .sb_enum import MOD


class SuperMod:
    def add_child_mod_in_list(self, list_name, child_mod):
        try:
            self.__getattribute__(list_name)
        except Exception:
            self.__setattr__(list_name, list())
        self.__getattribute__(list_name).append(child_mod)

    def add_new_attribute(self, attr, data):
        # Много неизвестных чанков. По мере нахождения их значения, будет сложно 
        # переименовывать атрибуты в каждом объекте.. Проще их добавлять при нахождении.
        try:
            self.__getattribute__(attr)
        except Exception:
            self.__setattr__(attr, data)

    def get_child_mod_list(self, MOD_TYPE):
        # Возвращает дочерний список MOD, при отсутсвии возваращает None
        try:
            return self.__getattribute__(f"{MOD_TYPE}_mods_list")
        except Exception:
            return None


class OOOO_Mod(SuperMod):
    def __init__(self):
        self.mod_type = '0000'


class DESC_Mod(SuperMod):
    def __init__(self):
        self.mod_type = 'DESC'


class MESH_Mod(SuperMod):
    def __init__(self):
        self.mod_type = 'MESH'

    def get_face_coords_list(self):
        face_coords_list = []
        for fd in self.face_list:
            face_coords_list.append(fd['face_coords'])
        return face_coords_list

class LITD_Mod(SuperMod):
    def __init__(self):
        self.mod_type = 'LITD'


class CAMR_Mod(SuperMod):
    def __init__(self):
        self.mod_type = 'CAMR'


class TEXR_Mod(SuperMod):
    def __init__(self):
        self.mod_type = 'TEXR'


class MATR_Mod(SuperMod):
    def __init__(self):
        self.mod_type = 'MATR'


class GLTX_Mod(SuperMod):
    def __init__(self):
        self.mod_type = 'GLTX'


class HHID_Mod(SuperMod):
    def __init__(self):
        self.mod_type = 'HHID'


class COLL_Mod(SuperMod):
    def __init__(self):
        self.mod_type = 'COLL'


class EMPT_Mod(SuperMod):
    def __init__(self):
        self.mod_type = 'EMPT'


class INST_Mod(SuperMod):
    def __init__(self):
        self.mod_type = 'INST'


class MARK_Mod(SuperMod):
    def __init__(self):
        self.mod_type = 'MARK'


class ASEQ_Mod(SuperMod):
    def __init__(self):
        self.mod_type = 'ASEQ'


class ANIM_Mod(SuperMod):
    def __init__(self):
        self.mod_type = 'ANIM'


class SPLN_Mod(SuperMod):
    def __init__(self):
        self.mod_type = 'SPLN'


class DYNM_Mod(SuperMod):
    def __init__(self):
        self.mod_type = 'DYNM'


class CNST_Mod(SuperMod):
    def __init__(self):
        self.mod_type = 'CNST'


class CVOL_Mod(SuperMod):
    def __init__(self):
        self.mod_type = 'CVOL'


class EVOL_Mod(SuperMod):
    def __init__(self):
        self.mod_type = 'EVOL'


class SCRI_Mod(SuperMod):
    def __init__(self):
        self.mod_type = 'SCRI'


class MODL_Mod(SuperMod):
    def __init__(self):
        self.mod_type = 'MODL'


class MSHD_Mod(SuperMod):
    def __init__(self):
        self.mod_type = 'MSHD'


class FOLD_Mod(SuperMod):
    def __init__(self):
        self.mod_type = 'FOLD'


class SOND_Mod(SuperMod):
    def __init__(self):
        self.mod_type = 'SOND'


class SNCH_Mod(SuperMod):
    def __init__(self):
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
