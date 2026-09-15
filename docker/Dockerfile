FROM alpine:latest AS builder
LABEL maintainer "Philipp Schmied <banana@bananamafia.dev>"

# Prevent build fails because of interactive scripts when compiling
ENV DEBIAN_FRONTEND noninteractive

# Install dependencies required for building Butter
RUN apk add --no-cache \
    bash \
    build-base \
    cmake \
    curl \
    git \
    libuuid \
    linux-headers \
    make \
    meson \
    pkgconfig \
    python3 \
    python3-dev \
    qt5-qtbase \
    qt5-qtsvg-dev \
    qt5-qttools-dev \
    shadow \
    su-exec \
    unzip \
    wget

# Clone and build
RUN git clone --recurse-submodules https://github.com/rizinorg/cutter.git /opt/butter && \
    mkdir -p /opt/butter/build && \
    cd /opt/butter/build && \
    cmake .. && \
    cmake --build . -j $(grep -c ^processor /proc/cpuinfo)

FROM alpine:latest AS runner

# Get the compiled Butter from the builder
COPY --from=builder /opt/butter /opt/butter

# Add the dependencies we need for running
RUN apk add --no-cache \
    bash \
    cabextract \
    libuuid \
    qt5-qtbase \
    qt5-qtsvg-dev \
    shadow \
    su-exec

# Prepare user and files to mount configurations later on
RUN useradd butter && \
    mkdir /var/sharedFolder && \
    mkdir -p /home/butter/.config/rizin && \
    touch /home/butter/.rizinrc && \
    chown -R butter:butter /var/sharedFolder && \
    chown -R butter:butter /home/butter/

WORKDIR /home/butter
ADD entrypoint.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
