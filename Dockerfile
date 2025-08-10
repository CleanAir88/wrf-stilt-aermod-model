FROM python:3.10.12-bookworm

WORKDIR /src

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    BASE_PATH=/src \
    STILT_WD=/src/stilt \
    TZ=UTC \
    LC_ALL=en_US.UTF-8 \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US.UTF-8

RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-backports main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian bullseye main" >> /etc/apt/sources.list && \
    echo "deb https://security.debian.org/debian-security bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list

RUN apt update && apt install -y --no-install-recommends \
        build-essential \
        git \
        libhdf5-dev \
        libhdf5-serial-dev \
        libnetcdf-dev \
        libssl-dev \
        locales \
        netcdf-bin \
        procps \
        r-base \
        r-base-dev \
        gdal-bin \
        libgdal-dev \
        libproj-dev \
        unzip \
        wget \
        vim \
        redis-server \
    && locale-gen en_US.UTF-8 \
    && update-locale \
    && rm -rf /var/lib/apt/lists/*


COPY scripts/ /src/scripts/
COPY build/ /src/

RUN chmod +x scripts/*.sh && bash scripts/install.sh

# copy server code and install dependencies
WORKDIR /src/server
COPY server .
RUN pip install --upgrade pip && \
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple . && \
    pip install wrf-python/

EXPOSE 8000 5555
CMD ["/src/scripts/start_server.sh"]
