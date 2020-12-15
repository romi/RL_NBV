# -*- coding: utf-8 -*-
'''
@author: alienor,david
'''

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import requests
from io import BytesIO
import os
from lettucethink.db.fsdb import DB
import json
import urllib.request

''' Before running this code, the virtual scanner should be initiated following 
these instructions: https://github.com/romi/blender_virtual_scanner. The scanner is hosted on localhost:5000'''



class virtual_scan():
    
    def __init__(self, w = None, h = None, f = None, path=None):
        self.R = 55 #radial distance from [x, y] center
        self.N = 72 #number of positions on the circle
        self.z = 50 #camera elevation
        self.rx = 60# camera tilt
        self.ry = 0 #camera twist
        self.w = 1920 #horizontal resolution
        self.h = 1080 #vertical resolution
        self.f = 24 #focal length in mm
        
        self.localhost = "http://localhost:5000/" 
        if (path==None): self.path = '/home/david/data/scans'         
        else: self.path=path
            
        if w is None:
            w = self.w
        if h is None:
            h = self.h
        if f is None:
            f = self.f
        
        #CAMERA API blender
        url_part = 'camera?w=%d&h=%d&f=%d'%(w, h, f)
        contents = urllib.request.urlopen(self.localhost + url_part).read()
        
    def create(self,folder_name):
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
            
    
    def load_im(self,num):
        '''This function loads the arabidopsis mesh. It should be included in the data folder associated to the virtual scanner as a .obj '''
        url_part = "load/arabidopsis_%s"%num
        contents = urllib.request.urlopen(self.localhost + url_part).read()
        return contents
    
    
    def render(self, x, y, z, rx, ry, rz):
        '''This functions calls the virtual scanner and loads an image of the 3D mesh taken from 
        a virtual camera as position x, y, z and orientations rx, ry, rz'''
        url_part = "move?x=%s&y=%s&z=%s&rx=%s&ry=%s&rz=%s"%(x, y, z, rx, ry, rz)
        contents = urllib.request.urlopen(self.localhost + url_part).read()
        response = requests.get(self.localhost + 'render')
        img = Image.open(BytesIO(response.content))
        return img   

    def get_mask(self, x, y, z, rx, ry, rz):
        '''This functions calls the virtual scanner and loads an image of the 3D mesh taken from 
        a virtual camera as position x, y, z and orientations rx, ry, rz'''
        url_part = "move?x=%s&y=%s&z=%s&rx=%s&ry=%s&rz=%s"%(x, y, z, rx, ry, rz)
        contents = urllib.request.urlopen(self.localhost + url_part).read()
        response = requests.get(self.localhost + 'render')
        img = Image.open(BytesIO(response.content))
        res=np.array(img)[:,:,:3]
        mask1=np.all((res==[70,70,70]), axis=-1) 
        mask2=np.all((res==[71,71,71]), axis=-1) 
        mask3=np.all((res==[72,72,72]), axis=-1)
        mask12=np.bitwise_or(mask1,mask2)
        mask_inv=np.bitwise_or(mask12,mask3)
        mask=np.bitwise_not(mask_inv)
        return 255*mask   
    
                       
    def circle_around(self, n, scan_name, N=None, R=None, z = None, rx = None, ry = None):
        if N is None:
            N = self.N
        if R is None:
            R = self.R        
        if z is None:
            z = self.z
        if rx is None:
            rx = self.rx
        if ry is None:
            ry = self.ry

        #Save to database
        self.create(self.path)
        database = DB(self.path)
        scan = database.create_scan(scan_name)
        fileset = scan.get_fileset('images', create = True)
       
        d_theta = 2 * np.pi/N
        c = self.load_im(n)

        for i in range(N):
            x = R * np.cos(i*d_theta) #x pos of camera
            y = R * np.sin(i * d_theta) #y pos of camera   
            rz = d_theta * i * 180/np.pi + 90 #camera pan
            im = self.render(x, y, z, rx, ry, rz) #call blender 
        
            file = fileset.create_file('%03d'%i)
            file.write_image('png',im)
            url_part = 'camera_intrinsics'
            camera_model = json.loads(urllib.request.urlopen(self.localhost + url_part).read().decode('utf-8'))
            url_part = 'camera_extrinsics'
            rt = json.loads(urllib.request.urlopen(self.localhost + url_part).read().decode('utf-8'))
            metadata = {"pose": [x, y, z, rx * np.pi/180, rz * np.pi/180], "camera_model":camera_model, **rt}            
            file.set_metadata(metadata)
        
    def circle_around_masks(self, n, scan_name, N=None, R=None, z = None, rx = None, ry = None):
        self.create(self.path)
        database = DB(self.path)
        scan = database.create_scan(scan_name)
        fileset = scan.get_fileset('images', create = True)
       
        d_theta = 2 * np.pi/N
        
        c = self.load_im(n)
        for i in range(N):
            x = R * np.cos(i*d_theta) #x pos of camera
            y = R * np.sin(i * d_theta) #y pos of camera   
            rz = d_theta * i * 180/np.pi + 90 #camera pan
            im = self.get_mask(x, y, z, rx, ry, rz) #call blender 

            file = fileset.create_file('%03d'%i)
            file.write_image('png',im)
            url_part = 'camera_intrinsics'
            camera_model = json.loads(urllib.request.urlopen(self.localhost + url_part).read().decode('utf-8'))
            url_part = 'camera_extrinsics'
            rt = json.loads(urllib.request.urlopen(self.localhost + url_part).read().decode('utf-8'))
            metadata = {"pose": [x, y, z, rx * np.pi/180, rz * np.pi/180], "camera_model":camera_model, **rt}            
            file.set_metadata(metadata)


    def circle_2cams(self,n, R, phi1, phi2, z0, N, scan_name):
      self.create(self.path)
      database = DB(self.path)
      scan = database.create_scan(scan_name)
      fileset = scan.get_fileset('images', create = True)

      c = self.load_im(n)

      dtheta=2*np.pi/N
      ry=0
      z0=50

      for i in range(N):
         print(i)
         x = R *np.cos(phi1) * np.cos(i*dtheta) #x pos of camera
         y = R *np.cos(phi1) * np.sin(i*dtheta) #y pos of camera   
         z = z0 + R *np.sin(phi1)
         rx = - phi1*180/np.pi  + 90 #camera tilt
         rz = i*dtheta * 180/np.pi + 90 
         im = self.get_mask(x, y, z, rx, ry, rz) #call blender 

         file = fileset.create_file('cam1_%03d'%i)
         file.write_image('png',im)

         url_part = 'camera_intrinsics'
         camera_model = json.loads(urllib.request.urlopen(self.localhost + url_part).read().decode('utf-8'))
         url_part = 'camera_extrinsics'
         rt = json.loads(urllib.request.urlopen(self.localhost + url_part).read().decode('utf-8'))
         metadata = {"pose": [x, y, z, rx * np.pi/180, rz * np.pi/180], "camera_model":camera_model, **rt}            
         file.set_metadata(metadata)

         x = R *np.cos(phi2) * np.cos(i*dtheta) #x pos of camera
         y = R *np.cos(phi2) * np.sin(i*dtheta) #y pos of camera   
         z = z0 + R *np.sin(phi2)
         rx = - phi2*180/np.pi + 90 #camera tilt
         rz = i*dtheta * 180/np.pi + 90 
         im = self.get_mask(x, y, z, rx, ry, rz) #call blender 

         file = fileset.create_file('cam2_%03d'%i)
         file.write_image('png',im)

         url_part = 'camera_intrinsics'
         camera_model = json.loads(urllib.request.urlopen(self.localhost + url_part).read().decode('utf-8'))
         url_part = 'camera_extrinsics'
         rt = json.loads(urllib.request.urlopen(self.localhost + url_part).read().decode('utf-8'))
         metadata = {"pose": [x, y, z, rx * np.pi/180, rz * np.pi/180], "camera_model":camera_model, **rt}            
         file.set_metadata(metadata)
