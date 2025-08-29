import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import argparse
import subprocess
from torchvision.datasets import ImageFolder
from torch.utils.data import DataLoader,Dataset
import random
import numpy as np
import json
from itertools import product
import argparse
from config import *
import pdb
parser = argparse.ArgumentParser(description='Generate Dataset using BlenderProc')
parser.add_argument('--glb_dir', type=str, default='/home/donghoon/Blender-python/glb_file_l',
                    help='Directory containing GLB files')
parser.add_argument('--debug', action='store_true',
                    help='Run in debug mode')
args = parser.parse_args()

glb_dir = args.glb_dir
debug_mode = args.debug

glb_file_paths = []
SAMPLE_NUM = 10000
for folder_name in os.listdir(glb_dir):
    if os.path.isdir(os.path.join(glb_dir, folder_name)):
        folder_path = os.path.join(glb_dir, folder_name)
        for file_name in os.listdir(folder_path):
            if file_name.endswith('.glb'):
                glb_file_paths.append(os.path.join(folder_path, file_name))
print(glb_file_paths)
for i, path in enumerate(os.listdir(glb_dir)):
    MAPPING_ID[path] = i + 1
print(MAPPING_ID)
# pdb.set_trace()
offset_path = 'output/coco_data/images'
try:
    offset = int(sorted(os.listdir(offset_path), key=lambda x: int(x.split('_')[0]))[-1].split('_')[0]) 
except: offset = 0
for i in range(SAMPLE_NUM):
    glb_paths = random.sample(glb_file_paths, 10)
    print(glb_paths)
    if debug_mode: 
        subprocess.run(['blenderproc', 'debug', 'main.py', '--glb', *map(str, glb_file_paths), '--scene_num', f'{i + offset}'])
    else:
        subprocess.run(['blenderproc', 'run', 'main.py', '--glb', *map(str, glb_paths), '--scene_num', f'{i + offset}'])


