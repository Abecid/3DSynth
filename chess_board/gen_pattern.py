import numpy as np
import cv2
import tempfile
import os

def create_chessboard_with_border(cols=7, rows=10, square_size=50, border_size=30):
    pattern_width = cols * square_size
    pattern_height = rows * square_size

    width = pattern_width + 2 * border_size
    height = pattern_height + 2 * border_size

    img = np.ones((height, width), dtype=np.uint8) * 255

    for y in range(rows):
        for x in range(cols):
            if (x + y) % 2 == 0:
                top_left_x = border_size + x * square_size
                top_left_y = border_size + y * square_size
                cv2.rectangle(img,
                              (top_left_x, top_left_y),
                              (top_left_x + square_size, top_left_y + square_size),
                              255 * 0.8,
                              thickness=-1)
    return img

chess_img = create_chessboard_with_border(cols=8, rows=11, square_size=50, border_size=200)
cv2.imwrite("chessboard_texture.png", chess_img)
