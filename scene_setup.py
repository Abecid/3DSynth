import bpy
import blenderproc as bproc
import random
import json
import math
from mathutils import Euler, Matrix
from config import *
import numpy as np
import pdb
def setup_gpu():
    """GPU 렌더링 설정"""
    bpy.context.scene.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'CUDA'
    prefs.get_devices()
    devices = prefs.devices
    if devices:
        for device in devices:
            if device.type in {'CUDA', 'OPTIX', 'OPENCL'}:
                device.use = True
        bpy.context.scene.cycles.device = 'GPU'

def clear_scene():
    """기존 오브젝트 삭제"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

def create_board():
    """보드 생성 및 설정"""
    bpy.ops.import_scene.gltf(filepath=BOARD_PATH)
    board = bpy.context.active_object
    board.location = (0, 0, -0.6)
    board.name = "Board"
    board.scale.z = 1.0
    
    board_bproc = bproc.python.types.MeshObjectUtility.MeshObject(board)
    board_bproc.set_cp("category_id", 0)
    
    bpy.context.view_layer.objects.active = board
    bpy.ops.rigidbody.object_add()
    board.rigid_body.type = 'PASSIVE'
    board.rigid_body.collision_shape = 'BOX'
    
    return board

def create_walls():
    """벽 4개 생성"""
    walls = []
    for i, (pos, scale) in enumerate(zip(WALL_POSITIONS, WALL_SCALES)):
        bpy.ops.mesh.primitive_cube_add(location=pos, scale=scale)
        wall = bpy.context.active_object
        wall.name = f"Wall_{i+1}"
        wall.hide_render = True
        wall.hide_viewport = False
        walls.append(wall)
        
        bpy.context.view_layer.objects.active = wall
        bpy.ops.rigidbody.object_add()
        wall.rigid_body.type = 'PASSIVE'
        wall.rigid_body.collision_shape = 'BOX'
    
    return walls

def import_and_setup_objects(board, walls):
    """GLB 객체들 임포트 및 설정"""
    for glb_file in GLB_PATHS:
        bpy.ops.import_scene.gltf(filepath=glb_file)
        imported = bpy.context.selected_objects
        
        # mesh만 필터링
        meshes = [obj for obj in imported if obj.type == 'MESH']
        if not meshes:
            continue
        
        # 하나의 mesh로 병합
        bpy.context.view_layer.objects.active = meshes[0]
        for m in meshes:
            m.select_set(True)
        bpy.ops.object.join()
        
        # 이제 active object가 합쳐진 하나의 mesh
        obj = bpy.context.active_object
        for obj in bpy.context.selected_objects:
            obj.name = os.path.dirname(glb_file).split('/')[-1]
            json_file = os.path.join(os.path.dirname(glb_file), 'size.json')
            with open(json_file, 'r') as f:
                size_data = json.load(f)
                obj['min_size'] = size_data.get("min_size", 6.0)
                obj['max_size'] = size_data.get("max_size", 12.0)
    imported_objects = [obj for obj in bpy.context.scene.objects 
                       if obj.type == 'MESH' and obj != board and obj not in walls]
    
    for i, obj in enumerate(imported_objects):
        obj.parent = None
        obj.matrix_parent_inverse.identity()
        
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
        obj = bpy.context.active_object
        
        target_length = random.uniform(obj['min_size'], obj['max_size'])

        # # x,y,z 축 중 가장 큰 길이를 기준으로 스케일링
        # dims = obj.dimensions
        # max_dim = max(dims)
        # scale_factor = target_length / max_dim

        # PCA 기반 스케일링
        vertices = np.array([obj.matrix_world @ v.co for v in obj.data.vertices])
        vertices_centered = vertices - np.mean(vertices, axis=0)
        cov = np.cov(vertices_centered.T)
        eigenvalues, eigenvectors = np.linalg.eig(cov)
        principal_axis = eigenvectors[:, np.argmax(eigenvalues)]
        projections = np.dot(vertices_centered, principal_axis)
        length = projections.max() - projections.min()
        scale_factor = target_length / length

        obj.location = (
            random.uniform(*MOVE_RANGE),
            random.uniform(*MOVE_RANGE),
            random.uniform(5, 10)
        )
        
        rx = random.uniform(0, 2*math.pi)
        ry = random.uniform(0, 2*math.pi)
        rz = random.uniform(0, 2*math.pi)
        
        rot_matrix = Euler((rx, ry, rz), 'XYZ').to_matrix().to_4x4()
        loc_matrix = Matrix.Translation(obj.location)
        scale_matrix = Matrix.Scale(scale_factor, 4)
        
        obj.matrix_world = loc_matrix @ rot_matrix @ scale_matrix
        
        obj_bproc = bproc.python.types.MeshObjectUtility.MeshObject(obj)
        try: category_id = MAPPING_ID[obj.name.split('.')[0]]
        except : category_id = MAPPING_ID[obj.name]
        obj_bproc.set_cp("category_id", category_id)
        obj_bproc.set_cp("instance_id", i)
        
        bpy.ops.rigidbody.object_add()
        obj.rigid_body.type = 'ACTIVE'
        obj.rigid_body.collision_shape = 'CONVEX_HULL'
        obj.rigid_body.collision_margin = 0.001
        obj.rigid_body.restitution = 0.0
        obj.rigid_body.friction = 1.0
        obj.rigid_body.linear_damping = 0.9
        obj.rigid_body.angular_damping = 0.9
        
        bpy.context.view_layer.update()
    
    return imported_objects

def setup_hdri():
    """HDRI 배경 랜덤 적용"""
    import os
    hdri_files = [f for f in os.listdir(HDRI_DIR) if f.lower().endswith(('.hdr', '.exr'))]
    if hdri_files:
        hdri_path = os.path.join(HDRI_DIR, random.choice(hdri_files))
        world = bpy.context.scene.world
        world.use_nodes = True
        env_node = world.node_tree.nodes.new('ShaderNodeTexEnvironment')
        env_node.image = bpy.data.images.load(hdri_path)
        world.node_tree.links.new(env_node.outputs['Color'], world.node_tree.nodes['World Output'].inputs['Surface']) 