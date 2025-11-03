import bpy
import blenderproc as bproc
import random
import json
import math
from mathutils import Euler, Matrix
from config import *
import numpy as np
import mathutils

from utils import get_orientations

def setup_gpu():
    """GPU 렌더링 설정"""
    bpy.context.scene.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX' # 'CUDA', 'OPTIX', 'OPENCL', 'HIP' 중 하나 선택
    prefs.get_devices()
    devices = prefs.devices
    if devices:
        for device in devices:
            if device.type in {'CUDA', 'OPTIX', 'OPENCL', 'HIP'}:
                device.use = True
            elif device.type == 'CPU':
                device.use = False
        bpy.context.scene.cycles.device = 'GPU'
    # GPU에 맞는 타일 크기 세팅
    tile_size = 2048
    bpy.context.scene.cycles.tile_x = tile_size
    bpy.context.scene.cycles.tile_y = tile_size

    # (옵션) 샘플 수 및 Denoiser 켜기
    bpy.context.scene.cycles.samples = 128
    bpy.context.scene.cycles.use_denoising = True

def clear_scene():
    """기존 오브젝트 삭제"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

def create_board():
    """보드 생성 및 설정 (정확히 50x36x2.5 cm)"""
    import mathutils, numpy as np, blenderproc as bproc, bpy

    TARGET_DIMS = np.array([0.36, 0.50, 0.04])  # meters

    # Import the board
    bpy.ops.import_scene.gltf(filepath=BOARD_PATH)
    board = bpy.context.active_object
    board.name = "Board"

    # Center origin at geometry center
    bpy.context.view_layer.objects.active = board
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

    # Measure current size
    bpy.context.view_layer.update()
    current_dims = np.array(board.dimensions)

    # Scale to target
    scale_factors = TARGET_DIMS / current_dims
    board.scale = tuple(scale_factors)

    bpy.context.view_layer.update()

    # Move center to origin
    board.location = (0, 0, 0)

    # Lift top surface to z = 0
    bbox = [board.matrix_world @ mathutils.Vector(corner) for corner in board.bound_box]
    z_min = min(v.z for v in bbox)
    z_max = max(v.z for v in bbox)
    height = z_max - z_min
    board.location.z += height / 2.0

    # Physics setup
    board_bproc = bproc.python.types.MeshObjectUtility.MeshObject(board)
    board_bproc.set_cp("category_id", 0)
    bpy.context.view_layer.objects.active = board
    bpy.ops.rigidbody.object_add()
    board.rigid_body.type = 'PASSIVE'
    board.rigid_body.collision_shape = 'BOX'
    board.rigid_body.collision_margin = 0.0

    print(f"Board scaled to: {board.dimensions}")
    return board

# def create_board():
#     """보드 생성 및 설정"""
#     # Import the board GLB
#     bpy.ops.import_scene.gltf(filepath=BOARD_PATH)
#     board = bpy.context.active_object
#     board.name = "Board"
#     board.scale.z = 1.0

#     # --- Center the board's origin at its geometric center ---
#     bpy.context.view_layer.objects.active = board
#     bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

#     # Move the board so its geometric center is at world origin
#     board.location = (0, 0, 0)

#     # --- Optional: align the *top surface* of the board to z = 0 ---
#     bbox = [board.matrix_world @ mathutils.Vector(corner) for corner in board.bound_box]
#     z_min = min(v.z for v in bbox)
#     z_max = max(v.z for v in bbox)
#     height = z_max - z_min
#     board.location.z += height / 2.0

#     # --- BlenderProc physics setup ---
#     board_bproc = bproc.python.types.MeshObjectUtility.MeshObject(board)
#     board_bproc.set_cp("category_id", 0)
    
#     bpy.context.view_layer.objects.active = board
#     bpy.ops.rigidbody.object_add()
#     board.rigid_body.type = 'PASSIVE'
#     board.rigid_body.collision_shape = 'BOX'
    
#     return board

def create_walls(board):
    """보드 주위를 둘러싸는 4개의 벽 생성"""
    bpy.context.view_layer.update()

    # get actual board extents (in meters)
    bbox = [board.matrix_world @ mathutils.Vector(corner) for corner in board.bound_box]
    x_min = min(v.x for v in bbox); x_max = max(v.x for v in bbox)
    y_min = min(v.y for v in bbox); y_max = max(v.y for v in bbox)

    # half width/length
    hx = (x_max - x_min) / 2.0
    hy = (y_max - y_min) / 2.0

    # wall parameters
    margin = 0.02   # 2 cm gap from board edge
    thick  = 0.01   # 1 cm thick wall
    height = 0.15   # 15 cm tall

    wall_specs = [
        # (+X) right wall
        (( hx + margin + thick/2, 0.0, height/2), (thick/2, hy + margin, height/2)),
        # (-X) left wall
        ((-hx - margin - thick/2, 0.0, height/2), (thick/2, hy + margin, height/2)),
        # (+Y) top wall
        ((0.0,  hy + margin + thick/2, height/2), (hx + margin, thick/2, height/2)),
        # (-Y) bottom wall
        ((0.0, -hy - margin - thick/2, height/2), (hx + margin, thick/2, height/2)),
    ]

    walls = []
    for i, (pos, scale) in enumerate(wall_specs, 1):
        bpy.ops.mesh.primitive_cube_add(location=pos, scale=scale)
        wall = bpy.context.active_object
        wall.name = f"Wall_{i}"
        wall.hide_render = True
        wall.hide_viewport = False

        # rigid body
        bpy.context.view_layer.objects.active = wall
        bpy.ops.rigidbody.object_add()
        wall.rigid_body.type = 'PASSIVE'
        wall.rigid_body.collision_shape = 'BOX'
        wall.rigid_body.collision_margin = 0.0
        wall.rigid_body.restitution = 0.0
        wall.rigid_body.friction = 1.0

        walls.append(wall)

    print("Walls created around board:", [w.name for w in walls])
    return walls

# def create_walls():
#     """벽 4개 생성"""
#     walls = []
#     for i, (pos, scale) in enumerate(zip(WALL_POSITIONS, WALL_SCALES)):
#         pos = (pos[0], pos[1], scale[2] / 2.0)
#         bpy.ops.mesh.primitive_cube_add(location=pos, scale=scale)
#         wall = bpy.context.active_object
#         wall.name = f"Wall_{i+1}"
#         wall.hide_render = True
#         wall.hide_viewport = False
#         walls.append(wall)
        
#         bpy.context.view_layer.objects.active = wall
#         bpy.ops.rigidbody.object_add()
#         wall.rigid_body.type = 'PASSIVE'
#         wall.rigid_body.collision_shape = 'BOX'
    
#     return walls

def import_and_setup_objects(board, walls, objects_info):
    """GLB 객체들 임포트 및 설정"""
    for glb_file in GLB_PATHS:
        bpy.ops.import_scene.gltf(filepath=glb_file)
        imported = bpy.context.selected_objects

        get_orientations(imported, objects_info, "original")

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
                obj['min'] = 0.1 # size_data.get("min", 1.0)
                obj['max'] = 0.3 # size_data.get("max", 1.0)
    imported_objects = [obj for obj in bpy.context.scene.objects 
                       if obj.type == 'MESH' and obj != board and obj not in walls]
    
    for i, obj in enumerate(imported_objects):
        obj.parent = None
        obj.matrix_parent_inverse.identity()
        
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
        obj = bpy.context.active_object
        
        target_length = random.uniform(obj['min'], obj['max'])

        # # x,y,z 축 중 가장 큰 길이를 기준으로 스케일링
        dims = obj.dimensions
        max_dim = max(dims)
        scale_factor = target_length / max_dim

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
            random.uniform(-0.24, 0.24),
            random.uniform(-0.17, 0.17),
            random.uniform(0.3, 0.6)
        )
        
        rx = random.uniform(0, 2*math.pi)
        ry = random.uniform(0, 2*math.pi)
        rz = random.uniform(0, 2*math.pi)
        
        rot_matrix = Euler((rx, ry, rz), 'XYZ').to_matrix().to_4x4()
        loc_matrix = Matrix.Translation(obj.location)
        scale_matrix = Matrix.Scale(scale_factor, 4)
        
        obj.matrix_world = loc_matrix @ rot_matrix @ scale_matrix
        
        obj_bproc = bproc.python.types.MeshObjectUtility.MeshObject(obj)
        
        category_id = obj.name.split(".")[0]
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