#!/bin/bash
export PYTHONPATH=/usr/lib/python3.8
#/opt/blender/blender -b --python-use-system-env -P vscanner_blender.py
/opt/blender/blender -b -noaudio -P vscanner_blender.py
