# A stock Ubuntu desktop (the package set of the official desktop ISO) plus
# the screenshot tools, for checking that the .deb installs offline.
ARG UBUNTU=24.04
FROM ubuntu:${UBUNTU}
ARG MANIFEST_URL
ARG TRIAL=0
ENV DEBIAN_FRONTEND=noninteractive
COPY stock-desktop.sh /stock-desktop.sh
RUN bash /stock-desktop.sh "$MANIFEST_URL" "$TRIAL"
