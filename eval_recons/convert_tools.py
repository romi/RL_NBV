import os
import pymesh
import open3d
import numpy as np
import proc3d

def obj2ply(file, folder): 
   mesh = pymesh.load_mesh(folder+file)
   pymesh.save_mesh_raw(folder+os.path.basename(file)[:-4]+"_mesh.ply", mesh.vertices, mesh.faces, mesh.voxels)

def mesh2pcd(file, folder, N):
   meshfile=folder+os.path.basename(file)[:-4]+"_mesh.ply"
   mesh=open3d.io.read_triangle_mesh(meshfile)

   pcd_poisson=mesh.sample_points_poisson_disk(N)

   open3d.io.write_point_cloud(folder+os.path.basename(file)[:-4]+"_gt.ply", pcd_poisson)

"""
folder = "/home/kodda/Dropbox/p2pflab/RL_NBV/scanner/data/"
file ="arabidopsis_2.obj"

N=20000
obj2ply(file, folder)
mesh2pcd(file, folder, N)
"""

pcdfile="/home/kodda/Dropbox/p2pflab/RL_NBV/scanner/virtual_arabidopsis/arabidopsis002/rec_octree.ply"
pcd=open3d.io.read_point_cloud(pcdfile)

vol, origin=proc3d.pcd2vol(pcd, .4)
pcd2=proc3d.vol2pcd(vol, origin, .4, level_set_value=.3)

open3d.visualization.draw_geometries([pcd2])
