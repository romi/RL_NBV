#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 17 15:58:18 2019

@author: alienor
"""
import argparse
from save_images import virtual_scan


if __name__ == '__main__':
    # Initialize the parser
    parser = argparse.ArgumentParser(
        description='''This code generate N images of a 3D model of arabidopsis number n from the database in 2019/arabidopsis_dataset,
 assuming the blender localhost is active (https://github.com/romi/blender_virtual_scanner for instructions).
 More information in the save_image.py script''')
    
    parser.add_argument(
            'n',
            type=int,
            help = 'Arabidopsis reference number',
            action="store",
            default = 0)
    
    
    parser.add_argument(
            '-N',
            type=int,
            help = 'Number of points on the trajectory',
            action="store",
            default = 72)
    
    
    parser.add_argument(
            '-R',
            type=int,
            help = 'Radial distance from plant center',
            action="store",
            default = 35)
    
    parser.add_argument(
            '-z',
            type=int,
            help = 'Camera elevation',
            action="store",
            default = 60)
    
    parser.add_argument(
            '-rx',
            type=int,
            help = 'Camera tilt in degrees',
            action="store",
            default = 60)
    
    parser.add_argument(
            '-ry',
            type=int,
            help = 'Camera rotation',
            action="store",
            default = 0)
    
    parser.add_argument(
            '-w',
            type=int,
            help = 'Horizontal resolution',
            action="store",
            default = 1902)
    
    parser.add_argument(
            '-l',
            type=int,
            help = 'Vertical resolution',
            action="store",
            default = 1080)
    
    parser.add_argument(
            '-f',
            type=int,
            help = 'Focal length',
            action="store",
            default = 24)
    
    arg = parser.parse_args()
    
    n = arg.n
    N = arg.N
    R = arg.R
    z = arg.z
    rx = arg.rx
    ry = arg.ry
    w = arg.w
    h = arg.l
    f = arg.f
    
    tool = virtual_scan(w=w, h=h, f=f)
    #tool.circle_around(n, N, R, z = z, rx = rx, ry = ry)
    tool.circle_around_masks(n, N, R, z = z, rx = rx, ry = ry)
