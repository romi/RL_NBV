FROM ubuntu:20.04

ARG USER_NAME=scanner
ARG USER_ID=1000
ARG GROUP_NAME=scanner
ARG GROUP_ID=1000

# Add Blender to system's PATH
ENV PATH=$PATH:"/home/${USER_NAME}}/.local/bin"
ENV PATH="/opt/blender:${PATH}"

# Change Shell to 'bash', default is 'sh'
SHELL [ "/bin/bash", "-c" ]

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-dev \
    libxi6 \
    libxrender1 \
    vim \
    wget \
    git \
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

# Create a non-root user and give it rights over "home folder"
RUN addgroup --gid $GROUP_ID $GROUP_NAME && \
    adduser --disabled-password --gecos '' --uid $USER_ID --gid $GROUP_ID $USER_NAME && \
    chown -R ${USER_NAME}: /home/${USER_NAME}

# Download Blender2.91 and move it to /opt/blender
ENV BLENDER_URL=https://download.blender.org/release/Blender2.91/blender-2.91.0-linux64.tar.xz
RUN wget --progress=bar $BLENDER_URL && \
    tar -xf blender-2.91.0-linux64.tar.xz && \
    mv blender-2.91.0-linux64 /opt/blender && \
    rm blender-2.91.0-linux64.tar.xz

# Install python packages needed for RL_NBV
RUN python -m pip install numpy imageio open3d pyopencl scipy scikit-image opencv-python networkx tqdm flask flask_restful tensorflow

# Copy python dependencies in Blender python's site package
RUN cp -r /usr/local/lib/python3.8/dist-packages/flask_restful/ /opt/blender/2.91/python/lib/python3.7/site-packages/
RUN cp -r /usr/local/lib/python3.8/dist-packages/markupsafe/ /opt/blender/2.91/python/lib/python3.7/site-packages/
RUN cp -r /usr/local/lib/python3.8/dist-packages/flask/ /opt/blender/2.91/python/lib/python3.7/site-packages/
RUN cp -r /usr/local/lib/python3.8/dist-packages/itsdangerous/ /opt/blender/2.91/python/lib/python3.7/site-packages/
RUN cp -r /usr/local/lib/python3.8/dist-packages/click/ /opt/blender/2.91/python/lib/python3.7/site-packages/
RUN cp -r /usr/local/lib/python3.8/dist-packages/werkzeug/ /opt/blender/2.91/python/lib/python3.7/site-packages/
RUN cp -r /usr/local/lib/python3.8/dist-packages/jinja2/ /opt/blender/2.91/python/lib/python3.7/site-packages/
RUN cp -r /usr/local/lib/python3.8/dist-packages/imageio/ /opt/blender/2.91/python/lib/python3.7/site-packages/

# Define Working Directory
WORKDIR /home/${USER_NAME}

# Change to the non-root user
USER ${USER_NAME}

# clone the RL_NBV repository
ARG RL_NBV_BRANCH=main
RUN git clone https://github.com/romi/RL_NBV.git && \
    cd RL_NBV/ && \
    git checkout $RL_NBV_BRANCH

EXPOSE 5000
