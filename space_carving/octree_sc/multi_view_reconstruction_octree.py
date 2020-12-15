# -*- python -*-
#
#       Copyright INRIA - CIRAD - INRA
#
#       Distributed under the Cecill-C License.
#       See accompanying file LICENSE.txt or copy at
#           http://www.cecill.info/licences/Licence_CeCILL-C_V1-en.html
#
# ==============================================================================
from __future__ import division, print_function, absolute_import

import collections
import math
import numpy
import open3d as o3d 

from voxelOctree import VoxelOctree
# ==============================================================================
# Function for no kep

def get_voxels_corners(voxels_position, voxels_size):
    """ According the voxels position and their size, return a numpy array
    containing for each input voxels the position of the 8 corners.
    Parameters
    ----------
    voxels_position : numpy.ndarray
        Center position of the voxels
    voxels_size : float
        Diameter size of the voxels
    Returns
    -------
    a : numpy.array
    """

    r = voxels_size / 2.0

    x_minus = voxels_position[0] - r
    x_plus = voxels_position[0] + r
    y_minus = voxels_position[ 1] - r
    y_plus = voxels_position[ 1] + r
    z_minus = voxels_position[ 2] - r
    z_plus = voxels_position[ 2] + r

    a1 = numpy.column_stack((x_minus, y_minus, z_minus))
    a2 = numpy.column_stack((x_plus, y_minus, z_minus))
    a3 = numpy.column_stack((x_minus, y_plus, z_minus))
    a4 = numpy.column_stack((x_minus, y_minus, z_plus))
    a5 = numpy.column_stack((x_plus, y_plus, z_minus))
    a6 = numpy.column_stack((x_plus, y_minus, z_plus))
    a7 = numpy.column_stack((x_minus, y_plus, z_plus))
    a8 = numpy.column_stack((x_plus, y_plus, z_plus))

    a = numpy.concatenate((a1, a2, a3, a4, a5, a6, a7, a8), axis=1)
    a = numpy.reshape(a, (a.shape[0] * 8, 3))

    return a


def get_bounding_box_voxel_projected(voxels_position,
                                     voxels_size,
                                     projection):

    """ Compute the bounding box value according the radius, angle and
    calibration parameters of point_3d projection
    Parameters
    ----------
    voxels_position : numpy.ndarray
        Center position of voxel
    voxels_size : float
        Size of side geometry of voxel
    projection : function ((x, y, z)) -> (x, y)
        Function of projection who take 1 argument (tuple of position (x, y, z))
        and return this position 2D (x, y)
    Returns
    -------
    bbox : numpy.ndarray
        [[x_min, x_max, y_min, y_max], ...]
        Containing min and max value of point_3d projection in x and y axes.
    """

    voxels_corners = get_voxels_corners(voxels_position, voxels_size)

    pt = numpy.array([projection(voxels_corners[i]) for i in range(8)])

    #pt = numpy.reshape(pt, (pt.shape[0] // 8, 8, 2))
    bbox = numpy.hstack((pt.min(axis=0), pt.max(axis=0)))

    return bbox

def voxel_is_visible_in_image(voxel_center,
                              voxel_size,
                              image,
                              projection,
                              inclusive):
    """
    Return True or False if the voxel projected on image with the function
    projection (projection) have positive value on image.

    **Algorithm**

    1. Project the center voxel position on image if the position projected
       (x, y) is positive on image return True

    |

    2. Project the bounding box of voxel in image, if one of the 4 corners
       position of the bounding box projected have positive value on image
       return True

    |

    3. Check if one pixel containing in the bounding box projected on image
       have positive value, if yes return True else return False

    Parameters
    ----------
    voxel_center : (x, y, z)
        Center position of voxel

    voxel_size : float
        Size of side geometry of voxel

    image: numpy.ndarray
        binary image

    projection : function ((x, y, z)) -> (x, y)
        Function of projection who take 1 argument (tuple of position (x, y, z))
         and return this position 2D (x, y)

    Returns
    -------
    out : bool
        True if voxel have a positive correspondence on image otherwise return
        False
    """

    height_image, length_image = image.shape
    """
    x, y = projection(voxel_center)

    if (0 <= x < length_image and
        0 <= y < height_image and
            image[int(y), int(x)] > 0):
        return True
    """
    # ==========================================================================

    x_min, y_min, x_max, y_max = get_bounding_box_voxel_projected(
        voxel_center, voxel_size, projection)

    if (x_max < 0 or x_min >= length_image or
            y_max < 0 or y_min >= height_image):
        return inclusive

    # if ((not (0 <= x_min < length_image or 0 <= x_max < length_image)) or
    #         (not (0 <= y_min < height_image or 0 <= y_max < height_image))):
    #     return inclusive

    x_min = int(min(max(math.floor(x_min), 0), length_image - 1))
    x_max = int(min(max(math.ceil(x_max), 0), length_image - 1))
    y_min = int(min(max(math.floor(y_min), 0), height_image - 1))
    y_max = int(min(max(math.ceil(y_max), 0), height_image - 1))

    if (image[y_min, x_min] > 0 or
        image[y_max, x_min] > 0 or
        image[y_min, x_max] > 0 or
            image[y_max, x_max] > 0):
        return True
    # ==========================================================================

    if numpy.any(image[y_min:y_max + 1, x_min:x_max + 1] > 0):
        return True
    return False


def _keep_visible(voxels_node,
                  image_views,
                  error_tolerance=0):
    i=0
    kept = collections.deque()
    for voxel_node in voxels_node:
        i+=1
        if (i/100==0): print("checking voxel: %s / %s"%(i,len(voxels_node))) 

        voxel_position = voxel_node.position
        voxel_size = voxel_node.size
        negative_weight = 0

        for image_view in image_views:
            if not voxel_is_visible_in_image(
                    voxel_position,
                    voxel_size,
                    image_view[0],
                    image_view[1], False):
                negative_weight += 1
                if negative_weight > error_tolerance:
                    break

        if negative_weight <= error_tolerance:
            kept.append(voxel_node)

        else:
            voxel_node.data = False

    return kept


# ==============================================================================

def reconstruction_3d_octree(image_views,
                             voxels_size=4,
                             error_tolerance=0,
                             voxel_center_origin=(0.0, 0.0, 0.0),
                             world_size=4096,
                             verbose=False):
    """
    Construct a list of voxel represented object with positive value on binary
    image in images of images_projections.

    Parameters
    ----------
    images_projections : [(image, projection), ...]
        List of tuple (image, projection) where image is a binary image
        (numpy.ndarray) and function projection (function (x, y, z) -> (x, y))
        who take (x, y, z) position on return (x, y) position according space
        representation of this image

    voxels_size : float, optional
        Size of side geometry of voxel that each voxel will have

    error_tolerance : int, optional


    voxel_center_origin : (x, y, z), optional
        Center position of the first original voxel, who will be split.

    world_size: int, optional
        Minimum size that the origin voxel size must include at beginning

    voxel_centers : collections.deque, optional
        List of first original voxel who will be split. If None, a list is
        create with the voxel_center_origin value.

    verbose : bool, optional
        If True, print for each iteration of split, number of voxel before and
        after projection on images

    Returns
    -------
    out : collections.deque
        List of visible voxel projected on each image according
        the error_tolerance
    """

    if len(image_views) == 0:
        raise ValueError("Len images view have not length")

    voxel_octree = VoxelOctree.from_position(
        voxel_center_origin, world_size, True)

    leaf_nodes = collections.deque()
    leaf_nodes.append(voxel_octree.root)

    nb_iteration = 0
    while voxels_size < world_size:
        voxels_size *= 2.0
        nb_iteration += 1
    

    for i in range(nb_iteration):

        tmp = collections.deque()
        for leaf in leaf_nodes:
            tmp.extend(leaf.creates_sons())
        leaf_nodes = tmp

        if verbose is True:
            print('Iteration', i + 1, '/', nb_iteration, end="")
            print(' : ', len(leaf_nodes), end="")

        leaf_nodes = _keep_visible(leaf_nodes,
                                   image_views,
                                   error_tolerance)

        # Gain time is not enough for keeping that
        # if i + 1 < nb_iteration:
        #     leaf_nodes = remove_surrounded_fully_visible(leaf_nodes,
        #                                                  images_projections,
        #                                                  error_tolerance)

        if verbose is True:
            print(' - ', len(leaf_nodes))
            points=[]
            for l in leaf_nodes:
               points.append(list(l.position))

            #pcl = o3d.geometry.PointCloud()
            #pcl.points=o3d.utility.Vector3dVector(points)
            #o3d.io.write_point_cloud("pc_level_%s.ply"%i,pcl) 


    return voxel_octree, leaf_nodes