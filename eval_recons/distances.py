import numpy as np
import open3d
import time
from scipy.spatial import cKDTree as KDTree


def chamfer_d(pc_1, pc_2):
    tree = KDTree(pc_1)
    ds, _ = tree.query(pc_2)
    d_21 = np.mean(ds)

    tree = KDTree(pc_2)
    ds, _ = tree.query(pc_1)
    d_12 = np.mean(ds)
    return d_21 + d_12


gt=open3d.io.read_point_cloud("/home/kodda/Dropbox/p2pflab/RL_NBV/scanner/data/arabidopsis_2_gt.ply")
gt_big=open3d.io.read_point_cloud("/home/kodda/Dropbox/p2pflab/RL_NBV/scanner/data/arabidopsis_2_gt_big.ply")

rec_octree=open3d.io.read_point_cloud("/home/kodda/Dropbox/p2pflab/RL_NBV/scanner/virtual_arabidopsis/arabidopsis002/rec_octree.ply")
rec_it=open3d.io.read_point_cloud("/home/kodda/Dropbox/p2pflab/RL_NBV/scanner/virtual_arabidopsis/arabidopsis002/rec_it.ply")


#rec_it.paint_uniform_color([0,0,1])
#gt.paint_uniform_color([1,0,0])

#open3d.visualization.draw_geometries([gt,rec_it])


t0=time.time()
d_s_octree=chamfer_d(rec_octree.points, gt.points)
print("small", time.time()-t0)

t0=time.time()
d_b_octree=chamfer_d(rec_octree.points, gt_big.points)
print("big",time.time()-t0)

t0=time.time()
d_s_it=chamfer_d(rec_it.points, gt.points)
print("small", time.time()-t0)

t0=time.time()
d_b_it=chamfer_d(rec_it.points, gt_big.points)
print("big",time.time()-t0)
