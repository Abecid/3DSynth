import sys
sys.path.append("/Users/byunghunlee/.local/lib/python3.11/site-packages")

import bpy
import bmesh
import numpy as np
import json
import cv2
from mathutils import Matrix, Vector, Euler

def load_camera(camera_config_path='stereo_config_online.json'):
    with open(camera_config_path, 'r') as f:
        cameras = json.load(f)['cameras']
    r_transform_blender_format = np.array([[1, 0, 0], [0, -1, 0], [0, 0, -1]])
    sensor_width = 4.8
    sensor_height = 3.6
    image_width = 640
    image_height = 480
    for c in cameras:
        name = c['name']
        R = np.array(c['R'])
        tvec = np.array(c['t']).T
        K = np.array(c['K'])
        d = np.array(c['distCoef'])
        rvec = cv2.Rodrigues(R)[0]
        fx = K[0][0]
        cx = K[0][2]
        fy = K[1][1]
        cy = K[1][2]

        #ttc, euler = opencv_pose_to_blender(rvec, tvec)

        Rb = r_transform_blender_format @ R
        tc = -R.T @ tvec / 1000.0
        fmm = fx * sensor_width / image_width
        M = Matrix((
            (Rb[0,0], Rb[1,0], Rb[2,0], 0),
            (Rb[0,1], Rb[1,1], Rb[2,1], 0),
            (Rb[0,2], Rb[1,2], Rb[2,2], 0),
            (0,0,0,1)
        ))
        sx = -(cx - image_width / 2) / image_width
        sy = (cy - image_height / 2) / image_height

        cam_data = bpy.data.cameras.new(name)
        cam_obj = bpy.data.objects.new(name, cam_data)
        bpy.context.collection.objects.link(cam_obj)

        cam_data.sensor_width = sensor_width
        cam_data.sensor_height = sensor_height
        cam_data.lens = fmm
        cam_data.shift_x = sx
        cam_data.shift_y = sy

        cam_obj.rotation_mode = 'XYZ'
        cam_obj.rotation_euler = M.to_euler('XYZ')
        cam_obj.location = Vector(tc.flatten())
        cam_obj.scale = (0.1, 0.1, 0.1)

if __name__ == '__main__':
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # camera setup
    load_camera()

    bpy.ops.mesh.primitive_cube_add(size=0.5, location=(0.066, 0.110, -0.025), scale=(0.36/0.5, 1.0, 0.1))
    cube = bpy.context.active_object

    mesh = cube.data
    bm = bmesh.new()
    bm.from_mesh(mesh)

    front_face = None
    for face in bm.faces:
        if face.normal.z > 0.99:
            front_face = face
    bm.faces.ensure_lookup_table()
    uv_layer = bm.loops.layers.uv.verify()

    for face in bm.faces:
        for loop in face.loops:
            loop[uv_layer].uv = (0, 0)

    uv_scale = 1.0
    uv_offset = (1 - uv_scale) / 2
    front_face.loops[0][uv_layer].uv = (uv_offset, uv_offset)
    front_face.loops[1][uv_layer].uv = (uv_offset + uv_scale, uv_offset)
    front_face.loops[2][uv_layer].uv = (uv_offset + uv_scale, uv_offset + uv_scale)
    front_face.loops[3][uv_layer].uv = (uv_offset, uv_offset + uv_scale)

    bm.to_mesh(mesh)
    bm.free()

    mat = bpy.data.materials.new(name="ChessboardMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    nodes.clear()

    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    diffuse_node = nodes.new(type='ShaderNodeBsdfPrincipled')
    tex_image_node = nodes.new(type='ShaderNodeTexImage')

    img_blender = bpy.data.images.load('/Users/byunghunlee/workspace/blender/chessboard_texture.png')
    tex_image_node.image = img_blender

    links.new(tex_image_node.outputs['Color'], diffuse_node.inputs['Base Color'])
    links.new(diffuse_node.outputs['BSDF'], output_node.inputs['Surface'])

    if cube.data.materials:
        cube.data.materials[0] = mat
    else:
        cube.data.materials.append(mat)

    scene = bpy.context.scene
    scene.render.resolution_x = 640
    scene.render.resolution_y = 480
    scene.render.resolution_percentage = 100  # 100% 크기 출력

    bpy.ops.wm.save_as_mainfile(filepath='./cams.blend')

    # render
    '''
    bpy.ops.object.camera_add(location=(5, -5, 5), rotation=(1.1, 0, 0.8))
    bpy.context.scene.camera = bpy.context.active_object
    bpy.context.scene.render.filepath = "./cube.png"
    bpy.context.scene.render.resolution_x = 640
    bpy.context.scene.render.resolution_y = 480
    bpy.ops.render.render(write_still=True)
    '''
