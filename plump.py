import blenderproc as bproc
import bpy
import random
from mathutils import Euler
import math
import mathutils
import numpy as np
import os
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
move_range = (-5, 5)
frame_start = 1
frame_end = 300
output_dir = "/home/donghoon/Blender-python/output"
render_frames = [200]  # 특정 프레임만 렌더링

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

# 조명 추가
bpy.ops.object.light_add(type='SUN', location=(np.random.uniform(-20,20), np.random.uniform(-20,20), 20))
sun_light = bpy.context.active_object
sun_light.data.energy = np.random.uniform(1, 7)


# BlenderProc 렌더링 설정
bproc.camera.set_resolution(512, 512)
bproc.renderer.enable_normals_output()
bproc.renderer.enable_depth_output(activate_antialiasing=False, convert_to_distance=True)
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
                hidden_objects.append(obj)
            else:
                obj.hide_render = False
                obj.hide_viewport = False
        # 한 번에 모든 데이터 렌더링
        bpy.context.scene.frame_start = frame
        bpy.context.scene.frame_end = frame + 1
        data = bproc.renderer.render()
        
        # HDF5 저장 (별도 폴더)
        hdf5_dir = os.path.join(output_dir, "hdf5")
        os.makedirs(hdf5_dir, exist_ok=True)
        bproc.writer.write_hdf5(os.path.join(hdf5_dir, f'{frame:04d}_{cam.name}.hdf5'), data)
        
        # 각 이미지를 PNG로 저장
        for idx, color_image in enumerate(data["colors"]):
            image_filename = f"{frame:04d}_{cam.name}_{idx:02d}.png"
            image_path = os.path.join(images_dir, image_filename)
            
            # PNG로 저장
            import cv2
            color_bgr = cv2.cvtColor(color_image, cv2.COLOR_RGB2BGR)
            cv2.imwrite(image_path, color_bgr)
            
            # COCO 이미지 정보 추가
            all_images.append({
                "id": image_id,
                "width": color_image.shape[1],
                "height": color_image.shape[0], 
                "file_name": 'images/' + image_filename
            })
            
            # 세그멘테이션 데이터가 있으면 annotation 생성
            seg_map = data["category_id_segmaps"][idx]
            unique_ids = np.unique(seg_map)
            
            for obj_id in unique_ids:
                if obj_id > 0:  # 배경 제외
                    mask = (seg_map == obj_id).astype(np.uint8)
                    coords = np.where(mask)
                    if len(coords[0]) > 0:
                        y_min, y_max = np.min(coords[0]), np.max(coords[0])
                        x_min, x_max = np.min(coords[1]), np.max(coords[1])
                        bbox = [int(x_min), int(y_min), int(x_max - x_min), int(y_max - y_min)]
                        
                        # RLE 인코딩
                        rle_encoded = encode_rle(mask)
                        
                        all_annotations.append({
                            "id": annotation_id,
                            "image_id": image_id,
                            "category_id": int(obj_id),
                            "bbox": bbox,
                            "area": int(bbox[2] * bbox[3]),
                            "segmentation": {
                                "counts": rle_encoded,
                                "size": [color_image.shape[0], color_image.shape[1]]
                            },
                            "iscrowd": 0
                        })
                        annotation_id += 1
            
            image_id += 1
        
        # 숨겨진 객체들 다시 보이게 하기
        for obj in hidden_objects:
            obj.hide_render = False
        
        # 다음 카메라를 위해 현재 포즈 제거
        bproc.camera.set_resolution(512, 512)  # 포즈 리셋

# 카테고리 정보 생성 (객체별)
all_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
for i, obj in enumerate(all_objects):
    category_id = 1 if obj == board else i + 1
    all_categories.append({"id": category_id, "name": obj.name, "supercategory": "object"})

# 통합된 COCO annotation JSON 저장
coco_data = {
    "images": all_images,
    "annotations": all_annotations, 
    "categories": all_categories,
    "info": {
        "description": "BlenderProc Generated Dataset",
        "version": "1.0"
    }
}

with open(os.path.join(output_dir, "coco_annotations.json"), "w") as f:
    import json
    json.dump(coco_data, f, indent=2)