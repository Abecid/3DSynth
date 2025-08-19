import blenderproc as bproc
import bpy
import random
from mathutils import Euler
import math
import mathutils
import numpy as np
import os

# BlenderProc 초기화
bproc.init()

# 설정
board_path = "/home/donghoon/Blender-python/glb_files/board.glb"
glb_paths = [
    "/home/donghoon/Blender-python/glb_files/textured_mesh.glb",
    "/home/donghoon/Blender-python/glb_files/textured_mesh.glb",
    "/home/donghoon/Blender-python/glb_files/textured_mesh.glb",
    "/home/donghoon/Blender-python/glb_files/textured_mesh.glb",
    "/home/donghoon/Blender-python/glb_files/textured_mesh.glb",
    "/home/donghoon/Blender-python/glb_files/textured_mesh.glb",
    "/home/donghoon/Blender-python/glb_files/textured_mesh.glb",
    "/home/donghoon/Blender-python/glb_files/textured_mesh.glb",
    "/home/donghoon/Blender-python/glb_files/textured_mesh.glb",
    "/home/donghoon/Blender-python/glb_files/textured_mesh.glb",
]
move_range = (-5, 5)
frame_start = 1
frame_end = 300
output_dir = "/home/donghoon/Blender-python/output"
render_frames = [200,250,300]  # 특정 프레임만 렌더링

os.makedirs(output_dir, exist_ok=True)

# 기존 오브젝트 삭제
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 보드 생성
bpy.ops.import_scene.gltf(filepath=board_path)
board = bpy.context.active_object
board.location = (0, 0, -0.6)
board.name = "Board"
board.scale.z = 1.0

board_bproc = bproc.python.types.MeshObjectUtility.MeshObject(board)
board_bproc.set_cp("category_id", 1)

bpy.context.view_layer.objects.active = board
bpy.ops.rigidbody.object_add()
board.rigid_body.type = 'PASSIVE'
board.rigid_body.collision_shape = 'BOX'

# GLB 임포트 
for glb_file in glb_paths:
    bpy.ops.import_scene.gltf(filepath=glb_file)

# 메시 오브젝트 필터링 (보드 제외)
imported_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH' and obj != board]

# 랜덤 위치/회전 + Rigidbody 적용
for i, obj in enumerate(imported_objects):
    obj.parent = None
    obj.matrix_parent_inverse.identity()
    
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    
    obj.location = (
        random.uniform(*move_range),
        random.uniform(*move_range),
        10
    )
    
    rx = random.uniform(0, 2*math.pi)
    ry = random.uniform(0, 2*math.pi)
    rz = random.uniform(0, 2*math.pi)

    rot_matrix = Euler((rx, ry, rz), 'XYZ').to_matrix().to_4x4()
    loc_matrix = mathutils.Matrix.Translation(obj.location)
    obj.matrix_world = loc_matrix @ rot_matrix   
    
    obj_bproc = bproc.python.types.MeshObjectUtility.MeshObject(obj)
    obj_bproc.set_cp("category_id", i + 2)
    
    bpy.ops.rigidbody.object_add()
    obj.rigid_body.type = 'ACTIVE'
    obj.rigid_body.collision_shape = 'CONVEX_HULL'
    obj.rigid_body.restitution = 0.0
    obj.rigid_body.friction = 1.0
    obj.rigid_body.linear_damping = 0.9
    obj.rigid_body.angular_damping = 0.9

# 물리 시뮬레이션 환경 설정
scene = bpy.context.scene
scene.rigidbody_world.enabled = True
scene.frame_start = frame_start
scene.frame_end = frame_end
scene.frame_current = frame_start
scene.rigidbody_world.effector_weights.gravity = 1.0



# 카메라 추가
cameras = []
target  = mathutils.Vector((0, 0, 0))
x_range = (10, 15)
y_range = (10, 15)
z_range = 10

def random_value(min_val, max_val):
    if np.random.rand() < 0.5:
        return random.uniform(min_val, max_val)
    else:
        return random.uniform(-max_val, -min_val)

for i in range(14):
    x_value, y_value, z_value = random_value(*x_range), random_value(*y_range), z_range
    bpy.ops.object.camera_add(location=(x_value, y_value, z_value))
    camera = bpy.context.active_object
    direction = target - camera.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera.rotation_euler = rot_quat.to_euler()
    camera.name = f"Camera_{i+1}"
    cameras.append(camera)

bpy.context.scene.camera = camera

# 조명 추가
bpy.ops.object.light_add(type='SUN', location=(np.random.uniform(-20,20), np.random.uniform(-20,20), 20))
sun_light = bpy.context.active_object
sun_light.data.energy = np.random.uniform(1, 7)


# BlenderProc 렌더링 설정
bproc.camera.set_resolution(512, 512)
bproc.renderer.enable_normals_output()
bproc.renderer.enable_depth_output(activate_antialiasing=False)
bproc.renderer.enable_segmentation_output() # map_by=["category_id"]

# 물리 시뮬레이션 전체 실행
scene.frame_set(frame_start)
# scene.frame_start = 200
# scene.frame_end = frame_end
# scene.rigidbody_world.point_cache.frame_start = 200
# scene.rigidbody_world.point_cache.frame_end = 250
bpy.ops.ptcache.bake_all(bake=True)

# BlenderProc 카메라 포즈 초기화 (기존 포즈 제거)
bproc.camera.set_resolution(512, 512)

# 시뮬레이션 완료 후 특정 프레임만 렌더링
for frame in render_frames:
    for i, cam in enumerate(cameras):
        # BlenderProc 카메라 포즈 설정 (각 카메라마다)
        cam_matrix = cam.matrix_world
        bproc.camera.add_camera_pose(cam_matrix)
        
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        
        # 한 번에 모든 데이터 렌더링
        bpy.context.scene.frame_start = frame
        bpy.context.scene.frame_end = frame + 1
        data = bproc.renderer.render()
        
        frame_output_dir = os.path.join(output_dir, f"hdf5")
        os.makedirs(frame_output_dir, exist_ok=True)
        
        bproc.writer.write_hdf5(output_dir + f'/hdf5/{frame:04d}_{cam.name}.hdf5', data)
        
        # # COCO 형식의 annotation JSON 저장
        bproc.writer.write_coco_annotations(
            os.path.join(frame_output_dir, "coco_annotations.json"),
            instance_segmaps=data.get("category_id_segmaps", []),
            instance_attribute_maps=data.get("instance_attribute_maps", []),
            colors=data["colors"],
            color_file_format="JPEG"
        )
        
        # 다음 카메라를 위해 현재 포즈 제거
        bproc.camera.set_resolution(512, 512)  # 포즈 리셋