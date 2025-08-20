import blenderproc as bproc
import bpy
import random
from mathutils import Euler, Matrix
import math
import mathutils
import numpy as np
import os
import json
# from blenderproc.scripts import visHdf5Files
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

def encode_rle(mask):
    """이진 마스크를 RLE로 인코딩"""
    pixels = mask.flatten()
    pixels = np.concatenate([[0], pixels, [0]])
    runs = np.where(pixels[1:] != pixels[:-1])[0] + 1
    runs[1::2] -= runs[::2]
    return runs.tolist()

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
json_path = "/home/donghoon/Blender-python/glb_files/can/size.json"
move_range = (-5, 5)
frame_start = 1
frame_end = 300
output_dir = "/home/donghoon/Blender-python/output"
render_frames = [50, 100, 200]  # 특정 프레임만 렌더링

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

# 벽 4개 생성 (물리 충돌용, 렌더링 제외)
wall_positions = [(8, 0, 2), (-8, 0, 2), (0, 8, 2), (0, -8, 2)]
wall_scales = [(0.5, 8, 50), (0.5, 8, 50), (8, 0.5, 50), (8, 0.5, 50)]
walls = []

for i, (pos, scale) in enumerate(zip(wall_positions, wall_scales)):
    bpy.ops.mesh.primitive_cube_add(location=pos, scale=scale)
    wall = bpy.context.active_object
    wall.name = f"Wall_{i+1}"
    wall.hide_render = True  # 렌더링에서 제외
    wall.hide_viewport = False
    walls.append(wall)
    
    bpy.context.view_layer.objects.active = wall
    bpy.ops.rigidbody.object_add()
    wall.rigid_body.type = 'PASSIVE'
    wall.rigid_body.collision_shape = 'BOX'

# GLB 임포트 
for glb_file in glb_paths:
    bpy.ops.import_scene.gltf(filepath=glb_file)

# 메시 오브젝트 필터링 (보드, 벽 제외)
imported_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH' and obj != board and obj not in walls]

# 랜덤 위치/회전 + Rigidbody 적용
for i, obj in enumerate(imported_objects):
    # 부모 해제 및 초기화
    obj.parent = None
    obj.matrix_parent_inverse.identity()
    
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    obj = bpy.context.active_object
    # JSON에서 크기 범위 불러오기
    with open(json_path, 'r') as f:
        size_data = json.load(f)
    min_size = size_data.get("min_size", 6.0)
    max_size = size_data.get("max_size", 12.0)
    
    # 현재 최대 축 길이 계산
    dims = obj.dimensions
    max_dim = max(dims)
    
    # 목표 길이 지정 (랜덤)
    target_length = random.uniform(min_size, max_size)
    
    # 스케일 비율 계산
    scale_factor = target_length / max_dim
    
    # 위치 랜덤 지정
    obj.location = (
        random.uniform(*move_range),
        random.uniform(*move_range),
        random.uniform(5, 10)  # z축은 0.1 이상으로 설정
    )
    
    # 회전 랜덤 지정
    rx = random.uniform(0, 2*math.pi)
    ry = random.uniform(0, 2*math.pi)
    rz = random.uniform(0, 2*math.pi)
    
    rot_matrix = Euler((rx, ry, rz), 'XYZ').to_matrix().to_4x4()
    loc_matrix = Matrix.Translation(obj.location)
    scale_matrix = Matrix.Scale(scale_factor, 4)

    # 최종 월드 매트릭스 적용
    obj.matrix_world = loc_matrix @ rot_matrix @ scale_matrix
    # 스케일 적용
    # obj.scale = [s * scale_factor for s in obj.scale]
    # bproc 메타데이터 설정
    obj_bproc = bproc.python.types.MeshObjectUtility.MeshObject(obj)
    obj_bproc.set_cp("category_id", i + 2)
    
    # 리지드바디 적용
    bpy.ops.rigidbody.object_add()
    obj.rigid_body.type = 'ACTIVE'
    obj.rigid_body.collision_shape = 'CONVEX_HULL'
    obj.rigid_body.restitution = 0.0
    obj.rigid_body.friction = 1.0
    obj.rigid_body.linear_damping = 0.9
    obj.rigid_body.angular_damping = 0.9
    
    # 업데이트
    bpy.context.view_layer.update()

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

z_range = 10

def random_value(min_val, max_val):
    if np.random.rand() < 0.5:
        return random.uniform(min_val, max_val)
    else:
        return random.uniform(-max_val, -min_val)

for i in range(14):
    radius = random.uniform(15.0, 20.0)
    x_value = np.random.uniform(-radius, radius)
    y_value, z_value = math.sqrt(radius ** 2 - x_value ** 2), z_range
    bpy.ops.object.camera_add(location=(x_value, y_value, z_value))
    camera = bpy.context.active_object
    direction = target - camera.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera.rotation_euler = rot_quat.to_euler()
    camera.name = f"Camera_{i+1}"
    cameras.append(camera)

bpy.context.scene.camera = camera

# HDRI 배경 랜덤 적용
hdri_dir = "/home/donghoon/Blender-python/background"
hdri_files = [f for f in os.listdir(hdri_dir) if f.lower().endswith(('.hdr', '.exr'))]
if hdri_files:
    hdri_path = os.path.join(hdri_dir, random.choice(hdri_files))
    world = bpy.context.scene.world
    world.use_nodes = True
    env_node = world.node_tree.nodes.new('ShaderNodeTexEnvironment')
    env_node.image = bpy.data.images.load(hdri_path)
    world.node_tree.links.new(env_node.outputs['Color'], world.node_tree.nodes['World Output'].inputs['Surface'])

# # 조명 추가
# bpy.ops.object.light_add(type='SUN', location=(np.random.uniform(-20,20), np.random.uniform(-20,20), 20))
# sun_light = bpy.context.active_object
# sun_light.data.energy = np.random.uniform(1, 7)


# BlenderProc 렌더링 설정
bproc.camera.set_resolution(512, 512)
bproc.renderer.enable_normals_output()
bproc.renderer.enable_depth_output(activate_antialiasing=False, convert_to_distance=True)
bproc.renderer.enable_segmentation_output(map_by=["category_id"])

# 물리 시뮬레이션 전체 실행
scene.frame_set(frame_start)
# scene.frame_start = 200
# scene.frame_end = frame_end
# scene.rigidbody_world.point_cache.frame_start = 200
# scene.rigidbody_world.point_cache.frame_end = 250
bpy.ops.ptcache.bake_all(bake=True)

# BlenderProc 카메라 포즈 초기화 (기존 포즈 제거)
bproc.camera.set_resolution(512, 512)

# COCO annotation 통합을 위한 변수들
all_images = []
all_annotations = []
all_categories = []
annotation_id = 1
image_id = 1

# images 폴더 생성
images_dir = os.path.join(output_dir, "images")
os.makedirs(images_dir, exist_ok=True)
os.makedirs(os.path.join(output_dir, "hdf5"), exist_ok=True)

# 시뮬레이션 완료 후 특정 프레임만 렌더링
for frame in render_frames:
    for i, cam in enumerate(cameras):
        # BlenderProc 카메라 포즈 설정 (각 카메라마다)
        cam_matrix = cam.matrix_world
        bproc.camera.add_camera_pose(cam_matrix)
        
        # 현재 프레임으로 설정
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        
        # z값이 0보다 아래인 객체들을 숨기기
        hidden_objects = []
        for obj in imported_objects:
            if obj.location.z < 0:
                obj.hide_render = True
                obj.hide_viewport = True
                obj.hide_render = True
                hidden_objects.append(obj)
            else:
                obj.hide_render = False
                obj.hide_viewport = False
                obj.hide_render = False
        # 한 번에 모든 데이터 렌더링
        bpy.context.scene.frame_start = frame
        bpy.context.scene.frame_end = frame + 1
        data = bproc.renderer.render()
        
        # HDF5 저장 (별도 폴더)
        hdf5_dir = os.path.join(output_dir, "hdf5")
        os.makedirs(hdf5_dir, exist_ok=True)
        bproc.writer.write_hdf5(os.path.join(hdf5_dir, f'{frame:04d}_{cam.name}.hdf5'), data)
        
        bproc.writer.write_coco_annotations(os.path.join(output_dir, 'coco_data'),
                                    instance_segmaps=data["category_id_segmaps"],
                                    instance_attribute_maps=data["instance_attribute_maps"],
                                    colors=data["colors"],
                                    color_file_format="JPEG")
        # 숨겨진 객체들 다시 보이게 하기
        for obj in hidden_objects:
            obj.hide_render = False
        
        # 다음 카메라를 위해 현재 포즈 제거
        bproc.camera.set_resolution(512, 512)  # 포즈 리셋