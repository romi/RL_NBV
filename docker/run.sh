#!/bin/bash

###############################################################################
# Example usages:
###############################################################################
# 1. Run starts an interactive shell:
# $ ./run.sh -t latest -v /abs/host/dir:/abs/container/dir

user=$USER
vtag="latest"
mount_option=""
port_option="-p 5000:5000"

usage() {
  echo "USAGE:"
  echo "  ./run.sh [OPTIONS]
    "

  echo "DESCRIPTION:"
  echo "  Run 'rl_nbv:<vtag>' container.
    "

  echo "OPTIONS:"
  echo "  -t, --tag
    Docker image tag to use, default to '$vtag'.
    "
  echo "  -v, --volume
    Volume mapping for docker, e.g. '/abs/host/dir:/abs/container/dir'. Multiple use is allowed.
  "
  echo "  -p
    Port mapping for docker, e.g. '5000:5000'. Multiple use is allowed.
  "
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
  -u | --user)
    shift
    user=$1
    ;;
  -v | --volume)
    shift
    if [ "$mount_option" == "" ]
    then
      mount_option="-v $1"
    else
      mount_option="$mount_option -v $1"  # append
    fi
    ;;
  -p)
    shift
    if [ "port_option" == "" ]
    then
      port_option="-p $1"
    else
      port_option="$port_option -p $1"  # append
    fi
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

# Start the docker image in interative mode:
docker run -it --gpus all $mount_option $port_option rl_nbv:$vtag bash
