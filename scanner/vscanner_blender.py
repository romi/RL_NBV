import bpy
import tempfile
from flask import jsonify
from flask import Flask, send_file
from flask import request, send_from_directory
import numpy as np
from flask_restful import Resource, Api
import sys
import glob
import flask
import os
import time
import argparse
from mathutils import Matrix, Vector


materials = ['Color_2', 'Color_0', 'Color_8', 'Color_1', 'Color_7']
data_dir = "/home/david/data/dataset_arabidopsis3d"
pi = 3.14159265

# BKE_camera_sensor_size
def get_sensor_size(sensor_fit, sensor_x, sensor_y):
    if sensor_fit == 'VERTICAL':
        return sensor_y
    return sensor_x

# BKE_camera_sensor_fit
def get_sensor_fit(sensor_fit, size_x, size_y):
    if sensor_fit == 'AUTO':
        if size_x >= size_y:
            return 'HORIZONTAL'
        else:
            return 'VERTICAL'
    return sensor_fit


def move_camera(tx=None, ty=None, tz=None):
    if "--hdri" in argv:
        bpy.context.scene.cycles.film_transparent = False #hdri visible

    # Set camera translation
    scene = bpy.data.scenes["Scene"]
    if tx is not None:
        scene.camera.location[0] = float(tx)
    if ty is not None:
        scene.camera.location[1] = float(ty)
    if tz is not None:
        scene.camera.location[2] = float(tz)
 

def rotate_camera(rx=None, ry=None, rz=None):
    scene = bpy.data.scenes["Scene"]

    # Set camera rotation in euler angles
    scene.camera.rotation_mode = 'XYZ'
    if rx is not None:
        scene.camera.rotation_euler[0] = float(rx)*(pi/180.0)
    if ry is not None:
        scene.camera.rotation_euler[1] = float(ry)*(pi/180.0)
    if rz is not None:
        scene.camera.rotation_euler[2] = float(rz)*(pi/180.0)
    bpy.context.scene.cycles.film_transparent = False


def setup_camera(w, h, f):
    """
    :input w image width
    :input h image height
    :input f focal length (equiv. 35mm)
    """
    scene = bpy.data.scenes["Scene"]

    fov = 90.0

    # Set render resolution
    scene.render.tile_x = 256
    scene.render.tile_y = 256
    
    scene.render.resolution_x = w
    scene.render.resolution_y = h
    scene.render.resolution_percentage = 100

    # Set camera fov in degrees
    scene.camera.data.angle = 2*np.arctan(35/f)
    scene.camera.data.clip_end = 10000
    
def get_K():
    scene = bpy.data.scenes["Scene"]
    camd = scene.camera.data
    f_in_mm = camd.lens
    scale = scene.render.resolution_percentage / 100
    resolution_x_in_px = scale * scene.render.resolution_x
    resolution_y_in_px = scale * scene.render.resolution_y
    sensor_size_in_mm = get_sensor_size(camd.sensor_fit, camd.sensor_width, camd.sensor_height)
    sensor_fit = get_sensor_fit(
        camd.sensor_fit,
        scene.render.pixel_aspect_x * resolution_x_in_px,
        scene.render.pixel_aspect_y * resolution_y_in_px
    )
    pixel_aspect_ratio = scene.render.pixel_aspect_y / scene.render.pixel_aspect_x
    if sensor_fit == 'HORIZONTAL':
        view_fac_in_px = resolution_x_in_px
    else:
        view_fac_in_px = pixel_aspect_ratio * resolution_y_in_px
    pixel_size_mm_per_px = sensor_size_in_mm / f_in_mm / view_fac_in_px
    s_u = 1 / pixel_size_mm_per_px
    s_v = 1 / pixel_size_mm_per_px / pixel_aspect_ratio

    # Parameters of intrinsic calibration matrix K
    u_0 = resolution_x_in_px / 2 - camd.shift_x * view_fac_in_px
    v_0 = resolution_y_in_px / 2 + camd.shift_y * view_fac_in_px / pixel_aspect_ratio
    skew = 0 # only use rectangular pixels

    K = [[s_u, skew, u_0],
        [   0,  s_v, v_0],
        [   0,    0,   1]]
    return K

def get_RT():
    scene = bpy.data.scenes["Scene"]
    cam = scene.camera
    # bcam stands for blender camera
    
    R_bcam2cv = Matrix(
        ((1, 0,  0),
        (0, -1, 0),
        (0, 0, -1)))
    """
    R_bcam2cv = np.array(
        [[1, 0,  0],
        [0, -1, 0],
        [0, 0, -1]])
    """ 
    # Use matrix_world instead to account for all constraints
    location, rotation = cam.matrix_world.decompose()[0:2]
    R_world2bcam = rotation.to_matrix().transposed()

    # Use location from matrix_world to account for constraints:     
    T_world2bcam = -1*R_world2bcam @ location

    # Build the coordinate transform matrix from world to computer vision camera
    R_world2cv = R_bcam2cv @ R_world2bcam
    T_world2cv = R_bcam2cv @ T_world2bcam

    R = np.matrix(R_world2cv)
    T = np.array(T_world2cv)

    return R.tolist(), T.tolist()


def select_by_material(material_name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in bpy.data.objects:
        for m in o.material_slots:
            if material_name in m.name:
                o.select = True

def set_hide_render(ob, val):
    ob.hide_render = val
    for child in ob.children:
        child.hide_render = val
        set_hide_render(child, val)

def select_plant_objects():
    bpy.ops.object.select_all(action='DESELECT')
    for x in bpy.data.objects.keys():
        if 'SHAPEID' in x:
            bpy.data.objects[x].select = True
            bpy.context.scene.objects.active = bpy.data.objects[x]

def show_only_material(material_name):

    bpy.ops.object.select_all(action='DESELECT')
    for x in bpy.data.objects.keys():
        sel = bpy.data.objects[x]
        if 'SHAPEID' in x or 'Plane' in x:
            flag = False
            for m in sel.material_slots:
                if material_name in m.name:
                    flag = True
                    break
            if not flag:
                set_hide_render(sel, True)
            continue
        set_hide_render(sel, False)
    if "--hdri" in argv:
        bpy.context.scene.cycles.film_transparent = True #remove the hdri background

def set_all_visible():
    for x in bpy.data.objects.keys():
        sel = bpy.data.objects[x]
        set_hide_render(sel, False)

def clear_all_rotation():
    for x in bpy.data.objects:
        x.rotation_euler[0] = 0

def load_object(fname, dx = None, dy = None, dz = None):
    """move object by dx, dy, dz if specified"""
    scene = bpy.data.scenes["Scene"]
    loc = scene.camera.location
    rot = scene.camera.rotation_euler
    print("loc=%s"%str(loc))
    print("rot=%s"%str(rot))

    for x in bpy.data.objects:
        if "SHAPEID" in x.name:
            bpy.data.objects.remove(x, True)
    bpy.ops.import_scene.obj(
        filepath=fname)
    imported_object = bpy.context.scene.objects
    clear_all_rotation()

    for obj in imported_object: #Move object
        if dx is not None:
            obj.location.x = float(dx)
        if dy is not None:
            obj.location.y = float(dy)
        if dz is not None:
            obj.location.x = float(dz)

    scene.camera.location = loc
    scene.camera.rotation_euler = rot
    
    #HDRI background
    if "--hdri" in argv:
        current_bg_image = bpy.data.images.load(hdri_folder + hdri_list[int(time.time())%L]) #random hdri background from folder
        env_text_node.image = current_bg_image   
        bpy.context.scene.cycles.film_transparent = False #hdri visible


if 'Cube' in bpy.data.objects:
    bpy.data.objects.remove(bpy.data.objects['Cube'], do_unlink=True)

# ob = bpy.data.objects['Lamp']
# ob.hide_render = True


# using the cycles rendering engine for hdri backgrounds
def setup_hdri():
    #inspired from https://github.com/tduboudi/IAMPS2019-Procedural-Fruit-Tree-Rendering-Framework
    bpy.data.scenes['Scene'].render.engine = 'CYCLES'
    bpy.data.worlds["World"].use_nodes = True
    world_nodes = bpy.data.worlds["World"].node_tree.nodes
    for node in world_nodes:
        world_nodes.remove(node)
    
    node = world_nodes.new("ShaderNodeTexEnvironment")
    node.name = "Environment Texture"
    
    node = world_nodes.new("ShaderNodeBackground")
    node.name = "Background"
    
    node = world_nodes.new("ShaderNodeOutputWorld")
    node.name = "World Output"
    
    output = world_nodes["Environment Texture"].outputs["Color"]
    input = world_nodes["Background"].inputs["Color"]
    bpy.data.worlds["World"].node_tree.links.new(output, input)
    
    output = world_nodes["Background"].outputs["Background"]
    input = world_nodes["World Output"].inputs["Surface"]
    bpy.data.worlds["World"].node_tree.links.new(output, input)
    
    scene = bpy.context.scene
    world = scene.world
    nodes_tree = bpy.data.worlds[world.name].node_tree
    env_text_node = nodes_tree.nodes["Environment Texture"]
    return env_text_node


# the folder in which all HDRIs files are located
#bpy.data.scenes['Scene'].render.engine = 'RENDER'

argv = sys.argv
if "--hdri" in argv:
    hdri_folder = './hdri/'
    #hdri source: https://hdrihaven.com/
    hdri_list = os.listdir(hdri_folder)
    L = len(hdri_list)
    env_text_node = setup_hdri()
    
setup_camera(1616, 1080, 24)
move_camera(-100, 0, 50)
rotate_camera(90, 0, -90)

class ObjectLoader(Resource):
    def get(self, name):
        dx = request.args.get('dx')
        dy = request.args.get('dy')
        dz = request.args.get('dz')
        fpath = os.path.join(data_dir, "%s.obj"%name)
        print(fpath)
        load_object(fpath, dx, dy, dz)
        move_camera(-100, 0, 50)
        rotate_camera(90, 0, -90)
        return {"success": True}

class Objects(Resource):
    def get(self):
        l = glob.glob(os.path.join(data_dir, "*.obj"))
        l = [os.path.splitext(os.path.basename(x))[0] for x in l]
        return l

class Materials(Resource):
    def get(self):
        return materials

class Move(Resource):
    def get(self):
        x = request.args.get('x')
        y = request.args.get('y')
        z = request.args.get('z')
        rx = request.args.get('rx')
        ry = request.args.get('ry')
        rz = request.args.get('rz')
        print("translation = %s, %s, %s"%(x,y,z))
        print("rotation = %s, %s, %s"%(rx,ry,rz))
        move_camera(x, y, z)
        rotate_camera(rx, ry, rz)
        return {"success": True}

class Render(Resource):
    def get(self):
        mat = request.args.get('mat')
        set_all_visible()
        with tempfile.TemporaryDirectory() as td:
            if mat is None:
                bpy.context.scene.render.filepath = os.path.join(td, "plant.png")
                bpy.ops.render.render(write_still=True)
            else:
                show_only_material(mat)
                #ob = bpy.data.objects['Lamp']
                scene = bpy.context.scene
                lamp_objects = [o for o in scene.objects if o.type == 'LAMP']
                for ob in lamp_objects: ob.hide_render = True
                bpy.context.scene.render.filepath = os.path.join(td, "plant.png")
                bpy.ops.render.render(write_still=True)
                for ob in lamp_objects: ob.hide_render = False
            return send_from_directory(td, "plant.png")

class RenderAndSave(Resource):
    def get(self):
       path = request.args.get('path')
       bpy.context.scene.render.filepath = os.path.join(path, "plant.png")
       bpy.ops.render.render(write_still=True)
       return {"succes": True}

        
class Save(Resource):
    def get(self):
         bpy.ops.wm.save_as_mainfile(filepath="plant.blend")
         return {"success" : True}

class CameraSetup(Resource):
    def get(self):
        w = request.args.get('w')
        h = request.args.get('h')
        f = request.args.get('f')
        if w is None or h is None or f is None:
            raise Exception("Missing argument w h or f")
        setup_camera(int(w), int(h), int(f))

class CameraIntrinsics(Resource):
    def get(self):
        scene = bpy.data.scenes["Scene"]
        K=get_K()
        camera_model = {
                    "width" : scene.render.resolution_x,
                    "height" : scene.render.resolution_y,
                    "model" : "OPENCV",
                    "params" : [ K[0][0], K[1][1], K[0][2], K[1][2], 0.0, 0.0, 0.0, 0.0 ]
                }

        return camera_model

class BoundingBox(Resource):
    def get(self):
            scene = bpy.context.scene
            
            xmin, ymin, zmin = 10000, 10000, 10000
            xmax, ymax, zmax = -10000, -10000, -10000
            for o in bpy.data.objects:
                m = o.matrix_world
                if not(o.name in ['Camera','Light']):
                   for b in o.bound_box:
                        x,y,z = b
                        xmin, ymin, zmin = np.minimum([xmin, ymin, zmin], [x,y,z])
                        xmax, ymax, zmax = np.maximum([xmax, ymax, zmax], [x,y,z])

            bbox ={
                "x" : [xmin, xmax],
                "y" : [ymin, ymax],
                "z" : [zmin, zmax]
            }
            return bbox

class CameraExtrinsics(Resource):
    def get(self):
        R,T= get_RT()
        return  {"R":R,"T":T}


app = Flask(__name__)
api = Api(app)

api.add_resource(ObjectLoader, '/load/<name>')
api.add_resource(Objects, '/objects')
api.add_resource(Materials, '/materials')
api.add_resource(Move, '/move')
api.add_resource(Render, '/render')
api.add_resource(RenderAndSave, '/render_and_save')
api.add_resource(Save, '/save')
api.add_resource(CameraSetup, '/camera')
api.add_resource(CameraIntrinsics, '/camera_intrinsics')
api.add_resource(CameraExtrinsics, '/camera_extrinsics')
api.add_resource(BoundingBox, '/bounding_box')

"""
cuda_devs, cl_devs = bpy.context.preferences.addons['cycles'].preferences.get_devices()
bpy.context.scene.render.engine = 'CYCLES'# echo $PYTHONPATH
# Set the device_type
bpy.context.preferences.addons["cycles"].preferences.compute_device_type = "CUDA"
# Set the device and feature set
bpy.context.scene.cycles.device = "GPU"
bpy.context.scene.cycles.feature_set = "SUPPORTED"
"""
"""
bpy.context.preferences.addons['cycles'].preferences.compute_device_type = 'CUDA'

bpy.context.preferences.addons['cycles'].preferences.get_devices()
bpy.context.preferences.addons['cycles'].preferences.devices[1].use= True

bpy.context.scene.cycles.device = 'GPU'

bpy.context.scene.render.tile_x = 256
bpy.context.scene.render.tile_y = 256
"""

app.run(debug=False, host="0.0.0.0")


# for i,m in enumerate(materials):
#     show_only_material(m)
#     bpy.context.scene.render.filepath = "./render/plant_%i.png"%i
#     bpy.ops.render.render(write_still=True)



