"""
romiscan.cl
___________
This module contains all OpenCL accelerated functions.
"""
import os
import numpy as np
import pyopencl as cl
import logging

from proc3d import point2index
from romidata import io
from skimage.morphology import binary_dilation
from scipy.ndimage import gaussian_filter


ctx = cl.create_some_context()
queue = cl.CommandQueue(ctx)
mf = cl.mem_flags

prg_dir = os.path.join(os.path.dirname(__file__), 'kernels')

