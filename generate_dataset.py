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

glb_file_paths = []

for folder_name in os.listdir('/home/donghoon/Blender-python/glb_files'):
    if os.path.isdir(os.path.join('/home/donghoon/Blender-python/glb_files', folder_name)):
        folder_path = os.path.join('/home/donghoon/Blender-python/glb_files', folder_name)
        for file_name in os.listdir(folder_path):
            if file_name.endswith('.glb'):
                glb_file_paths.append(os.path.join(folder_path, file_name))

for _ in range(SAMPLE_NUM):
    glb_paths = random.sample(glb_file_paths, 10)


