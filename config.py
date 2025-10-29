import os

# Mapping ID for GLB files
MAPPING_ID = {'상온HMR': 13, '과자': 15, '주류': 6, '커피차': 1, '소스': 7, '통조림': 16, '생활용품': 12, '면류': 8, '의약외품': 3, '음료': 5, '이-미용': 2, '유제품': 10, '홈클린': 11, '빵': 9, '안주': 14}
# 파일 경로
BOARD_PATH = "assets/board.glb"
GLB_PATHS = []
OUTPUT_DIR = "output"
HDRI_DIR = "background"

# 시뮬레이션 설정
MOVE_RANGE = (-5, 5)
FRAME_START = 1
FRAME_END = 300
RENDER_FRAMES = [300]

# 카메라 설정
NUM_CAMERAS = 5
CAMERA_RADIUS_RANGE = (15.0, 20.0)
CAMERA_Z = 10
RENDER_RESOLUTION = (640, 480)

# 벽 설정
WALL_POSITIONS = [(8, 0, 2), (-8, 0, 2), (0, 8, 2), (0, -8, 2)]
WALL_SCALES = [(0.5, 8, 50), (0.5, 8, 50), (8, 0.5, 50), (8, 0.5, 50)]

# Cycles 설정
CYCLES_SAMPLES = 128
CYCLES_PREVIEW_SAMPLES = 32 