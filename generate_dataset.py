import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import argparse
import subprocess
import random
import argparse
from collections import defaultdict

from config import *

SAMPLE_NUM = 4

def parse_args():
    parser = argparse.ArgumentParser(description='Generate Dataset using BlenderProc')
    parser.add_argument('--glb_dir', type=str, default='assets/Welstory',
                        help='Directory containing GLB files')
    parser.add_argument('--debug', action='store_true',
                        help='Run in debug mode')
    args = parser.parse_args()
    return args

def main(args):
    glb_dir = args.glb_dir

    glb_file_paths = defaultdict(list)
    glb_paths = []

    for folder_name in os.listdir(glb_dir):
        if os.path.isdir(os.path.join(glb_dir, folder_name)):
            folder_path = os.path.join(glb_dir, folder_name)
            for file_name in os.listdir(folder_path):
                if file_name.endswith('.glb'):
                    file_path = os.path.join(folder_path, file_name)
                    glb_file_paths[folder_path.split('/')[-1]].append(file_path)
                    glb_paths.append(file_path)
    print(glb_file_paths)
    for i, path in enumerate(os.listdir(glb_dir)):
        if os.path.isdir(os.path.join(glb_dir, path)):
            MAPPING_ID[path] = i + 1
    print(MAPPING_ID)
    
    glb_paths = random.sample(glb_paths, SAMPLE_NUM)
    print(glb_paths)

    if args.debug: 
        subprocess.run(['blenderproc', 'debug', 'main.py', '--glb', *map(str, glb_file_paths)])
    else:
        subprocess.run(['blenderproc', 'run', 'main.py', '--glb', *map(str, glb_paths)])

if __name__ == "__main__":
    args = parse_args()
    main(args)


