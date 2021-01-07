# RL_NBV
Reinforcement learning for next best view.

The DQN part is inspired from the work of Daryl Perrelta https://github.com/darylperalta/ScanRL, and the space carving is from the work of Timothée Wintz https://github.com/romi/space-carving.

##Requirements

* Python packages

You need to install numpy, imageio, json, open3d, pyopencl, scipy, scikit-image, opencv, networkx, tqdm, bisect, flask, tensorflow, urllib

* Blender
Download the executable for Blender (2.90.0) and change the hard path in scanner/vscanner_launch.sh

##Preparation
Change the hard path in scanner/vscanner_blender.py for data_dir

# Build and run with Docker
You have to install Docker in your system to build and run the docker image

## Build the docker image
Clone this repository and run the `build.sh` script in the `docker` directory.

```
    git clone https://github.com/romi/RL_NBV.git
    cd docker/
    ./build.sh
```
This will create by default a docker image `rl_nbv:latest`.

Inside the docker image, a user is created and named as the one currently used by your system.

If you want more build options (specific branches, tags...etc), type `./build.sh --help`.

## Run the docker image
In the docker directory, you will find also a script named `run.sh`.
By default, a docker container will run with this following port mapping (5000:5000). You can also map a volume with `-v` option.

E.g. `./run.sh -v /abs/host/dir:/abs/container/dir`

To show more options, type `./run.sh --help`
