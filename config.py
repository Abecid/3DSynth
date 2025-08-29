import os
# Mapping ID for GLB files
MAPPING_ID = {'상온HMR': 1, '과자': 2, '주류': 3, '커피차': 4, '소스': 5, '통조림': 6, '생활용품': 7, '면류': 8, '의약외품': 9, '음료': 10, '이-미용': 11, '유제품': 12, '홈클린': 13}
# 파일 경로
BOARD_PATH = "/home/donghoon/Blender-python/glb_files/board.glb"
GLB_PATHS = [
    "/home/donghoon/Blender-python/glb_files/can/can1.glb",
] * 10
OUTPUT_DIR = "/home/donghoon/Blender-python/output"
HDRI_DIR = "/home/donghoon/Blender-python/background"

# 시뮬레이션 설정
MOVE_RANGE = (-5, 5)
FRAME_START = 1
FRAME_END = 300
RENDER_FRAMES = [300]

# 카메라 설정
NUM_CAMERAS = 5
CAMERA_RADIUS_RANGE = (15.0, 20.0)
CAMERA_Z = 10
RENDER_RESOLUTION = 512

# 벽 설정
WALL_POSITIONS = [(8, 0, 2), (-8, 0, 2), (0, 8, 2), (0, -8, 2)]
WALL_SCALES = [(0.5, 8, 50), (0.5, 8, 50), (8, 0.5, 50), (8, 0.5, 50)]

# Cycles 설정
CYCLES_SAMPLES = 128
CYCLES_PREVIEW_SAMPLES = 32 