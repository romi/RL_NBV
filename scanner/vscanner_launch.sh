#!/bin/bash
export PYTHONPATH=/usr/lib/python3.8
/opt/blender/blender -E CYCLES -b -noaudio -P vscanner_blender.py
