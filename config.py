import os
# Mapping ID for GLB files
MAPPING_ID = {'can': 1, 'bottle': 2, 'box': 3, 'cup': 4, 'plate': 5}

# 파일 경로
BOARD_PATH = "/home/donghoon/Blender-python/glb_files/board.glb"
GLB_PATHS = [
    "/home/donghoon/Blender-python/glb_files/textured_mesh.glb",
] * 10
JSON_PATH = "/home/donghoon/Blender-python/glb_files/can/size.json"
OUTPUT_DIR = "/home/donghoon/Blender-python/output"
HDRI_DIR = "/home/donghoon/Blender-python/background"

# 시뮬레이션 설정
MOVE_RANGE = (-5, 5)
FRAME_START = 1
FRAME_END = 200
RENDER_FRAMES = [200]

# 카메라 설정
NUM_CAMERAS = 14
CAMERA_RADIUS_RANGE = (15.0, 20.0)
CAMERA_Z = 10
RENDER_RESOLUTION = 512

# 벽 설정
WALL_POSITIONS = [(8, 0, 2), (-8, 0, 2), (0, 8, 2), (0, -8, 2)]
WALL_SCALES = [(0.5, 8, 50), (0.5, 8, 50), (8, 0.5, 50), (8, 0.5, 50)]

# Cycles 설정
CYCLES_SAMPLES = 128
CYCLES_PREVIEW_SAMPLES = 32 