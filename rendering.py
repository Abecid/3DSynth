import bpy
import blenderproc as bproc
import mathutils
import random
import math
import os
import numpy as np
from config import *
from utils import random_value

def create_cameras():
    """카메라들 생성"""
    cameras = []
    target = mathutils.Vector((0, 0, 0))
    
    for i in range(NUM_CAMERAS):
        radius = random.uniform(*CAMERA_RADIUS_RANGE)
        x_value = np.random.uniform(-radius, radius)
        y_value, z_value = math.sqrt(radius ** 2 - x_value ** 2), CAMERA_Z
        bpy.ops.object.camera_add(location=(x_value, y_value, z_value))
        camera = bpy.context.active_object
        direction = target - camera.location
        rot_quat = direction.to_track_quat('-Z', 'Y')
        camera.rotation_euler = rot_quat.to_euler()
        camera.name = f"Camera_{i+1}"
        cameras.append(camera)
    
    bpy.context.scene.camera = camera
    return cameras

def setup_blenderproc_rendering():
    """BlenderProc 렌더링 설정"""
    bproc.camera.set_resolution(RENDER_RESOLUTION, RENDER_RESOLUTION)
    bproc.renderer.enable_normals_output()
    bproc.renderer.enable_depth_output(activate_antialiasing=False, convert_to_distance=True)
    bproc.renderer.enable_segmentation_output(map_by=["category_id"])

def render_all_cameras(cameras, imported_objects):
    """모든 카메라로 렌더링"""
    all_images = []
    all_annotations = []
    all_categories = []
    annotation_id = 1
    image_id = 1
    
    # 출력 디렉토리 생성
    images_dir = os.path.join(OUTPUT_DIR, "images")
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "hdf5"), exist_ok=True)
    
    for frame in RENDER_FRAMES:
        for i, cam in enumerate(cameras):
            # BlenderProc 카메라 포즈 설정
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
            
            # 렌더링
            bpy.context.scene.frame_start = frame
            bpy.context.scene.frame_end = frame + 1
            data = bproc.renderer.render()
            
            # HDF5 저장
            hdf5_dir = os.path.join(OUTPUT_DIR, "hdf5")
            bproc.writer.write_hdf5(os.path.join(hdf5_dir, f'{frame:04d}_{cam.name}.hdf5'), data)
            
            # COCO 어노테이션 저장
            bproc.writer.write_coco_annotations(os.path.join(OUTPUT_DIR, 'coco_data'),
                                        instance_segmaps=data["category_id_segmaps"],
                                        instance_attribute_maps=data["instance_attribute_maps"],
                                        colors=data["colors"],
                                        color_file_format="JPEG")
            
            # 숨겨진 객체들 다시 보이게 하기
            for obj in hidden_objects:
                obj.hide_render = False
            
            # 다음 카메라를 위해 현재 포즈 제거
            bproc.camera.set_resolution(RENDER_RESOLUTION, RENDER_RESOLUTION) 