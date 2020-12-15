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
    
    def __init__(self, w = None, h = None, f = None):
        self.R = 35 #radial distance from [x, y] center
        self.N = 72 #number of positions on the circle
        self.z = 50 #camera elevation
        self.rx = 60# camera tilt
        self.ry = 0 #camera twist
        self.w = 1920 #horizontal resolution
        self.h = 1080 #vertical resolution
        self.f = 24 #focal length in mm
        
        self.localhost = "http://localhost:5000/" 
        
        
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
    
    def get_label(self, x, y, z, rx, ry, rz):
        '''This functions calls the virtual scanner and loads an image of the 3D mesh taken from 
        a virtual camera as position x, y, z and orientations rx, ry, rz, for each 
        class, and overlaps the labels using binary encoding.'''
        img = np.zeros((self.h, self.w))
        
        #rows = 1
        #columns = 5
        #fig=plt.figure(figsize = (10, 1))
        #titles = ['Flowers', 'Peduncle','Stem','Leaves','Fruits']
        
        for i, label in enumerate([0, 1, 2, 7, 8]):
            #fig.add_subplot(rows, columns, i+1)
            #plt.axis('off')
            #plt.grid(False)            
            #print(i, label)
            url_part = "move?x=%s&y=%s&z=%s&rx=%s&ry=%s&rz=%s"%(x, y, z, rx, ry, rz)
            contents = urllib.request.urlopen(self.localhost + url_part).read()
            url_part = 'render?mat=Color_%d'%label
            response = requests.get(self.localhost + url_part)
            collect_image = np.array(Image.open(BytesIO(response.content)))[:,:,0]
            print(i, label, collect_image.shape)
            collect_image[collect_image != 64] = 2**i  #Binary encoding to describe
            #plt.imshow(collect_image, cmap = 'gray')
            #plt.title(titles[i])

            #the possibiility of multiclass for 1 pixel
            collect_image[collect_image == 64] = 0

            img += collect_image
        #plt.show()
        return img                       
     
    def read_label(self, im):
        '''This function reads the binary-encoded label of the input image and
        returns the one hot encoded label. 6 classes: 5 plan organs and ground'''
        a, b = im.shape
        label_image = np.zeros((6, a, b))
        label_image[0][im == 0] = 1
        for i in range(1,6): #[binary reading]
            label_image[i] = im%2
            im = im//2
        
        return label_image
                
                       
                       
    def circle_around(self, n, N=None, R=None, z = None, rx = None, ry = None):
        
        '''This function takes a virtual scan of the 3D mesh by truning around.
        Inputs : N [int] : number of points on the circular trajectory
                R [float]: Radial distance from the [x, y] origin
                n [int]: plant number in the database
                z [float]: elevation of the camera
                rx [float]: horizontal inclination of the camera
                ry  [float]: in-plane tilt of the camera
                
        Outputs: saves scanned images in the folder virtual_arabidopsis/arabidopsisn/images and collects the metadata
                plots a figure with the trajectory and relevant information, saves it in the same folder'''
                
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
        self.create('virtual_arabidopsis')
        database = DB('virtual_arabidopsis')
        scan = database.create_scan('arabidopsis%03d'%n)
        fileset = scan.get_fileset('images', create = True)
       

        scale_arrow = 10
        d_theta = 2 * np.pi/N
        
        fig, ax = plt.subplots(figsize = (8,8))
        
        #LOAD IMAGE IN BLENDER
        c = self.load_im(n)
        
        #TRAJECTORY
        for i in range(N):
            
            #MOVE CAMERA
            x = R * np.cos(i*d_theta) #x pos of camera
            y = R * np.sin(i * d_theta) #y pos of camera   
            rz = d_theta * i * 180/np.pi + 90 #camera pan
            im = self.render(x, y, z, rx, ry, rz) #call blender 
            print(x,y,z,rx,ry,rz)

            file = fileset.create_file('arabidopsis%03d_image%03d'%(n,i))
            file.write_image('png',im)
            url_part = 'camera_intrinsics'
            camera_model = json.loads(urllib.request.urlopen(self.localhost + url_part).read().decode('utf-8'))
            url_part = 'camera_extrinsics'
            rt = json.loads(urllib.request.urlopen(self.localhost + url_part).read().decode('utf-8'))
            metadata = {"pose": [x, y, z, rx * np.pi/180, rz * np.pi/180], "camera_model":camera_model, **rt}            
            file.set_metadata(metadata)
            
            #PLOT THE TRAJECTORY
            plt.scatter(x, y)
            rz0 = d_theta * i + np.pi
            plt.quiver(x, y, np.cos(rz0), np.sin(rz0), scale = scale_arrow, width = 0.004)
            ax.annotate(i, (x, y), xytext = (x + 4*np.cos(rz0 + np.pi)-1, y + 4*np.sin(rz0 + np.pi)-1))
        
        #PLOT THE TRAJECTORY    
        plt.title('Trajectory of the camera')
        plt.xlabel('y')
        plt.ylabel('x')  
        plt.xlim(-R-10, R + 10)
        plt.ylim(-R-10, R + 10)
        
        textstr = '\n'.join((
        r'$%d$ positions' %N,
        r'$z = %d$ cm' %z,
        r'$R = %d$ cm' %R))
    
        props = dict(boxstyle='round', alpha=0.5)
    
        # place a text box in upper left in axes coords
        ax.text(0.43, 0.57, textstr, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=props)
                
        plt.savefig("virtual_arabidopsis/arabidopsis%03d/trajectory.png"%n,
                            bbox_inches='tight', frameon = False)

    def circle_around_masks(self, n, N=None, R=None, z = None, rx = None, ry = None):
        
        '''This function takes a virtual scan of the 3D mesh by truning around.
        Inputs : N [int] : number of points on the circular trajectory
                R [float]: Radial distance from the [x, y] origin
                n [int]: plant number in the database
                z [float]: elevation of the camera
                rx [float]: horizontal inclination of the camera
                ry  [float]: in-plane tilt of the camera
                
        Outputs: saves scanned images in the folder virtual_arabidopsis/arabidopsisn/images and collects the metadata
                plots a figure with the trajectory and relevant information, saves it in the same folder'''
                
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
        self.create('virtual_arabidopsis')
        database = DB('virtual_arabidopsis')
        scan = database.create_scan('arabidopsis%03d'%n)
        fileset = scan.get_fileset('images', create = True)
       

        scale_arrow = 10
        d_theta = 2 * np.pi/N
        
        fig, ax = plt.subplots(figsize = (8,8))
        
        #LOAD IMAGE IN BLENDER
        c = self.load_im(n)
        
        #TRAJECTORY
        for i in range(N):
            
            #MOVE CAMERA
            x = R * np.cos(i*d_theta) #x pos of camera
            y = R * np.sin(i * d_theta) #y pos of camera   
            rz = d_theta * i * 180/np.pi + 90 #camera pan
            im = self.get_mask(x, y, z, rx, ry, rz) #call blender 

            file = fileset.create_file('arabidopsis%03d_image%03d'%(n,i))
            file.write_image('png',im)
            url_part = 'camera_intrinsics'
            camera_model = json.loads(urllib.request.urlopen(self.localhost + url_part).read().decode('utf-8'))
            url_part = 'camera_extrinsics'
            rt = json.loads(urllib.request.urlopen(self.localhost + url_part).read().decode('utf-8'))
            metadata = {"pose": [x, y, z, rx * np.pi/180, rz * np.pi/180], "camera_model":camera_model, **rt}            
            file.set_metadata(metadata)
            
            #PLOT THE TRAJECTORY
            plt.scatter(x, y)
            rz0 = d_theta * i + np.pi
            plt.quiver(x, y, np.cos(rz0), np.sin(rz0), scale = scale_arrow, width = 0.004)
            ax.annotate(i, (x, y), xytext = (x + 4*np.cos(rz0 + np.pi)-1, y + 4*np.sin(rz0 + np.pi)-1))
        
        #PLOT THE TRAJECTORY    
        plt.title('Trajectory of the camera')
        plt.xlabel('y')
        plt.ylabel('x')  
        plt.xlim(-R-10, R + 10)
        plt.ylim(-R-10, R + 10)
        
        textstr = '\n'.join((
        r'$%d$ positions' %N,
        r'$z = %d$ cm' %z,
        r'$R = %d$ cm' %R))
    
        props = dict(boxstyle='round', alpha=0.5)
    
        # place a text box in upper left in axes coords
        ax.text(0.43, 0.57, textstr, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=props)
                
        plt.savefig("virtual_arabidopsis/arabidopsis%03d/trajectory.png"%n,
                            bbox_inches='tight', frameon = False)


    def make_labels(self, n, N=None, R=None, z = None, rx = None, ry = None):
        
        '''This function takes a virtual scan of the 3D mesh by truning around.
        Inputs : N [int] : number of points on the circular trajectory
                R [float]: Radial distance from the [x, y] origin
                n [int]: plant number in the database
                z [float]: elevation of the camera
                rx [float]: horizontal inclination of the camera
                ry  [float]: in-plane tilt of the camera
                
        Outputs: saves scanned images in the folder virtual_arabidopsis/arabidopsisn/images and collects the metadata
                plots a figure with the trajectory and relevant information, saves it in the same folder'''
                
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
        self.create('segmentation_arabidopsis')
        database = DB('segmentation_arabidopsis')
        scan = database.create_scan('arabidopsis%03d'%n)
        fileset = scan.get_fileset('images', create = True)
       
        d_theta = 2 * np.pi/N
                
        #LOAD IMAGE IN BLENDERprod
        c = self.load_im(n)
        
        #TRAJECTORY
        for i in range(N):
            
            #MOVE CAMERA
            x = R * np.cos(i*d_theta) #x pos of camera
            y = R * np.sin(i * d_theta) #y pos of camera   prod
            rz = d_theta * i * 180/np.pi + 90 #camera pan
            im = self.get_label(x, y, z, rx, ry, rz) #call blender 
            im = im.astype(np.uint8)
            print(np.max(im))
            #SAVE IMAGE
            file = fileset.create_file('arabidopsis%03d_image%03d'%(n,i))
            file.write_image('png',im)
            metadata = {"pose": [x, y, z, rx * np.pi/180, rz * np.pi/180]}            
            file.set_metadata(metadata)
            
            
    def image_and_label(self, n, N=None, R=None, z = None, rx = None, ry = None):
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
        self.create('segmentation_arabidopsis')
        database = DB('segmentation_arabidopsis')
        scan = database.create_scan('arabidopsis%03d'%n)
        file_images = scan.get_fileset('images', create = True)
        file_labels = scan.get_fileset('labels', create = True)

        
        d_theta = 2 * np.pi/N
                
        #LOAD IMAGE IN BLENDER
        c = self.load_im(n)
        
        #TRAJECTORY
        for i in range(N):
            
            #MOVE CAMERA
            x = R * np.cos(i*d_theta) #x pos of camera
            y = R * np.sin(i * d_theta) #y pos of camera   
            rz = d_theta * i * 180/np.pi + 90 #camera pan
            
            im = self.render(x, y, z, rx, ry, rz) #call blender 
            file = file_images.create_file('arabidopsis%03d_image%03d'%(n,i))
            file.write_image('png',im)
            
            im = self.get_label(x, y, z, rx, ry, rz) #call blender 
            im = im.astype(np.uint8)
            #SAVE IMAGE
            file = file_labels.create_file('arabidopsis%03d_image%03d'%(n,i))
            file.write_image('png',im)
            metadata = {"pose": [x, y, z, rx * np.pi/180, rz * np.pi/180]}            
            file.set_metadata(metadata)
        
            