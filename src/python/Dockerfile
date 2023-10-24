FROM nvidia/cuda:12.1.1-devel-ubuntu22.04

RUN apt-get update && \
    apt-get install -y curl cmake git g++ pkg-config protobuf-compiler libprotobuf-dev libzstd-dev python3 python3-dev pip
RUN curl -sL https://developer.download.nvidia.com/compute/nvcomp/2.6.1/local_installers/nvcomp_2.6.1_x86_64_12.x.tgz | tar xzvf - --directory=/usr/local

RUN git clone -b python https://github.com/keichi/MGARD.git
RUN mkdir MGARD/build && \
    cd MGARD/build && \
    cmake -DBUILD_TESTING=OFF -DMGARD_ENABLE_OPENMP=ON -DMGARD_ENABLE_CUDA=ON -DMGARD_ENABLE_PYTHON=ON -DCMAKE_CUDA_ARCHITECTURES="80;86" .. && \
    make -j $(nproc) && \
    make install && \
    ldconfig

RUN pip3 install numpy 

COPY ./server ./
COPY ./client ./
ENV PYTHONPATH /MGARD/build/lib

