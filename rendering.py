import bpy
import blenderproc as bproc
import mathutils
import random
import math
import os
import numpy as np
from config import *
from utils import random_value
import pdb
import json

def create_cameras():
    """카메라들 생성"""
    cameras = []
    target = mathutils.Vector((0, 0, 0))
    
    # 지정된 카메라 위치들 (스케일링 전)
    camera_positions = [
        ("LW_left", (0.2355, 0.4636, 0.3124)),
        ("LW_right", (0.1766, 0.4892, 0.3148)),
        ("RW_left", (0.1761, -0.2991, 0.3210)),
        ("RW_right", (0.2377, -0.2679, 0.3119)),
        ("TB_left", (0.2168, 0.0624, 0.5770)),
        ("TB_right", (0.2251, 0.1225, 0.5786)),
        ("TC_left", (0.0082, 0.1374, 0.5959)),
        ("TC_right", (0.0269, 0.0550, 0.5958)),
        ("TF_left", (-0.0793, 0.1408, 0.5768)),
        ("TF_right", (-0.0745, 0.0734, 0.5798)),
        ("TL_left", (0.0970, 0.3051, 0.5611)),
        ("TL_right", (0.0335, 0.3056, 0.5579)),
        ("TR_left", (0.0248, -0.1088, 0.5578)),
        ("TR_right", (0.0908, -0.1111, 0.5531))
    ]
    
    # 현재 위치들의 평균 거리 계산
    current_distances = []
    for _, pos in camera_positions:
        distance = math.sqrt(pos[0]**2 + pos[1]**2 + pos[2]**2)
        current_distances.append(distance)
    avg_current_distance = sum(current_distances) / len(current_distances)
    
    # 목표 반경 범위의 중간값 계산
    target_radius = (CAMERA_RADIUS_RANGE[0] + CAMERA_RADIUS_RANGE[1]) / 2
    
    # 스케일링 팩터 계산
    scale_factor = target_radius / avg_current_distance
    
    # 지정된 위치들로 카메라 생성
    for name, pos in camera_positions:
        # 위치 스케일링
        scaled_pos = (pos[0] * scale_factor, pos[1] * scale_factor, pos[2] * scale_factor)
        
        bpy.ops.object.camera_add(location=scaled_pos)
        camera = bpy.context.active_object
        direction = target - camera.location
        rot_quat = direction.to_track_quat('-Z', 'Y')
        camera.rotation_euler = rot_quat.to_euler()
        camera.name = name
        cameras.append(camera)
    
    bpy.context.scene.camera = camera
    return cameras

def setup_blenderproc_rendering():
    """BlenderProc 렌더링 설정"""
    bproc.camera.set_resolution(RENDER_RESOLUTION, RENDER_RESOLUTION)
    bproc.renderer.set_output_format("JPEG", jpg_quality=90)
    # bproc.renderer.set_render_devices(['CUDA','OPTIX','HIP'], desired_gpu_device_type=[0])
    bproc.renderer.set_render_devices()

    # bproc.renderer.enable_normals_output()
    # bproc.renderer.enable_depth_output(activate_antialiasing=False, convert_to_distance=True)
    bproc.renderer.enable_segmentation_output(map_by=["instance","class","name"]) # category_id
    # pdb.set_trace()
def render_all_cameras(cameras, imported_objects, scene_num):
    # """모든 카메라로 렌더링"""
    os.makedirs(os.path.join(OUTPUT_DIR, "hdf5"), exist_ok=True)
    
    # BlenderProc 카메라 포즈 초기화 (기존 포즈 제거)
    bproc.camera.set_resolution(RENDER_RESOLUTION, RENDER_RESOLUTION)
    hidden_objects = []
    for obj in imported_objects:
        if obj.location.z < 0:
            obj.hide_render = True
            obj.hide_viewport = True
            hidden_objects.append(obj)
        else:
            obj.to_mesh()
            obj.hide_render = False
            obj.hide_viewport = False
    # for single batch 
    for frame in RENDER_FRAMES:
        for i, cam in enumerate(cameras):
            bpy.context.scene.frame_set(frame)
            bpy.context.view_layer.update()
            
            # z값이 0보다 아래인 객체들을 숨기기
            
            # BlenderProc 카메라 포즈 설정 (각 카메라마다)
            bpy.context.scene.camera = cam
            cam_matrix = cam.matrix_world
            bproc.camera.add_camera_pose(cam_matrix)
            print(bproc.camera.get_camera_pose())
            # 한 번에 모든 데이터 렌더링
            bpy.context.scene.frame_start = frame
            bpy.context.scene.frame_end = frame + 1
            data = bproc.renderer.render()
            
            # HDF5 저장
            hdf5_dir = os.path.join(OUTPUT_DIR, "hdf5")
            # bproc.writer.write_hdf5(os.path.join(hdf5_dir, f'{frame:04d}_{cam.name}.hdf5'), data)
            print(data.keys())
            # COCO 어노테이션 저장
            bproc.writer.write_coco_annotations(os.path.join(OUTPUT_DIR, 'coco_data'),
                                        instance_segmaps=data["instance_segmaps"],
                                        instance_attribute_maps=data["instance_attribute_maps"],
                                        colors=data["colors"],
                                        color_file_format="JPEG",
                                        file_prefix=f'{scene_num}_{cam.name}_',
                                        indent=4)
            print(f'COCO annotations saved for scene_num {scene_num} and camera {cam.name}')
            numpy_data = data["instance_segmaps"][0]
            os.makedirs(os.path.join(OUTPUT_DIR, 'instance_segmap'), exist_ok=True)
            np.save(os.path.join(OUTPUT_DIR, 'instance_segmap', f'{scene_num}_{cam.name}.npy'), numpy_data)

            # 다음 카메라를 위해 현재 포즈 제거
            bproc.camera.set_resolution(RENDER_RESOLUTION, RENDER_RESOLUTION) 
    # for frame in RENDER_FRAMES:
    #     bpy.context.scene.frame_set(frame)
    #     bpy.context.view_layer.update()
        
    #     # **중요: 이전 키프레임 초기화**
    #     bproc.utility.reset_keyframes()
        
    #     # **모든 카메라 포즈를 한 번에 등록**
    #     # 각 카메라 포즈가 별도 키프레임으로 추가됨
    #     for cam in cameras:
    #         bproc.camera.add_camera_pose(cam.matrix_world)
        
    #     # 프레임 범위 설정 (모든 카메라 포즈 렌더링)
    #     bpy.context.scene.frame_start = frame
    #     bpy.context.scene.frame_end = frame + len(cameras)
        
    #     # **배치 렌더링 실행**
    #     # 모든 카메라 포즈에서 렌더링 (키프레임 개수만큼)
    #     data = bproc.renderer.render()
        
    #     # **각 카메라별로 결과 저장**
    #     for i, cam in enumerate(cameras):
    #         # HDF5 저장
    #         hdf5_path = os.path.join(OUTPUT_DIR, "hdf5", f'{frame:04d}_{cam.name}.hdf5')
    #         os.makedirs(os.path.dirname(hdf5_path), exist_ok=True)
    #         pdb.set_trace()
    #         # bproc.writer.write_hdf5(hdf5_path, {
    #         #     "instance_segmaps": [data["instance_segmaps"][i]],
    #         #     "instance_attribute_maps": [data["instance_attribute_maps"][i]], 
    #         #     "colors": [data["colors"][i]],
    #         # })
            
    #         # COCO 저장
    #         coco_dir = os.path.join(OUTPUT_DIR, 'coco_data')
    #         os.makedirs(coco_dir, exist_ok=True)
            
    #         bproc.writer.write_coco_annotations(
    #             coco_dir,
    #             instance_segmaps=[data["instance_segmaps"][i]],
    #             instance_attribute_maps=[data["instance_attribute_maps"][i]],
    #             colors=[data["colors"][i]],
    #             color_file_format="JPEG",
    #             file_prefix=f'{scene_num}_{cam.name}_',
    #             indent=4
    #         )

    #         bproc.writer.write_coco_annotations(coco_dir,instance_segmaps=data["instance_segmaps"],instance_attribute_maps=data["instance_attribute_maps"],colors=data["colors"],color_file_format="JPEG",file_prefix=f'{scene_num}_{cam.name}_',indent=4)

    #         pdb.set_trace()
    #         print(f'COCO annotations saved for scene_num {scene_num} and camera {cam.name}')
            
    #         # Numpy instance_segmap 저장
    #         segmap_dir = os.path.join(OUTPUT_DIR, 'instance_segmap')
    #         os.makedirs(segmap_dir, exist_ok=True)
    #         np.save(os.path.join(segmap_dir, f'{scene_num}_{cam.name}.npy'),
    #                 data["instance_segmaps"][i])
