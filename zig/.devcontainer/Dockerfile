FROM gwmcassella/devcontainer-base:latest

ENV VERSION=0.15.2
ENV FILE=zig-x86_64-linux-${VERSION}.tar.xz
RUN curl https://ziglang.org/download/${VERSION}/${FILE} -L --output ${FILE} && \
    tar -xf ${FILE} && \
    rm ${FILE}
