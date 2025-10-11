#! /bin/bash

set -euxo pipefail

image=debian:12

case "$ARCH" in
    x86_64)
        platform=linux/amd64
        ;;
    aarch64)
        platform=linux/arm64
        ;;
    *)
        echo "unknown architecture: $ARCH"
        exit 2
        ;;
esac


repo_root="$(readlink -f "$(dirname "${BASH_SOURCE[0]}")"/..)"

# run the build with the current user to
#   a) make sure root is not required for builds
#   b) allow the build scripts to "mv" the binaries into the /out directory
uid="$(id -u)"

# make sure Docker image is up to date
#docker pull "$image"

docker run \
    --platform "$platform" \
    --rm \
    -i \
    -e ARCH \
    -e OUT_UID="$uid" \
    -v "$repo_root":/source \
    -v "$PWD":/out \
    -w /out \
    "$image" \
    sh <<\EOF

set -eux

apt update
# prevent tzdata from asking timezone during install
DEBIAN_FRONTEND=noninteractive TZ="Asia/Kolkata" apt install -y tzdata
apt install -y wget file python3 python3-pip python3-pyqt5 pyqt5-dev-tools
apt install -y --no-install-recommends python3-pyqt5.qtwebkit gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-alsa gstreamer1.0-libav qt5ct

pip3 install pyinstaller --break-system-packages

wget -q "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-${ARCH}.AppImage"
wget -q "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-${ARCH}.AppImage"


chmod 755 *.AppImage
mv appimagetool*AppImage /usr/bin/appimagetool
mv linuxdeploy*AppImage /usr/bin/linuxdeploy

bash -eux /source/AppImage/appimage_gen.sh

chown "$OUT_UID" Quartz_Browser*.AppImage

EOF
