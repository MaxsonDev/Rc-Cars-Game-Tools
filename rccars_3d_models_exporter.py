import os
import bpy
import bmesh
import math

from mathutils import Matrix
from rccars_sb_file_parser import SBFileParser

SB_FILE_PATH = ""

class RCCarsExportToBlender:
    def __init__(self, 
                 file_path,
                 flag_mesh_create_mesh=False,
                 flag_mesh_create_visual_box=False, 
                 flag_mesh_create_collision_box=False, 
                 flag_mesh_create_3DPoints=False,
                 var_mesh_create_meshes_by_IDs=None,
                 flag_coll_build_matrix=False,
                 flag_coll_build_only_voxel_with_collision=True,
                 flag_coll_create_3DPoints=False,
                 var_coll_row_start=None,
                 var_coll_row_end=None,
                 flag_hhid_build_matrix=False,
                 flag_hhid_build_only_voxel_with_collision=True,
                 flag_hhid_create_3DPoints=False,
                 var_hhid_row_start=None,
                 var_hhid_row_end=None,
                 flag_evol_on=False,
                 flag_evol_build_volume_prism=False
                 ):
        self.file_path = file_path
        self.current_MODL = None
        self.parser = None
        # Params
        # MESH
        self.flag_mesh_create_mesh = flag_mesh_create_mesh
        self.flag_mesh_create_visual_box = flag_mesh_create_visual_box
        self.flag_mesh_create_collision_box = flag_mesh_create_collision_box
        self.flag_mesh_create_3DPoints = flag_mesh_create_3DPoints
        self.var_mesh_create_meshes_by_IDs = var_mesh_create_meshes_by_IDs
        # COLL
        self.flag_coll_build_matrix = flag_coll_build_matrix
        self.flag_coll_build_only_voxel_with_collision = flag_coll_build_only_voxel_with_collision
        self.flag_coll_create_3DPoints = flag_coll_create_3DPoints
        self.var_coll_row_start = var_coll_row_start
        self.var_coll_row_end = var_coll_row_end
        # HHID
        self.flag_hhid_build_matrix = flag_hhid_build_matrix
        self.flag_hhid_build_only_voxel_with_collision = flag_hhid_build_only_voxel_with_collision
        self.flag_hhid_create_3DPoints = flag_hhid_create_3DPoints
        self.var_hhid_row_start = var_hhid_row_start
        self.var_hhid_row_end = var_hhid_row_end
        # EVOL
        self.flag_evol_on = flag_evol_on
        self.flag_evol_build_volume_prism = flag_evol_build_volume_prism
        # name vars
        self.name_visual_box = 'visual_box'
        self.name_collision_box = 'collision_box'
        self.name_3DPoint = '3DPoint'
        # self.name_VOXEL = 'VOXEL'

        self._check_class_args()
    
    def _check_class_args(self):
        if os.path.exists(self.file_path) is False:
            raise FileNotFoundError('Передайте путь к .sb файлу в аргумент file_path.')
        # MESH
        if self.var_mesh_create_meshes_by_IDs is not None and type(self.var_mesh_create_meshes_by_IDs) not in [int, list]:
            raise Exception("Значение 'var_mesh_create_meshes_by_IDs' может быть только целыми числами >= 0, списком или None.")
        if type(self.var_mesh_create_meshes_by_IDs) == int:
            self.var_mesh_create_meshes_by_IDs = [self.var_mesh_create_meshes_by_IDs]
        # COLL
        if self.var_coll_row_start is not None:
            if type(self.var_coll_row_start) != int or self.var_coll_row_start <= 0:
                raise Exception("Значения 'var_coll_row_start' и 'var_coll_row_end' могут быть только целыми положительными числами больше 0.")
        if self.var_coll_row_end is not None:
            if type(self.var_coll_row_end) != int or self.var_coll_row_end <= 0:
                raise Exception("Значения 'var_coll_row_start' и 'var_coll_row_end' могут быть только целыми положительными числами больше 0.")
        # HHID  
        if self.var_hhid_row_start is not None:
            if type(self.var_hhid_row_start) != int or self.var_hhid_row_start <= 0:
                raise Exception("Значения 'var_hhid_row_start' и 'var_hhid_row_end' могут быть только целыми положительными числами больше 0.")
        if self.var_hhid_row_end is not None:
            if type(self.var_hhid_row_end) != int or self.var_hhid_row_end <= 0:
                raise Exception("Значения 'var_hhid_row_start' и 'var_hhid_row_end' могут быть только целыми положительными числами больше 0.")
        

    def run_export(self):
        print("Скрипт запущен!")
        print("Парсим SB файл.")
        self.parser = SBFileParser(self.file_path)
        self.parser.parse_file()
        print("Парсинг SB файла завершен.")
        DESC = self.parser.get_parsing_result()
        if DESC.mod_type != 'DESC':
            raise Exception("Корневым MOD должен быть DESC.")
        print("Начинаем перенос объектов из SB файла в Blender.")
        self._open_all_children(DESC)

    def _open_all_children(self, mod_obj):
        if mod_obj.mod_type == 'MODL':
            self.prepare_MODL(mod_obj)
        elif mod_obj.mod_type == 'MESH':
            self.prepare_MESH(mod_obj)
        elif mod_obj.mod_type == 'COLL':
            if self.flag_coll_build_matrix:
                self.prepare_COLL(mod_obj)
        elif mod_obj.mod_type == 'HHID':
            if self.flag_hhid_build_matrix:
                self.prepare_HHID(mod_obj)
        elif mod_obj.mod_type == 'EVOL':
            if self.flag_evol_on:
                if self.flag_evol_build_volume_prism:
                    self.prepare_EVOL(mod_obj)

        for mod_type in self.parser.mods_str_list:
            child_mod_list = mod_obj.get_child_mod_list(mod_type)
            if child_mod_list is None:
                continue
            for child_mod in child_mod_list:
                self._open_all_children(child_mod)
    
    def prepare_MODL(self, mod_obj):
        """
        Всё что задает MODL - это название коллекций в Blender для более удобной каталогизации объектов.
        """
        # закрепим текущий MODL объект
        self.current_MODL = mod_obj
        collection_name = f"{mod_obj.get_mod_name()}"
        create_new_collection(collection_name)
        # MESH_VISUAL_BOX
        if self.flag_mesh_create_visual_box:
            # создадим коллекцию
            col_name = f"{collection_name}_{self.name_visual_box}s"
            create_new_collection(col_name)
            # создадим материал, если его нет
            if self.name_visual_box not in [i.name for i in bpy.data.materials]:
                # #F5E52DFF
                color = (0.915, 0.783539, 0.0262414, 1)
                create_new_transparent_material(self.name_visual_box, color)
        # MESH_COLLISION_BOX  
        if self.flag_mesh_create_collision_box:
            col_name = f"{collection_name}_{self.name_collision_box}s"
            create_new_collection(col_name)
            # создадим материал, если его нет
            if self.name_collision_box not in [i.name for i in bpy.data.materials]:                
                # #2CE5E5FF
                color = (0.025186, 0.783539, 0.784, 1)
                create_new_transparent_material(self.name_collision_box, color)
        # 3DPoints
        if self.flag_mesh_create_3DPoints or self.flag_coll_create_3DPoints or self.flag_hhid_create_3DPoints:
            col_name = f"{collection_name}_{self.name_3DPoint}s"
            create_new_collection(col_name)
            # создадим материал, если его нет
            if self.name_3DPoint not in [i.name for i in bpy.data.materials]:                
                # #2CE5E5FF
                color = (0.768829, 0.0638148, 0.80094, 1)
                create_new_transparent_material(self.name_3DPoint, color)
        # COLL

    def prepare_MESH(self, mod_obj):
        if self.flag_mesh_create_mesh and False not in [mod_obj.is_chunk_exist('0617h'), mod_obj.is_chunk_exist('7411h')]:
            collection_name = self.current_MODL.get_mod_name()
            mesh_name = f'{mod_obj.get_mod_name()}_id{mod_obj.get_mod_id()}'
            transform_data = mod_obj.get_transform_data()
            vertex_list = mod_obj.get_vertex_list()
            face_indexes_list = mod_obj.get_face_indexes_list()
            obj = create_new_mesh(collection_name, mesh_name, vertex_list, face_indexes_list, transform_data)
            uv_maps = mod_obj.get_uv_maps()
            if uv_maps:
                create_uv_maps(obj, uv_maps)
            print(f"MESH {mesh_name} создан.")
        
        if self.var_mesh_create_meshes_by_IDs is not None:
            if mod_obj.get_mod_id() not in self.var_mesh_create_meshes_by_IDs:
                return

        if self.flag_mesh_create_visual_box and mod_obj.is_chunk_exist('8215h'):
            collection_name = f"{self.current_MODL.get_mod_name()}_{self.name_visual_box}s"
            mesh_name = f"{mod_obj.get_mod_name()}_{self.name_visual_box}_id{mod_obj.get_mod_id()}"
            face_indexes_list = [[0,1,3,2],[0,1,7,6],[0,2,4,6],[5,3,2,4],[5,3,1,7],[5,7,6,4]]
            vertex_list = mod_obj.get_mesh_visual_box_vertex_coords()
            create_mesh_visual_box(collection_name, mesh_name, self.name_visual_box, vertex_list, face_indexes_list)
            print(f'MESH_HHID_BOX {mesh_name} создан.')

        if self.flag_mesh_create_collision_box and mod_obj.is_chunk_exist('8216h'):
            collection_name = f"{self.current_MODL.get_mod_name()}_{self.name_collision_box}s"
            mesh_name = f"{mod_obj.get_mod_name()}_{self.name_collision_box}_id{mod_obj.get_mod_id()}"
            transform_data = mod_obj.get_mesh_collision_box_transform_data()
            create_mesh_collision_box(collection_name, mesh_name, self.name_collision_box, transform_data)
            print(f'MESH_COLL_BOX {mesh_name} создан.')
        
        if self.flag_mesh_create_3DPoints:
            # Список чанков 3D точек
            # 7027h хранится в 0617h
            # UPD: 0617h убрал из списка. слишком странно создаются точки(не ошибка,а именно непонятно почему все 3Д точки в районе 0 координаты и далеко от фэйсов меша.)
            # Хотя скорее всего так работает 3DMax, в котором работали разрааботчики
            collection_name = f"{self.current_MODL.get_mod_name()}_{self.name_3DPoint}s"
            points3D_chunks_list = ["7414h", "7030h", "7029h"]
            self.create_3DPoints_of_mod(mod_obj, points3D_chunks_list, collection_name)


    def prepare_COLL(self, mod_obj):
        print("Start Create collision matrix.")
        voxel_color_name = 'coll_voxel_color'
        # создадим коллекцию
        collection_name = f"{self.current_MODL.get_mod_name()}_COLL"
        create_new_collection(collection_name)
        # создадим материал, если его нет
        if voxel_color_name not in [i.name for i in bpy.data.materials]:                
            # #81E7D1FF
            color = (0.21945, 0.800694, 0.635172, 1)
            create_new_transparent_material(voxel_color_name, color)

        if self.flag_coll_create_3DPoints:
            # создадим 3D точки коллизии
            points3D_chunks_list = ["7099h", "709Ah"]
            self.create_3DPoints_of_mod(mod_obj, points3D_chunks_list, collection_name)
        # Построим матрицу коллизии.
        collision_matrix_809Dh = mod_obj.data_809Dh
        # 1. Берем значение кол-ва вокселей на ось
        x_vox_length, z_vox_length, y_vox_length = mod_obj.get_data_by_chunk('3498h')
        # 2. Посчитаем размер 1го вокселя
        x_vox_size, z_vox_size, y_vox_size = mod_obj.calculate_coll_voxel_size()
        if self.var_coll_row_start is not None:
            x_vox_count = self.var_coll_row_start - 1
        else:
            x_vox_count = 0
        while x_vox_count < x_vox_length:
            if self.var_coll_row_start is not None and self.var_coll_row_end is not None:
                if self.var_coll_row_start <= x_vox_count and x_vox_count == self.var_coll_row_end:
                    break
            z_vox_count = 0
            while z_vox_count < z_vox_length:
                y_vox_count = 0
                while y_vox_count < y_vox_length:
                    point_data_809Dh = y_vox_count + y_vox_length * (z_vox_count + z_vox_length * x_vox_count)
                    if collision_matrix_809Dh[point_data_809Dh] == 0 and self.flag_coll_build_only_voxel_with_collision:
                        y_vox_count += 1
                        continue
                    vertex_list = calculate_coll_voxel_vertex_coords(mod_obj.get_data_by_chunk('7099h'), x_vox_count, z_vox_count, y_vox_count, x_vox_size, z_vox_size, y_vox_size)
                    # создадим имя вокселя
                    voxel_name = f"COLL_VOX_COL{x_vox_count + 1}_ROW{z_vox_count + 1}_POS{y_vox_count + 1}_ID{point_data_809Dh + 1}"
                    # зададим флаг для отрисовки материала
                    isHaveColl = False
                    if collision_matrix_809Dh[point_data_809Dh] != 0:
                        isHaveColl = True
                    create_voxel_for_matrix(collection_name, voxel_name, voxel_color_name, vertex_list, isHaveColl)
                    y_vox_count += 1
                z_vox_count += 1
            x_vox_count += 1
    
    def prepare_HHID(self, mod_obj):
        print("Start Create hhide matrix.")
        voxel_color_name = 'hhid_voxel_color'
        # создадим коллекцию
        collection_name = f"{self.current_MODL.get_mod_name()}_HHID"
        create_new_collection(collection_name)
        # создадим материал, если его нет
        if voxel_color_name not in [i.name for i in bpy.data.materials]:                
            # #E780D1FF
            color = (0.799098, 0.21586, 0.637597, 1)
            create_new_transparent_material(voxel_color_name, color)
        if self.flag_hhid_create_3DPoints:
            # создадим 3D точки "куба" коллизии
            points3D_chunks_list = ["7091h", "7092h"]
            self.create_3DPoints_of_mod(mod_obj, points3D_chunks_list, collection_name)
        # Построим матрицу HHID
        # 1. Берем значение кол-ва вокселей на ось
        x_vox_length, z_vox_length, y_vox_length = mod_obj.get_data_by_chunk('3490h')
        # 2. Получим общее количесвто вокселей
        matrix_size = x_vox_length * z_vox_length * y_vox_length
        # 3. Создадим массив из 0 значений для матрицы
        hhide_matrix = [0 for _ in range(matrix_size)]
        # 4. С помощью указателей из data_8094h в hhid_matrix заменим 0 на 1
        for data in mod_obj.get_data_by_chunk('8094h'):
            # берем индексы матрицы
            x_vox, z_vox, y_vox = data['xzy_vox_point']
            # высчитываем указатель на массив
            point = y_vox + y_vox_length * (z_vox + x_vox * z_vox_length)
            # заменяем на 1
            hhide_matrix[point] = 1
        # 5. Посчитаем размер 1го вокселя
        x_vox_size, z_vox_size, y_vox_size = mod_obj.calculate_hhid_voxel_size()
        # 6. Отрисуем матрицу HHID
        if self.var_hhid_row_start is not None:
            x_vox_count = self.var_hhid_row_start - 1
        else:
            x_vox_count = 0
        while x_vox_count < x_vox_length:
            if self.var_hhid_row_start is not None and self.var_hhid_row_end is not None:
                if self.var_hhid_row_start <= x_vox_count and x_vox_count == self.var_hhid_row_end:
                    break
            z_vox_count = 0
            while z_vox_count < z_vox_length:
                y_vox_count = 0
                while y_vox_count < y_vox_length:
                    point = y_vox_count + y_vox_length * (z_vox_count + z_vox_length * x_vox_count)
                    if hhide_matrix[point] == 0 and self.flag_hhid_build_only_voxel_with_collision:
                        y_vox_count += 1
                        continue
                    vertex_list = calculate_hhid_voxel_vertex_coords(mod_obj.get_data_by_chunk('7091h'), x_vox_count, z_vox_count, y_vox_count, x_vox_size, z_vox_size, y_vox_size)
                    # создадим имя вокселя
                    voxel_name = f"HHID_VOX_COL{x_vox_count + 1}_ROW{z_vox_count + 1}_POS{y_vox_count + 1}_ID{point + 1}"
                    # зададим флаг для отрисовки материала
                    ## при переносе данных в аддон сделать однострочное условие
                    isHaveColl = False
                    if hhide_matrix[point] != 0:
                        isHaveColl = True
                    create_voxel_for_matrix(collection_name, voxel_name, voxel_color_name, vertex_list, isHaveColl)
                    y_vox_count += 1
                z_vox_count += 1
            x_vox_count += 1

    def prepare_EVOL(self, mod_obj):
        # создадим коллекцию для EVOL
        collection_name = f"{mod_obj.parent_mod.mod_type}_{mod_obj.parent_mod.get_mod_name()}"
        create_new_collection(collection_name)
        # будем для теста создавать 3DPoint точки, а не полноценную призму
        # для этого делаем из чанка 80D4h сисок 3DPoint
        prisma_coords = mod_obj.get_data_by_chunk('80D4h')
        axis_indexes = {
            'X': [2, 4, 6, 8],
            'Z': [0, 1],
            'Y': [3, 5, 7, 9]
        }
        points3D_list = []
        for i in range(4):
            for z in range(2):
                point_coord = [
                    prisma_coords[axis_indexes['X'][i]],
                    prisma_coords[axis_indexes['Z'][z]],
                    prisma_coords[axis_indexes['Y'][i]]
                ]
                points3D_list.append(point_coord)
        for num, point3D in enumerate(points3D_list):
            point_name = f"{mod_obj.mod_type}_{mod_obj.get_mod_name()}_prizm_ind{num}"
            create_3DPoint(collection_name, point_name, self.name_3DPoint, point3D)

    def create_3DPoints_of_mod(self, mod_obj, points3D_chunks_list, collection_name):
        if mod_obj.get_mod_name() is not None:
            obj_name = f"{mod_obj.get_mod_name()}_{self.name_3DPoint}"
        else:
            obj_name = f"{self.name_3DPoint}"

        for chunk in points3D_chunks_list:
            if mod_obj.is_chunk_exist(chunk) is False:
                continue
            # данные чанка
            chunk_data = mod_obj.get_data_by_chunk(chunk)
            if chunk == "7414h":
                for num, point3D in enumerate(chunk_data):
                    point_name = f'{obj_name}_{chunk}_{num + 1}'
                    create_3DPoint(collection_name, point_name, self.name_3DPoint, point3D)
                continue
            elif chunk == "0617h":
                # В условии чанк есть, но не используется.
                # Это чанк, который хранит данные о фейсах меша.
                # Надо взять все фэйсы и взять оттуда 3DPoint
                for num, face_data in enumerate(chunk_data):
                    point_name = f'{obj_name}_7027h_face_{num + 1}'
                    point3D = face_data['data_7027h']
                    create_3DPoint(collection_name, point_name, self.name_3DPoint, point3D)
                continue
            # Проверим 3D точки на наличие нулевых координат,
            # чтобы не создавать пустышки
            zero_check = [i for i in chunk_data if i != 0.0]
            if len(zero_check) == 0:
                continue
            point_name = f'{obj_name}_{chunk}'
            create_3DPoint(collection_name, point_name, self.name_3DPoint, chunk_data)


def create_voxel_for_matrix(collection_name, voxel_name, material_name, vertex_list, isHaveColl):
    face_indexes_list = [[0, 2, 3, 1], [2, 6, 7, 3], [6, 4, 5, 7], [4, 0, 1, 5], [0, 4, 6, 2], [1, 3, 7 ,5]]
    obj = create_new_mesh(collection_name, voxel_name, vertex_list, face_indexes_list)
    if isHaveColl:
        # возьмем материал
        mat = bpy.data.materials.get(material_name)
        # добавим в объект
        obj.data.materials.append(mat)
    print("Sozdan", voxel_name)

"""
def create_voxel_for_matrix(collection_name, voxel_name, material_name, voxel_coords, isHaveColl):
    # сделаем коллекцию активной
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[collection_name]
    # создадим примитивный куб
    bpy.ops.mesh.primitive_cube_add(align='WORLD')
    # он автоматически становится активным после создания - возьмем его из актива
    obj = bpy.context.view_layer.objects.active
    # переименуем объект
    obj.name = voxel_name
    # переименуем меш
    obj.data.name = voxel_name
    # установим локацию
    set_object_transform_data(obj, location=voxel_coords, scale=[0.25, 0.25, 0.25])
    if isHaveColl:
        # возьмем материал
        mat = bpy.data.materials.get(material_name)
        # добавим в объект
        obj.data.materials.append(mat)    
"""

def create_3DPoint(collection_name, point_name, material_name, point3D):
    # сделаем коллекцию активной
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[collection_name]
    # создадим примитивную окружность
    bpy.ops.mesh.primitive_uv_sphere_add()
    # меш автоматически становится активным после создания - возьмем его из актива
    obj = bpy.context.view_layer.objects.active
    # переименуем объект
    obj.name = point_name
    # переименуем меш
    obj.data.name = point_name
    # зададим объекту данные трансформации
    set_object_transform_data(obj, location=point3D, scale=[0.25, 0.25, 0.25])
    # возьмем материал
    mat = bpy.data.materials.get(material_name)
    # добавим в объект
    obj.data.materials.append(mat)


def create_new_collection(collection_name):
    # Функция создает коллецию
    new_collection = bpy.data.collections.new(collection_name)
    bpy.context.scene.collection.children.link(new_collection)


def create_new_mesh(collection_name, mesh_name, vertex_list, face_indexes_list, transform_data=None):
    # создаем меш
    mesh = bpy.data.meshes.new(mesh_name)
    mesh.from_pydata(vertex_list, [], face_indexes_list)
    # создаем объект. к нему привязывается меш.
    obj = bpy.data.objects.new(mesh_name, mesh)
    if transform_data:
        # зададим объекту данные трансформации
        set_object_transform_data(obj, transform_data['location'], transform_data['scale'], transform_data['rotation'])
    # добавим объект в коллекцию
    bpy.data.collections[collection_name].objects.link(obj)
    return obj


def create_uv_maps(mesh_obj, uv_maps: dict):
    # 1. Создадим bmesh и uv_layers
    mesh = mesh_obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    uv_name_list = uv_maps.keys()
    uv_layers = {}
    for uv_name in uv_name_list:
        uv_layers[uv_name] = bm.loops.layers.uv.new(uv_name)
    # 2. Переберем все loop меша. loop - это узел uv развертки. loop хранит информацию о вертексе в контексте uv, а имеено face_id, edge_id, vertex_id.
    # Душный участок, но альтернатив нет
    for face in bm.faces:
        for vert_pos, loop in enumerate(face.loops):
            for uv_name in uv_name_list:
                uv_coords = uv_maps[uv_name]['uv_map'].get(loop.face.index)
                if uv_coords is None:
                    continue
                uv_lay = uv_layers[uv_name]
                loop[uv_lay].uv = uv_coords[vert_pos]
    bm.to_mesh(mesh)
    bm.free()


def create_mesh_collision_box(collection_name, mesh_name, material_name, transform_data):
    # сделаем коллекцию активной
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[collection_name]
    # создадим примитивный куб
    bpy.ops.mesh.primitive_cube_add(align='WORLD')
    # он автоматически становится активным после создания - возьмем его из актива
    obj = bpy.context.view_layer.objects.active
    # переименуем объект
    obj.name = mesh_name
    # переименуем меш
    obj.data.name = mesh_name

    if transform_data:
        # зададим объекту данные трансформации
        set_object_transform_data(obj, transform_data['location'], transform_data['scale'], transform_data['rotation'])

    # возьмем материал
    mat = bpy.data.materials.get(material_name)
    # добавим в объект
    obj.data.materials.append(mat)
    # добавим модификатор
    add_modifier_for_cage(obj)


def create_mesh_visual_box(collection_name, mesh_name, material_name, vertex_list, face_indexes_list):
    obj = create_new_mesh(collection_name, mesh_name, vertex_list, face_indexes_list)
    # добавим материал
    mat = bpy.data.materials.get(material_name)
    # добавим в объект
    obj.data.materials.append(mat)
    # добавим модификатор
    add_modifier_for_cage(obj)


def create_new_transparent_material(name, color):
    """Функция делает "технические" меши прозрачными при отображении в рендере"""
    # создадим материал
    new_mat = bpy.data.materials.new(name)
    try:
        # зададим значение - смешанный
        new_mat.surface_render_method = 'BLENDED'
    except AttributeError:
        # на старой версии 2.81 нет атрибута surface_render_method. 
        # в старом блендере это blend_method
        # зададим значение - смешанный
        new_mat.blend_method = 'BLEND'
    except Exception as ex:
        raise ex

    # добавим цвет материалу для вьюпорта
    new_mat.diffuse_color = color
    # включим возможность использовать ноды
    new_mat.use_nodes = True
    # проверим есть ли нода "Принцпиальный BSDF". 
    # Она вроде бы может создаться автоматом при включении нод, а вроде и нет..
    # Лишним проверить не будет
    node = [i for i in list(new_mat.node_tree.nodes) if i.bl_idname == 'ShaderNodeBsdfPrincipled']
    if len(node) == 0:
        node = new_mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    else:
        node = node[0]
    # зададим ноде цвет
    node.inputs[0].default_value = color
    # зададим альфа-канал
    node.inputs[4].default_value = 0.3


def add_modifier_for_cage(obj):
    # делает из куба клетку с помощью модификатора
    obj.modifiers.new(name='cage', type='WIREFRAME')
    # задать толщину клетки
    obj.modifiers['cage'].thickness = 0.2


def set_object_transform_data(obj, location=None, scale=None, rotation=None):
    if location is not None:
        # создаем матрицу позиции. задается списком
        translation_matrix = Matrix.Translation(location)
        obj.matrix_world @= translation_matrix
    if scale is not None:
        # матрица масштабирования. задается отдельными осями
        for n, axis in enumerate([(1,0,0), (0,1,0), (0,0,1)]):
            scale_matrix = Matrix.Scale(scale[n], 4, axis)
            obj.matrix_world @= scale_matrix
    if rotation is not None:
        # матрица вращения. задается отдельными осями
        for n, axis in enumerate('XYZ'):
            rotation_matrix = Matrix.Rotation(math.radians(rotation[n]), 4, axis)
            obj.matrix_world @= rotation_matrix


def calculate_coll_voxel_vertex_coords(point3D_7099h, x_vox_count, z_vox_count, y_vox_count, x_vox_size, z_vox_size, y_vox_size):
    return _calculate_voxel_vertex_coords(point3D_7099h, x_vox_count, z_vox_count, y_vox_count, x_vox_size, z_vox_size, y_vox_size)

def calculate_hhid_voxel_vertex_coords(point3D_7091h, x_vox_count, z_vox_count, y_vox_count, x_vox_size, z_vox_size, y_vox_size):
    return _calculate_voxel_vertex_coords(point3D_7091h, x_vox_count, z_vox_count, y_vox_count, x_vox_size, z_vox_size, y_vox_size)

def _calculate_voxel_vertex_coords(start_point3D, x_vox_count, z_vox_count, y_vox_count, x_vox_size, z_vox_size, y_vox_size):
    # vertex_list = [[-1,-1,-1], [-1,-1,1], [-1,1,-1], [-1,1,1], [1,-1,-1], [1,-1,1], [1,1,-1], [1,1,1]]
    vertex_list = []
    for i in range(8):
        coor = [start_point3D[0] + (x_vox_count * x_vox_size), start_point3D[1] + (z_vox_count * z_vox_size), start_point3D[2] + (y_vox_count * y_vox_size)]
        if i == 0:    
            vertex_list.insert(i, coor)
        elif i == 1:
            coor[2] += y_vox_size
            vertex_list.insert(i, coor)
        elif i == 2:
            coor[1] += z_vox_size
            vertex_list.insert(i, coor)
        elif i == 3:
            coor[1] += z_vox_size
            coor[2] += y_vox_size
            vertex_list.insert(i, coor)
        elif i == 4:
            coor[0] += x_vox_size
            vertex_list.insert(i, coor)
        elif i == 5:
            coor[0] += x_vox_size
            coor[2] += y_vox_size
            vertex_list.insert(i, coor)
        elif i == 6:
            coor[0] += x_vox_size
            coor[1] += z_vox_size
            vertex_list.insert(i, coor)
        else:
            coor[0] += x_vox_size
            coor[1] += z_vox_size
            coor[2] += y_vox_size
            vertex_list.insert(i, coor)
    return vertex_list

# var_mesh_create_meshes_by_IDs=[439, 480, 437, 476], beach_4 Voyna

if __name__ == "__main__":
    exporter = RCCarsExportToBlender(
        SB_FILE_PATH,
        flag_mesh_create_mesh=False,
        flag_mesh_create_visual_box=False, 
        flag_mesh_create_collision_box=False, 
        flag_mesh_create_3DPoints=False,
        var_mesh_create_meshes_by_IDs=None,
        flag_coll_build_matrix=False,
        flag_coll_build_only_voxel_with_collision=True,
        flag_coll_create_3DPoints=False,
        var_coll_row_start=None,
        var_coll_row_end=None,
        flag_hhid_build_matrix=False,
        flag_hhid_build_only_voxel_with_collision=True,
        flag_hhid_create_3DPoints=False,
        var_hhid_row_start=None,
        var_hhid_row_end=None,
        flag_evol_on=False,
        flag_evol_build_volume_prism=False
        )
    exporter.run_export()
