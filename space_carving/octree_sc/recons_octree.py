import numpy as np
import json
import imageio as io
import glob
import multi_view_reconstruction_octree as mvr
import os
import time
import open3d as o3d 

def get_integrale_image(img):
    a = np.zeros_like(img, dtype=int)
    a[img > 0] = 1
    for y, x in np.ndindex(a.shape):
        if x - 1 >= 0:
            a[y, x] += a[y, x - 1]
        if y - 1 >= 0:
            a[y, x] += a[y - 1, x]
        if x - 1 >= 0 and y - 1 >= 0:
            a[y, x] -= a[y - 1, x - 1]
    return a

def get_projection(K, rot, tvec):
    def projection(point):
        point=np.array(point)
        x = rot @ point + tvec
        x = K @ x
        x = x / x[2,]
        return x[:2]
    return projection

def mk_image_views(folder, im_params, K):
   views=[]
   ims=glob.glob(folder+"*")
   ims.sort()
   for i in range(len(ims)):
      rotmat = np.array(im_params[i]["rotmat"])
      tvec = np.array(im_params[i]["tvec"])
      im=io.imread(ims[i])
      projection=get_projection(K, rotmat, tvec) 	
      views.append((im, projection))
   return views   

def mk_image_views_fake(folder, im_params, K):
   views=[]
   ims=glob.glob(folder+"*")
   ims.sort()
   im=get_fake_im(130)
   for i in range(len(ims)):
      rotmat = np.array(im_params[i]["rotmat"])
      tvec = np.array(im_params[i]["tvec"])
      projection=get_projection(K, rotmat, tvec)  
      views.append((im, projection))
   return views   

def mk_image_views_blender(folder, K):
   views=[]
   ims=glob.glob(folder+"images/*")
   ims.sort()

   for i in range(len(ims)):
      #print("Building views: %s / %s"%(i,len(ims))) 
      im=io.imread(ims[i])
      cam_file=folder+"metadata/images/"+os.path.basename(ims[i])[:-4]+".json"
      camera=json.load(open(cam_file))
      rotmat = np.array(camera["R"])
      tvec = np.array(camera["T"])
      projection=get_projection(K, rotmat, tvec)  
      views.append((im, projection))
   return views   

def get_fake_im(r):
  import cv2
  a=cv2.imread("visual_hull/2018-12-17_17-05-35/Masks/rgb-000.jpg",0)
  z=np.zeros_like(a)
  z2=cv2.circle(z,(808,540),r,255,-1)
  return z2

def recons(im_folder, pcdfile, voxel_size):
   cam_file=folder+"/metadata/images/arabidopsis002_image000.json"
   camera=json.load(open(cam_file))

   intrinsics = camera["camera_model"]["params"]
   K = np.array([[intrinsics[0], 0, intrinsics[2]],
                 [0, intrinsics[1], intrinsics[3]], [0, 0, 1]])

   image_views=mk_image_views_blender(im_folder, K)

   octree, lns=mvr.reconstruction_3d_octree(image_views,
                            voxels_size=vs,
                            error_tolerance=0,
                            voxel_center_origin=(0.0, 0.0, 0.0),
                            world_size=128,
                            verbose=True)

   points=[]
   for l in lns:
      points.append(list(l.position))

   pcl = o3d.geometry.PointCloud()
   pcl.points=o3d.utility.Vector3dVector(points)
   o3d.io.write_point_cloud(folder+pcdfile, pcl) 


t0=time.time()

vs=1
folder="/home/kodda/Dropbox/p2pflab/RL_NBV/scanner/virtual_arabidopsis/arabidopsis002/"
pcdfile="recons_octree.ply"

recons(folder, pcdfile, vs)

print(time.time()-t0)
