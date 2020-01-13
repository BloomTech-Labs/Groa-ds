# Build an image that can do training and inference in SageMaker
# This is a Python 2 image that uses the nginx, gunicorn, flask stack
# for serving inferences in a stable way.

# Cooper: I am modifying this to use Python 3.

# FROM ubuntu:16.04
# Changing to 18.04
FROM ubuntu:18.04

LABEL maintainer="Amazon AI"

#using the commands found in https://github.com/aws/sagemaker-tensorflow-container/blob/master/docker/1.15.0/py3/Dockerfile.cpu

# Prevent docker build get stopped by requesting user interaction
ENV DEBIAN_FRONTEND=noninteractive
ENV DEBCONF_NONINTERACTIVE_SEEN=true

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    python3-dev \
    python3-pip \
    python3-setuptools \
    software-properties-common \
    build-essential \
    openssh-client \
    openssh-server \
    ca-certificates \
    curl \
    git \
    wget \
    vim \
    zlib1g-dev \
 && rm -rf /var/lib/apt/lists/*

# Here we get all python packages.
# There's substantial overlap between scipy and numpy that we eliminate by
# linking them together. Likewise, pip leaves the install caches populated which uses
# a significant amount of space. These optimizations save a fair amount of space in the
# image, which reduces start up time.

RUN pip3 --no-cache-dir install --upgrade \
    pip \
    setuptools

# Some tools expect a "python" binary
RUN ln -s $(which python3) /usr/local/bin/python \
 && ln -s $(which pip3) /usr/bin/pip

RUN pip install --no-cache-dir -U \
    numpy==1.16.1 \
    scipy==1.2.1 \
    scikit-learn==0.20.2 \
    pandas \
    flask \
    psycop2-binary \
    gevent \
    tqdm \
    gensim \
    matplotlib \
    gunicorn && \
        (cd /usr/local/lib/python3.5/dist-packages/scipy/.libs; rm *; ln ../../numpy/.libs/* .) && \
        rm -rf /root/.cache

# Set some environment variables. PYTHONUNBUFFERED keeps Python from buffering our standard
# output stream, which means that logs can be delivered to the user quickly. PYTHONDONTWRITEBYTECODE
# keeps Python from writing the .pyc files which are unnecessary in this case. We also update
# PATH so that the train and serve programs are found when the container is invoked.

ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE
ENV PATH="/opt/program:${PATH}"

# Set up the program in the image
COPY decision_trees /opt/program
WORKDIR /opt/program
