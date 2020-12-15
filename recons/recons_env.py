import open3d as o3d
import cl
import utils as ut
import numpy as np
from skimage.morphology import binary_dilation
import proc3d
from vscan import virtual_scan
import json
import urllib

class scanner_env():
    def __init__(self, params):
        self.gt=o3d.io.read_point_cloud(params["gt_path"])
        self.vscan = virtual_scan(w=params['scanner']['w'], h=params['scanner']['h'], f=params['scanner']['f'])
        self.vscan.load_im(params["plant_id"])
        self.N_theta = params["traj"]["N_theta"]
        self.N_phi = params["traj"]["N_phi"]
        self.z0 = params["traj"]["z0"]
        self.R = params["traj"]["R"]
        self.n_dilation=params["sc"]["n_dilation"]
        self.voxel_size = params['sc']['voxel_size']
        self.set_sc()
        self.get_intrinsics()
        self.theta = 0
        self.phi = 0
        self.x = 0
        self.y = 0
        self.z = 0
        self.rx = 0
        self.ry = 0
        self.rz = 0
        self.i_theta = 0
        self.i_phi = 0
        self.count_steps = 0
        self.max_steps = 40
        self.d = 5
        
    def set_sc(self):
       bbox = json.loads(urllib.request.urlopen(self.vscan.localhost + 'bounding_box').read().decode('utf-8'))

       x_min, x_max = bbox['x']
       y_min, y_max = bbox['y']
       z_min, z_max = bbox['z']

       nx = int((x_max - x_min) / self.voxel_size) + 1
       ny = int((y_max - y_min) / self.voxel_size) + 1
       nz = int((z_max - z_min) / self.voxel_size) + 1

       self.origin = np.array([x_min, y_min, z_min])
       self.sc = cl.Backprojection([nx, ny, nz], [x_min, y_min, z_min], self.voxel_size)

    def get_intrinsics(self):
       url_part = 'camera_intrinsics'
       camera_model = json.loads(urllib.request.urlopen(self.vscan.localhost + url_part).read().decode('utf-8'))
       self.intrinsics= camera_model['params'][0:4]

    def update_pose(self):   
        self.theta=self.i_theta*2*np.pi/self.N_theta
        self.phi=self.i_phi*.5*np.pi/self.N_phi
        self.x = self.R *np.cos(self.phi) * np.cos(self.theta) #x pos of camera
        self.y = self.R *np.cos(self.phi) * np.sin(self.theta) #y pos of camera   
        self.z = self.z0 + self.R *np.sin(self.phi)
        self.rx = - self.phi*180/np.pi + 90 #camera tilt
        self.rz = self.theta * 180/np.pi + 90 

    def get_reward(self):
       vol = self.sc.values()
       vol = vol.reshape(self.sc.shape)
       pcd=proc3d.vol2pcd_exp(vol, self.origin, self.voxel_size, level_set_value=0)  
       cd=ut.chamfer_d(np.asarray(self.gt.points), np.asarray(pcd.points))
       delta_cd=self.cd-cd
       self.cd=cd

       if cd<.6:
           done=True
           reward=100
       else:
           done=False
           reward=-2+delta_cd
       return reward, done

    def space_carve(self, im):
       mask = ut.get_mask(im)
       rt = json.loads(urllib.request.urlopen(self.vscan.localhost +  'camera_extrinsics').read().decode('utf-8'))
       rot = sum(rt['R'], [])
       tvec = rt['T']
       if self.n_dilation:
          for k in range(self.n_dilation): mask = binary_dilation(mask)    
       self.sc.process_view(self.intrinsics, rot, tvec, mask)
   
    def reset(self):
       del(self.sc)
       self.set_sc()       
       self.count_steps = 0 
       self.cd=5 #Compute the real d
       self.i_theta = np.random.randint(0,self.N_theta)
       self.i_phi = np.random.randint(0,self.N_phi)
       self.update_pose()
       im = self.vscan.render(self.x, self.y, self.z, self.rx, self.ry, self.rz)
       self.space_carve(im)
       fr = ut.get_frame(im)
       self.state = np.array([fr,fr,fr]).transpose(1,2,0)
       return self.state
       
    def increase_theta(self):
        self.i_theta+=1
        if self.i_theta==self.N_theta: self.i_theta=0
        self.update_pose()

    def decrease_theta(self):
        self.i_theta-=1
        if self.i_theta==self.N_theta: self.i_theta=N_theta-1
        self.update_pose()    

    def increase_phi(self):
        self.i_phi+=1
        if self.i_phi==self.N_phi:
            self.i_theta=(self.i_theta+self.N_theta/2)%self.N_theta
            self.i_phi-=1
        self.update_pose()

    def decrease_phi(self):
        self.i_phi-=1
        #if self.i_phi==-1: self.i_phi=0
        if self.i_phi==-1:
            self.i_phi=0
            self.i_theta=(self.i_theta+self.N_theta/2)%self.N_theta
        self.update_pose()            
        
    def change_pose(self, action):
        if action==0: self.increase_theta()
        if action==1: self.decrease_theta()
        if action==2: self.increase_phi()
        if action==3: self.decrease_phi()
   
    def step(self, action):
        self.count_steps+=1
        self.change_pose(action)
        im = self.vscan.render(self.x, self.y, self.z, self.rx, self.ry, self.rz)
        self.space_carve(im)
        fr = ut.get_frame(im)
        self.state=np.array([self.state[:,:,1],self.state[:,:,2], fr]).transpose(1,2,0)
        reward, done = self.get_reward()
        if self.count_steps > self.max_steps:
            done = True
        return self.state, reward, done, {}
