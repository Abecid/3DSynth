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
SAMPLE_NUM = 1000
for folder_name in os.listdir('/home/donghoon/Blender-python/glb_files'):
    if os.path.isdir(os.path.join('/home/donghoon/Blender-python/glb_files', folder_name)):
        folder_path = os.path.join('/home/donghoon/Blender-python/glb_files', folder_name)
        for file_name in os.listdir(folder_path):
            if file_name.endswith('.glb'):
                glb_file_paths.append(os.path.join(folder_path, file_name))
print(glb_file_paths)

# subprocess.run(['blenderproc', 'debug', 'main.py', '--glb', *map(str, glb_file_paths)])
for _ in range(SAMPLE_NUM):
    glb_paths = random.sample(glb_file_paths, 10)
    print(glb_paths)
    subprocess.run(['blenderproc', 'run', 'main.py', '--glb', *map(str, glb_paths)])

