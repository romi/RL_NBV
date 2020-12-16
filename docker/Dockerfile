FROM ubuntu:20.04

# Change Shell to 'bash', default is 'sh'
SHELL [ "/bin/bash", "-c" ]

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-dev \
    libxi6 \
    wget \
    xz-utils \
    python3-pip \
    gcc python3-dev \
    ocl-icd-libopencl1 opencl-headers clinfo && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.8 10 && \
    ln -s /usr/lib/x86_64-linux-gnu/libOpenCL.so.1 /usr/lib/libOpenCL.so && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /etc/OpenCL/vendors && \
    echo "libnvidia-opencl.so.1" > /etc/OpenCL/vendors/nvidia.icd

ENV NVIDIA_VISIBLE_DEVICES all
ENV NVIDIA_DRIVER_CAPABILITIES compute,utility

WORKDIR /home/wd

ENV BLENDER_URL=https://download.blender.org/release/Blender2.91/blender-2.91.0-linux64.tar.xz
RUN wget --progress=bar $BLENDER_URL && \
    tar -xf blender-2.91.0-linux64.tar.xz && \
    mv blender-2.91.0-linux64 /opt/blender && \
    rm blender-2.91.0-linux64.tar.xz

ENV LD_LIBRARY_PATH "/opt/blender/lib"

# Install python packages
RUN python -m pip install numpy imageio open3d pyopencl scipy scikit-image opencv-python networkx tqdm flask tensorflow

RUN git clone https://github.com/romi/RL_NBV.git
#    #cd RL_NBV/scanner/ && \
#    # ./vscanner_launch.sh
    
# CMD [ "/bin/bash", "-c" ]
