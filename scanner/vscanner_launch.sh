#!/bin/bash
export PYTHONPATH=/usr/lib/python3.8
# Launch blender python script (blender application must be defined in your PATH system)
/opt/blender/blender -E CYCLES -b -noaudio -P vscanner_blender.py
