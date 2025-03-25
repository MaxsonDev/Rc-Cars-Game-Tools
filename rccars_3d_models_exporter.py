import bpy
import math

from mathutils import Matrix
from rccars_sb_file_parser import SBFileParser

FILE_PATH = "C:\\new folder\\Fixed China Crack Version\\RCCarsDB\\stone.sb"


def prepare_models(DESC_DATA):
    MODL_list = DESC_DATA.get_child_mod_list('MODL')
    if MODL_list is None:
        raise "SB файл не имеет MODL для экспорта"
    prepare_data = []
    for MODL in MODL_list:
        modl_data = {}
        modl_data["modl_name"] = MODL.name
        MESH_LIST = MODL.get_child_mod_list('MESH')
        if MESH_LIST is None:
            continue
        mesh_prepare_list = []
        # цикл будет работать пока не закончатся MESH
        while MESH_LIST:
            # 1 Берем MESH из MESH_LIST
            MESH = MESH_LIST.pop(0)
            # 1.1 Проверяем имеет ли MESH данные на отрисовку
            is_visible = None
            try:
                MESH.face_count
                is_visible = True
            except:
                is_visible = False
            # 1.2 Если да, то добавляем в список мешей модели
            if is_visible:
                mesh_prepare_list.append(prepare_mesh(MESH))
            # 2. Смотрим имеет ли MESH дочерние MESH.
            new_mesh_list = MESH.get_child_mod_list('MESH')
            # 2.1 Если new_mesh_list не None и имеет элементы в списке
            if new_mesh_list is not None and len(new_mesh_list) != 0:
                # 2.2 то добавляем эти MESH в MESH_LIST,
                # чтобы их поймать в этом цикле при следующей итерации.
                for new_mesh in new_mesh_list:
                    MESH_LIST.append(new_mesh)
        modl_data['mesh_list'] = mesh_prepare_list
        prepare_data.append(modl_data)
    return prepare_data


def prepare_mesh(MESH):
    mesh_data = {}
    mesh_data['mesh_name'] = MESH.name
    mesh_data['vertex_list'] = MESH.vertex_list
    mesh_data['face_coords_list'] = MESH.get_face_coords_list()
    mesh_data['transform'] = MESH.transform
    return mesh_data

def get_desc_data(file_path):
    sb_parser = SBFileParser(file_path)
    sb_parser.parse_file()
    return sb_parser.get_desc_data_result()


def build_models(modl):
    # создадим коллекцию
    col = bpy.data.collections.new(modl['modl_name'])
    bpy.context.scene.collection.children.link(col)
    # создадим меши
    for m in modl['mesh_list']:
        # if m.is_blank_mesh:
        #    continue
        # создаем меш
        mesh = bpy.data.meshes.new(m['mesh_name'])
        mesh.from_pydata(m['vertex_list'], [], m['face_coords_list'])
        # создаем объект. к нему привязывается меш.
        obj = bpy.data.objects.new(m['mesh_name'], mesh)
        # obj.location = m.location
        # создаем матрицу позиции
        translation_matrix = Matrix.Translation(m['transform']['location'])
        obj.matrix_world @= translation_matrix
        # матрица вращения. задается отдельными осями
        for n, axis in enumerate('XYZ'):
            rotation_matrix = Matrix.Rotation(math.radians(m['transform']['rotation'][n]), 4, axis)
            obj.matrix_world @= rotation_matrix
        # матрица масштабирования. задается отдельными осями
        for n, axis in enumerate([(1,0,0), (0,1,0), (0,0,1)]):
            scale_matrix = Matrix.Scale(m['transform']['scale'][n], 4, axis)
            obj.matrix_world @= scale_matrix
        # добавляем объект в коллекцию
        bpy.data.collections[modl['modl_name']].objects.link(obj)


def main(file_path):
    DESC_DATA = get_desc_data(file_path)
    prepare_data = prepare_models(DESC_DATA)
    for modl in prepare_data:
        build_models(modl)


main(FILE_PATH)
