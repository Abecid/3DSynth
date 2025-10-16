#!/usr/bin/env python3
import blenderproc as bproc
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
script_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
sys.path.append(script_dir)

import json
import importlib.util
import time

config_path = os.path.join(script_dir, "config.py")
spec = importlib.util.spec_from_file_location("config", config_path)
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)

import argparse
from config import OUTPUT_DIR, GLB_PATHS, RENDER_FRAMES, NUM_CAMERAS, RENDER_RESOLUTION

def main():
    global OUTPUT_DIR, GLB_PATHS, RENDER_FRAMES, NUM_CAMERAS, RENDER_RESOLUTION

    
    parser = argparse.ArgumentParser(description='BlenderProc Physics Simulation and Rendering')
    parser.add_argument('--output', '-o', default=OUTPUT_DIR, 
                       help='Output directory path')
    parser.add_argument('--frames', '-f', nargs='+', type=int, default=RENDER_FRAMES,
                       help='Frames to render (e.g., --frames 50 100 200)')
    parser.add_argument('--glb', '-g', nargs='+', type=str, default=[],
                       help='Frames to render (e.g., --frames /home/donghoon/Blender-python/glb_files/textured_mesh.glb /home/donghoon/Blender-python/glb_files/textured_mesh.glb /home/donghoon/Blender-python/glb_files/textured_mesh.glb)')
    parser.add_argument('--cameras', '-c', type=int, default=NUM_CAMERAS,
                       help='Number of cameras to create')
    parser.add_argument('--resolution', '-r', type=int, default=RENDER_RESOLUTION,
                       help='Render resolution (square)')
    parser.add_argument('--no-gpu', action='store_true',
                       help='Disable GPU rendering')
    parser.add_argument('--scene_num', type=str, default='',
                       help='Scene number identifier for output files')
    args = parser.parse_args()
    
    # 설정 업데이트

    # config 모듈의 변수들을 동적으로 업데이트
    import config
    config.OUTPUT_DIR = args.output
    config.GLB_PATHS = args.glb
    config.RENDER_FRAMES = args.frames
    config.NUM_CAMERAS = args.cameras
    config.RENDER_RESOLUTION = args.resolution
    # 출력 디렉토리 생성
    os.makedirs(args.output, exist_ok=True)
    
    print(f"Starting BlenderProc simulation...")
    print(f"Output directory: {args.output}")
    print(f"Render frames: {args.frames}")
    print(f"Number of cameras: {args.cameras}")
    print(f"Resolution: {args.resolution}x{args.resolution}")
    
    # BlenderProc 초기화
    bproc.init()
    start = time.time()

    from scene_setup import setup_gpu, clear_scene, create_board, create_walls, import_and_setup_objects, setup_hdri
    from physics import setup_physics, run_physics_simulation
    from rendering import create_cameras, setup_blenderproc_rendering, render_all_cameras
    from utils import get_orientations
    # GPU 설정 (옵션)
    if not args.no_gpu:
        setup_gpu()
        print("GPU rendering enabled")
    
    # 씬 설정
    print("Setting up scene...")
    clear_scene()
    board = create_board()
    walls = create_walls()
    
    objects_info = {}
    imported_objects = import_and_setup_objects(board, walls, objects_info)
    
    import bpy
    print("Render Engine:", bpy.context.scene.render.engine)
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.get_devices()
    for d in prefs.devices: print(d.name, d.type, d.use)
    # 물리 시뮬레이션
    print("Running physics simulation...")
    scene = setup_physics()
    setup_hdri()

    run_physics_simulation(scene)
    get_orientations(bpy.context.scene.objects, objects_info, "final")
    # 카메라 생성 및 렌더링 (물리 시뮬레이션 후)
    print("Creating cameras and rendering...")
    cameras = create_cameras()
    setup_blenderproc_rendering()
    render_all_cameras(cameras, imported_objects, args.scene_num)
    end = time.time()
    print(f"Total time: {end - start:.2f} seconds")
    print(f"Simulation completed! Results saved to: {args.output}")

    # Save objects_info to a JSON file
    with open(os.path.join(args.output, f'objects_info.json'), 'w') as f:
        json.dump(objects_info, f, indent=4)

if __name__ == "__main__":
    main() 