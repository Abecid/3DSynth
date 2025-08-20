import bpy
from config import *

def setup_physics():
    """물리 시뮬레이션 환경 설정"""
    scene = bpy.context.scene
    scene.rigidbody_world.enabled = True
    scene.frame_start = FRAME_START
    scene.frame_end = FRAME_END
    scene.frame_current = FRAME_START
    scene.rigidbody_world.effector_weights.gravity = 1.0

def run_physics_simulation():
    """물리 시뮬레이션 실행"""
    scene = bpy.context.scene
    scene.frame_set(FRAME_START)
    bpy.ops.ptcache.bake_all(bake=True) 