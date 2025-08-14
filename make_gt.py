import bpy
import random
import os
import math
import mathutils
import json
import numpy as np
import cv2
from bpy_extras.object_utils import world_to_camera_view

def encode_rle(mask):
    """이진 마스크를 RLE로 인코딩"""
    pixels = mask.flatten()
    pixels = np.concatenate([[0], pixels, [0]])
    runs = np.where(pixels[1:] != pixels[:-1])[0] + 1
    runs[1::2] -= runs[::2]
    return runs.tolist()

# 환경 설정
output_dir = "/home/donghoon/Blender-python/output"
os.makedirs(output_dir, exist_ok=True)
frame_to_render = 200

# 렌더 엔진 및 해상도 설정
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
width = scene.render.resolution_x
height = scene.render.resolution_y

# 메시 오브젝트 가져오기
mesh_objects = [obj for obj in scene.objects if obj.type == 'MESH']

# Object Index Pass 활성화 및 고유 ID 부여
view_layer = scene.view_layers["ViewLayer"]
view_layer.use_pass_object_index = True
for i, obj in enumerate(mesh_objects):
    obj.pass_index = i + 1

# 카메라 설정
camera_obj = bpy.data.objects.get("Camera") or bpy.context.object
board_center = mathutils.Vector((0, 0, 0.1))

# 랜덤 카메라 위치 설정
angle = random.uniform(0, 2 * math.pi)
radius = random.uniform(15.0, 20.0)
height_pos = random.uniform(5.0, 10.0)
camera_obj.location = mathutils.Vector((radius * math.cos(angle), radius * math.sin(angle), height_pos))

# 카메라 방향 설정
direction = board_center - camera_obj.location
rot_quat = direction.to_track_quat('-Z', 'Y')
camera_obj.rotation_euler = rot_quat.to_euler()
scene.camera = camera_obj

# 컴포지터 노드 설정
scene.use_nodes = True
tree = scene.node_tree
tree.nodes.clear()

# 렌더 레이어 및 RGB 출력 노드
rlayers = tree.nodes.new(type='CompositorNodeRLayers')
rlayers.layer = "ViewLayer"

rgb_output = tree.nodes.new(type='CompositorNodeOutputFile')
rgb_output.base_path = output_dir
rgb_output.file_slots[0].path = f"rgb{frame_to_render:04d}"
rgb_output.format.file_format = 'JPEG'
rgb_output.format.quality = 90
tree.links.new(rlayers.outputs['Image'], rgb_output.inputs[0])

# Material Index 설정 (Object Index가 없는 경우 대비)
view_layer.use_pass_material_index = True
for i, obj in enumerate(mesh_objects):
    mat_name = f"SegMat_{i}"
    mat = bpy.data.materials.new(name=mat_name)
    mat.pass_index = i + 1
    obj.data.materials.clear()
    obj.data.materials.append(mat)

# 렌더링 직전에 프레임 설정 및 강제 업데이트
bpy.context.scene.frame_set(frame_to_render)
bpy.context.scene.frame_current = frame_to_render
bpy.context.view_layer.update()
bpy.context.evaluated_depsgraph_get().update()

# 렌더링 실행
bpy.ops.render.render(write_still=True)

# 어노테이션 데이터 생성
annotations_list = []

for i, obj in enumerate(mesh_objects):
    # 월드 좌표를 카메라 뷰 좌표로 변환
    world_coords = [obj.matrix_world @ v.co for v in obj.data.vertices]
    camera_coords = [world_to_camera_view(scene, camera_obj, coord) for coord in world_coords]
    
    # 유효한 좌표 필터링
    valid_coords = [c for c in camera_coords if 0 <= c.x <= 1 and 0 <= c.y <= 1 and c.z > 0]
    
    if valid_coords:
        # 바운딩 박스 계산
        xs = [c.x for c in valid_coords]
        ys = [c.y for c in valid_coords]
        
        x_min_norm = min(xs)
        y_min_norm = 1.0 - max(ys)  # Y축 뒤집기
        x_max_norm = max(xs)
        y_max_norm = 1.0 - min(ys)
        
        # 픽셀 좌표로 변환
        x_min_px = int(x_min_norm * width)
        y_min_px = int(y_min_norm * height)
        x_max_px = int(x_max_norm * width)
        y_max_px = int(y_max_norm * height)
        
        # COCO 바운딩 박스
        bbox_width = x_max_px - x_min_px
        bbox_height = y_max_px - y_min_px
        coco_bbox = [x_min_px, y_min_px, bbox_width, bbox_height]
        
        # 세그멘테이션 마스크 생성
        obj_mask = np.zeros((height, width), dtype=np.uint8)
        obj_mask[y_min_px:y_max_px, x_min_px:x_max_px] = 1
        rle_encoded = encode_rle(obj_mask)
        
        # 어노테이션 데이터
        annotation = {
            "id": i + 1,
            "image_id": 1,
            "category_id": i + 1,
            "bbox": coco_bbox,
            "area": float(bbox_width * bbox_height),
            "segmentation": {
                "counts": rle_encoded,
                "size": [height, width]
            },
            "iscrowd": 0
        }
        annotations_list.append(annotation)

# 바운딩 박스 정보 저장
with open(os.path.join(output_dir, "bboxes.txt"), "w") as f:
    for annotation in annotations_list:
        bbox = annotation['bbox']
        obj_name = f"Object_{annotation['category_id']}"
        x_min_norm = bbox[0] / width
        y_min_norm = bbox[1] / height
        x_max_norm = (bbox[0] + bbox[2]) / width
        y_max_norm = (bbox[1] + bbox[3]) / height
        width_norm = bbox[2] / width
        height_norm = bbox[3] / height
        
        f.write(f"{obj_name}: x_min={x_min_norm:.4f}, y_min={y_min_norm:.4f}, "
                f"x_max={x_max_norm:.4f}, y_max={y_max_norm:.4f}, "
                f"width={width_norm:.4f}, height={height_norm:.4f}\n")

# YOLO 포맷 저장
with open(os.path.join(output_dir, "yolo_format.txt"), "w") as f:
    for annotation in annotations_list:
        bbox = annotation['bbox']
        center_x = (bbox[0] + bbox[2] / 2) / width
        center_y = (bbox[1] + bbox[3] / 2) / height
        width_norm = bbox[2] / width
        height_norm = bbox[3] / height
        class_id = annotation['category_id'] - 1
        f.write(f"{class_id} {center_x:.6f} {center_y:.6f} {width_norm:.6f} {height_norm:.6f}\n")

# COCO 형식 JSON 생성
image_info = {
    "id": 1,
    "width": width,
    "height": height,
    "file_name": f"rgb{frame_to_render:04d}.jpg"
}

categories = [{"id": i + 1, "name": obj.name, "supercategory": "object"} 
              for i, obj in enumerate(mesh_objects)]

coco_data = {
    "images": [image_info],
    "annotations": annotations_list,
    "categories": categories,
    "info": {
        "description": "Blender Generated Dataset with RLE Segmentation",
        "version": "1.0",
        "year": 2024,
        "contributor": "Blender Python Script"
    }
}

# 파일 저장
with open(os.path.join(output_dir, "annotations.json"), "w") as f:
    json.dump(coco_data, f, indent=2)

# 카메라 정보 저장
camera_info = {
    'location': list(camera_obj.location),
    'rotation': list(camera_obj.rotation_euler),
    'lens': camera_obj.data.lens,
    'render_size': [width, height]
}

with open(os.path.join(output_dir, "camera_info.txt"), "w") as f:
    for key, value in camera_info.items():
        f.write(f"{key}: {value}\n")

# 정리
tree.nodes.clear()
scene.use_nodes = False