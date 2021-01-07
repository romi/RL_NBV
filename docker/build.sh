#!/bin/bash

###############################################################################
# Example usages:
###############################################################################
# 1. Default build options will create `rl_nbv:latest`:
# $ ./build.sh
#
# 2. Build image with 'debug' tag & another 'RL_NBV' branch 'Feat/Some_great_feature' options:
# $ ./build.sh -t debug -b Feat/Some_great_feature

vtag="latest"
rl_nbv_branch='main'
user=$USER
uid=$(id -u)
group=$(id -g -n)
gid=$(id -g)
docker_opts=""

usage() {
    echo "USAGE:"
    echo " ./build.sh [OPTIONS]
    "

    echo "DESCRIPTION:"
    echo " Build a docker image named 'rl_nbv' using Dockerfile in the same location.
    "

    echo "OPTIONS:"
    echo "  -t, --tag
        Docker image tag to use, default to '$vtag'.
        "
    echo "  -u, --user
        User name to create inside docker image, default to '$user'.
        "
    echo "  --uid
        User id to use with 'user' inside docker image, default to '$uid'.
        "
    echo "  -g, --group
        Group name to create inside docker image, default to 'group'.
        "
    echo "  --gid
        Group id to use with 'user' inside docker image, default to '$gid'.
        "
    echo "  -b, --rl_nbv_branch
        Git branch to use for cloning 'rl_nbv' inside docker image, default to '$rl_nbv_branch'.
        "
    # Docker options:
    echo "  --no-cache
        Do not use cache when building the image, (re)start from scratch.
        "
    echo "  --pull
        Always attempt to pull a newer version of the parent image.
        "
    # General options:
    echo "  -h, --help
        Output a usage message and exit.
        "    
}

while [ "$1" != "" ]; do
  case $1 in
  -t | --tag)
    shift
    vtag=$1
    ;;
  -b | --rl_nbv_branch)
    shift
    rl_nbv_branch=$1
    ;;
  --no-cache)
    shift
    docker_opts="$docker_opts --no-cache"
    ;;
  --pull)
    shift
    docker_opts="$docker_opts --pull"
    ;;
  -h | --help)
    usage
    exit
    ;;
  *)
    usage
    exit 1
    ;;
  esac
  shift
done

# Start the docker image build:
docker build -t rl_nbv:$vtag $docker_opts \
  --build-arg RL_NBV_BRANCH=$rl_nbv_branch \
  --build-arg USER_NAME=$user \
  --build-arg USER_ID=$uid \
  --build-arg GROUP_NAME=$group \
  --build-arg GROUP_ID=$gid \
  .
