import numpy as np
import random
import mathutils

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

def compute_axes_lengths(obj):
    """Return x, y, z axis vectors (and lengths) from the object's center."""
    # Get bounding-box corners in world space
    bb = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]
    bb = np.array([v[:] for v in bb])
    
    # Center and full size
    center = (bb.max(axis=0) + bb.min(axis=0)) / 2
    full_lengths = bb.max(axis=0) - bb.min(axis=0)
    half_lengths = full_lengths / 2

    # Create axis vectors from the center (like local x, y, z coverage)
    axes = {
        "x": ([half_lengths[0], 0, 0]),
        "y": ([0, half_lengths[1], 0]),
        "z": ([0, 0, half_lengths[2]]),
    }

    return {
        "center": center.tolist(),
        "axes": axes
    }


def compute_pca(obj):
    """Compute PCA on mesh vertices (in world coordinates)."""
    vertices = np.array([obj.matrix_world @ v.co for v in obj.data.vertices])
    vertices_centered = vertices - vertices.mean(axis=0)

    cov = np.cov(vertices_centered.T)
    eigenvalues, eigenvectors = np.linalg.eigh(cov)

    # Sort eigenvalues descending
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[order]
    eigenvectors = eigenvectors[:, order]

    return {
        "eigenvalues": eigenvalues.tolist(),
        "eigenvectors": eigenvectors.tolist()  # each column is a direction vector
    }

def get_orientations(objects, objects_info, key_name="original"):
    """Get the current orientations of objects and store them in objects_info."""
    for obj in objects:
        if obj.type == "MESH":
            if obj.name not in objects_info:
                objects_info[obj.name] = {}
            current_rotation = tuple(obj.matrix_world.to_euler())
            object_info = {
                "rotation": current_rotation,
                "pca": compute_pca(obj),
                "axes_lengths": compute_axes_lengths(obj)
            }
            objects_info[obj.name][key_name] = object_info
