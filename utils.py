import numpy as np
import random

def encode_rle(mask):
    """이진 마스크를 RLE로 인코딩"""
    pixels = mask.flatten()
    pixels = np.concatenate([[0], pixels, [0]])
    runs = np.where(pixels[1:] != pixels[:-1])[0] + 1
    runs[1::2] -= runs[::2]
    return runs.tolist()

def random_value(min_val, max_val):
    """50% 확률로 양수/음수 범위에서 랜덤값 반환"""
    if np.random.rand() < 0.5:
        return random.uniform(min_val, max_val)
    else:
        return random.uniform(-max_val, -min_val) 