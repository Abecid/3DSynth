import json
import random
from pathlib import Path
import argparse
import os
import sys


parser = argparse.ArgumentParser(description='Train-Val Split for COCO Annotations')
parser.add_argument('--path', type=str, default='/home/donghoon/Blender-python/output/coco_data/coco_annotations.json',
                    help='Input COCO annotation JSON file')
args = parser.parse_args()
# 원본 COCO JSON

coco_file = Path(args.path)
with open(coco_file) as f:
    coco = json.load(f)

images = coco["images"]
annotations = coco["annotations"]
categories = coco["categories"]

# Shuffle images
random.shuffle(images)

# 80% train, 20% val
split_idx = int(0.8 * len(images))
train_images = images[:split_idx]
val_images = images[split_idx:]

# image id set
train_ids = {img["id"] for img in train_images}
val_ids = {img["id"] for img in val_images}

# annotations split
train_annotations = [ann for ann in annotations if ann["image_id"] in train_ids]
val_annotations = [ann for ann in annotations if ann["image_id"] in val_ids]

# 새로운 JSON 생성
train_coco = {
    "images": train_images,
    "annotations": train_annotations,
    "categories": categories
}

val_coco = {
    "images": val_images,
    "annotations": val_annotations,
    "categories": categories
}
os.makedirs(os.path.join(os.path.dirname(args.path), 'annotations'), exist_ok=True)
# 저장
with open(os.path.join(os.path.dirname(args.path), 'annotations/instances_train.json'), "w") as f:
    json.dump(train_coco, f, indent=4)
with open(os.path.join(os.path.dirname(args.path), 'annotations/instances_val.json'), "w") as f:
    json.dump(val_coco, f, indent=4)

print(f"Train: {len(train_images)} images, Val: {len(val_images)} images")
