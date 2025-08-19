import cv2
import numpy as np
import os
import json
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# 파일 경로 설정
output_dir = "/home/donghoon/Blender-python/output"
annotation_file = os.path.join(output_dir, "annotations.json")
rgb_file = os.path.join(output_dir, "rgb0200.jpg")
# seg_file = os.path.join(output_dir, "segmentation_mask0200.png")

# RGB 이미지 로드
rgb_image = cv2.imread(rgb_file)
rgb_image = cv2.cvtColor(rgb_image, cv2.COLOR_BGR2RGB)
height, width = rgb_image.shape[:2]

# 세그멘테이션 이미지 로드 (PNG 파일)
seg_image = None
# if os.path.exists(seg_file):
#     seg_image = cv2.imread(seg_file, cv2.IMREAD_GRAYSCALE)

# COCO 형식 어노테이션 파일 파싱
annotations_data = []
categories_data = {}

if os.path.exists(annotation_file):
    with open(annotation_file, 'r') as f:
        coco_data = json.load(f)
    
    # 카테고리 정보 매핑 (id -> name)
    for category in coco_data.get('categories', []):
        categories_data[category['id']] = category['name']
    
    # 어노테이션 정보 추출
    annotations_data = coco_data.get('annotations', [])

# 세그멘테이션 마스크 처리
if seg_image is not None:
    # PNG 파일은 이미 grayscale로 로드되므로 바로 사용
    seg_mask = seg_image
    
    # 고유한 세그멘테이션 ID들 찾기
    unique_ids = np.unique(seg_mask)
    unique_ids = unique_ids[unique_ids > 0]  # 배경(0) 제외
    
    # 컬러맵 생성 (각 객체마다 다른 색상)
    if len(unique_ids) > 0:
        colors = plt.cm.tab20(np.linspace(0, 1, min(len(unique_ids), 20)))
        if len(unique_ids) > 20:
            # 20개 이상의 객체가 있으면 추가 컬러맵 사용
            colors2 = plt.cm.Set3(np.linspace(0, 1, len(unique_ids) - 20))
            colors = np.vstack([colors, colors2])
    else:
        colors = []
    
    # 세그멘테이션 컬러 이미지 생성
    seg_colored = np.zeros((height, width, 3), dtype=np.uint8)
    
    for i, seg_id in enumerate(unique_ids):
        if i < len(colors):
            mask = seg_mask == seg_id
            color = (colors[i][:3] * 255).astype(np.uint8)
            seg_colored[mask] = color
    
    # RGB 이미지와 세그멘테이션 블렌딩
    alpha = 0.4  # 세그멘테이션 투명도
    blended_image = rgb_image.copy()
    
    # 세그멘테이션이 있는 부분만 블렌딩
    seg_mask_bool = seg_mask > 0
    blended_image[seg_mask_bool] = (
        (1 - alpha) * rgb_image[seg_mask_bool] + 
        alpha * seg_colored[seg_mask_bool]
    ).astype(np.uint8)
else:
    blended_image = rgb_image.copy()
    seg_colored = None

# 바운딩 박스 그리기
bbox_colors = [
    (255, 0, 0),    # Red
    (0, 255, 0),    # Green  
    (0, 0, 255),    # Blue
    (255, 255, 0),  # Yellow
    (255, 0, 255),  # Magenta
    (0, 255, 255),  # Cyan
    (128, 0, 128),  # Purple
    (255, 165, 0),  # Orange
]

for i, annotation in enumerate(annotations_data):
    # COCO 형식 바운딩 박스: [x, y, width, height] (픽셀 좌표)
    bbox = annotation['bbox']
    x_min = int(bbox[0])
    y_min = int(bbox[1])
    x_max = int(bbox[0] + bbox[2])
    y_max = int(bbox[1] + bbox[3])
    
    # 바운딩 박스 색상 선택
    color = bbox_colors[i % len(bbox_colors)]
    
    # 바운딩 박스 그리기
    cv2.rectangle(blended_image, (x_min, y_min), (x_max, y_max), color, 2)
    
    # 객체 이름 라벨 추가 (카테고리 ID로 이름 찾기)
    category_id = annotation['category_id']
    obj_name = categories_data.get(category_id, f"Object_{category_id}")
    label = f"{obj_name}"
    label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
    
    # 라벨 배경 그리기
    cv2.rectangle(blended_image, 
                 (x_min, y_min - label_size[1] - 10),
                 (x_min + label_size[0], y_min),
                 color, -1)
    
    # 라벨 텍스트 그리기
    cv2.putText(blended_image, label,
                (x_min, y_min - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

# 결과 이미지 저장
result_file = os.path.join(output_dir, "visualization.jpg")
result_image_bgr = cv2.cvtColor(blended_image, cv2.COLOR_RGB2BGR)
cv2.imwrite(result_file, result_image_bgr)

# 추가로 바운딩 박스만 있는 이미지도 저장
bbox_only_image = rgb_image.copy()
for i, annotation in enumerate(annotations_data):
    # COCO 형식 바운딩 박스: [x, y, width, height] (픽셀 좌표)
    bbox = annotation['bbox']
    x_min = int(bbox[0])
    y_min = int(bbox[1])
    x_max = int(bbox[0] + bbox[2])
    y_max = int(bbox[1] + bbox[3])
    
    # 바운딩 박스 색상 선택
    color = bbox_colors[i % len(bbox_colors)]
    
    # 바운딩 박스 그리기
    cv2.rectangle(bbox_only_image, (x_min, y_min), (x_max, y_max), color, 2)
    
    # 객체 이름 라벨 추가 (카테고리 ID로 이름 찾기)
    category_id = annotation['category_id']
    obj_name = categories_data.get(category_id, f"Object_{category_id}")
    label = f"{obj_name}"
    label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
    
    # 라벨 배경 그리기
    cv2.rectangle(bbox_only_image, 
                 (x_min, y_min - label_size[1] - 10),
                 (x_min + label_size[0], y_min),
                 color, -1)
    
    # 라벨 텍스트 그리기
    cv2.putText(bbox_only_image, label,
                (x_min, y_min - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

bbox_result_file = os.path.join(output_dir, "bbox_visualization.jpg")
bbox_result_bgr = cv2.cvtColor(bbox_only_image, cv2.COLOR_RGB2BGR)
cv2.imwrite(bbox_result_file, bbox_result_bgr)

# 세그멘테이션만 있는 이미지도 저장
if seg_colored is not None:
    seg_only_file = os.path.join(output_dir, "segmentation_visualization.jpg")
    seg_result_bgr = cv2.cvtColor(seg_colored, cv2.COLOR_RGB2BGR)
    cv2.imwrite(seg_only_file, seg_result_bgr)
