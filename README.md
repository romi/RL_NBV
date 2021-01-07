# RL_NBV
Reinforcement learning for next best view.

The DQN part is inspired from the work of Daryl Perrelta https://github.com/darylperalta/ScanRL, and the space carving is from the work of Timothée Wintz https://github.com/romi/space-carving.

# Requirements without docker

* Python packages

You need to install numpy, imageio, json, open3d, pyopencl, scipy, scikit-image, opencv, networkx, tqdm, bisect, flask, tensorflow, urllib

* Blender
Download the executable for Blender (2.90.0) and change the hard path in scanner/vscanner_launch.sh

##Preparation
Change the hard path in scanner/vscanner_blender.py for data_dir

# Build and run with Docker

You have to prepare the dataset and install Docker in your system to build and run the docker image

## Prepare dataset

Run 
...
wget https://media.romi-project.eu/data/dataset_arabidopsis3d.zip
...

and unzip the folder to ~/data/

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

## Run the docker image and launch the virtual scanner
In the docker directory, you will find also a script named `run.sh`.
By default, a docker container will run with this following port mapping (5000:5000). You can also map a volume with `-v` option.

E.g. `./run.sh -v /home/(username)/data/dataset_arabidopsis3d:/home/(username)/data/dataset_arabidopsis3d`

To show more options, type `./run.sh --help`

In the container, launch the virtual scanner
...
   cd RL_NBV/scanner
   sh vscanner_launch.sh
...

## Connect to the docker image and launch the learning

In another shell, run
...
docker container ls 
...
and get the id of the container where the scanner runs.
Then connect to the same container:
...
docker exec -it container_id /bin/bash
...
and run the learning
...
cd RL_NBV/recons
python3 train.py
...
