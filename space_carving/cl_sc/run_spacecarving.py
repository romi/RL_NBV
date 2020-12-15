import numpy as np
import imageio
import cl
import open3d
import proc3d

folder="/home/david/RL_NBV/scanner/virtual_arabidopsis/arabidopsis002"


voxel_size = .4

x_min, x_max = -30,30
y_min, y_max = -30,30
z_min, z_max = 0,100

nx = int((x_max - x_min) / voxel_size) + 1
ny = int((y_max - y_min) / voxel_size) + 1
nz = int((z_max - z_min) / voxel_size) + 1

origin = np.array([x_min, y_min, z_min])

sc = cl.Backprojection(
     [nx, ny, nz], [x_min, y_min, z_min], voxel_size)

vol = sc.process_fileset(folder)

#b = imageio.volwrite(imageio.RETURN_BYTES, vol, format="npz")
#with open("res.npz", "wb") as f: f.write(b)

pcd=proc3d.vol2pcd(vol, origin, voxel_size, level_set_value=0)
open3d.io.write_point_cloud(folder+"/pcd.ply", pcd)
