import bpy
import random
from mathutils import Euler
import math
import mathutils
# ------------------------------
# 설정
# ------------------------------
glb_paths = [
    "/home/donghoon/images/textured_mesh.glb",
    "/home/donghoon/images/textured_mesh.glb",
    "/home/donghoon/images/textured_mesh.glb",
    "/home/donghoon/images/textured_mesh.glb",
    "/home/donghoon/images/textured_mesh.glb",
    "/home/donghoon/images/textured_mesh.glb",
    "/home/donghoon/images/textured_mesh.glb",
    "/home/donghoon/images/textured_mesh.glb",
    "/home/donghoon/images/textured_mesh.glb",
    "/home/donghoon/images/textured_mesh.glb",
]
move_range = (-5, 5)
frame_start = 1
frame_end = 300

# ------------------------------
# 기존 오브젝트 삭제
# ------------------------------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# ------------------------------
# 보드 생성
# ------------------------------
bpy.ops.mesh.primitive_cube_add(size=12, location=(0, 0, -0.6))
board = bpy.context.active_object
board.name = "Board"
board.scale.z = 0.1

board_material = bpy.data.materials.new(name="BoardMaterial")
board_material.diffuse_color = (0.8, 0.8, 0.8, 1.0)
board.data.materials.append(board_material)

bpy.context.view_layer.objects.active = board
bpy.ops.rigidbody.object_add()
board.rigid_body.type = 'PASSIVE'
board.rigid_body.collision_shape = 'BOX'

# ------------------------------
# GLB 임포트 
# ------------------------------
for glb_file in glb_paths:
    bpy.ops.import_scene.gltf(filepath=glb_file)

# ------------------------------
# 메시 오브젝트 필터링 (보드 제외)
# ------------------------------
imported_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH' and obj != board]

# ------------------------------
# 랜덤 위치/회전 + Rigidbody 적용
# ------------------------------
for obj in imported_objects:
    # 부모 해제
    obj.parent = None
    obj.matrix_parent_inverse.identity()
    
    # origin을 메시 중심으로 이동
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    
    # 랜덤 위치
    obj.location = (
        random.uniform(*move_range),
        random.uniform(*move_range),
        10
    )
    
    # 랜덤 회전 (월드 기준)
    rx = random.uniform(0, 2*math.pi)
    ry = random.uniform(0, 2*math.pi)
    rz = random.uniform(0, 2*math.pi)

    rot_matrix = Euler((rx, ry, rz), 'XYZ').to_matrix().to_4x4()
    loc_matrix = mathutils.Matrix.Translation(obj.location)
    obj.matrix_world = loc_matrix @ rot_matrix   
    
    # Rigidbody
    bpy.ops.rigidbody.object_add()
    obj.rigid_body.type = 'ACTIVE'
    obj.rigid_body.collision_shape = 'CONVEX_HULL'
    obj.rigid_body.restitution = 0.0
    obj.rigid_body.friction = 1.0
    obj.rigid_body.linear_damping = 0.9
    obj.rigid_body.angular_damping = 0.9

# ------------------------------
# 물리 시뮬레이션 환경 설정
# ------------------------------
scene = bpy.context.scene
scene.rigidbody_world.enabled = True
scene.frame_start = frame_start
scene.frame_end = frame_end
scene.frame_current = frame_start
scene.rigidbody_world.effector_weights.gravity = 1.0

# ------------------------------
# 카메라 추가
# ------------------------------
bpy.ops.object.camera_add(location=(15, -15, 10))
camera = bpy.context.active_object
camera.rotation_euler = (1.1, 0, 0.785)

# ------------------------------
# 조명 추가
# ------------------------------
bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
sun_light = bpy.context.active_object
sun_light.data.energy = 3

# ------------------------------
# 뷰 레이어 업데이트
# ------------------------------
scene.frame_set(frame_start)
bpy.context.view_layer.update()
