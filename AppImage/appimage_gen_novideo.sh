#!/bin/bash

check_dep()
{
  DEP=$1
  if [ -z $(which $DEP) ] ; then
    echo "Error : $DEP command not found"
    exit 1
  fi
}

check_dep appimagetool
check_dep linuxdeploy
check_dep pyinstaller
#check_dep pyuic5


#ARCH=`dpkg --print-architecture`
MULTIARCH=`gcc -dumpmachine`
LIBDIR=lib/${MULTIARCH}

# enables running this script from different directory
AppDirParent="$(readlink -f "$(dirname "$0")")"
cd "$AppDirParent"

# generate resource and ui files
#pyrcc5 -o ../quartz_browser/resources_rc.py ../files/resources.qrc
#pyuic5 -o ../quartz_browser/ui_download_confirm.py ../files/download_confirm.ui
#pyuic5 -o ../quartz_browser/ui_settings_dialog.py ../files/settings_dialog.ui
# run pyinstaller
pyinstaller ../Windows/quartz_browser.spec
rm -r build


mkdir -p AppDir/usr/bin
mkdir -p AppDir/usr/lib
mkdir -p AppDir/usr/share/applications
mkdir -p AppDir/usr/share/icons/hicolor/scalable/apps
mkdir -p AppDir/usr/share/metainfo

cd AppDir

APPDIR=`pwd`

# copy executable and desktop file
cp ../../files/quartz-browser.desktop usr/share/applications/io.github.ksharindam.quartz_browser.desktop
#cp ../../files/io.github.ksharindam.quartz_browser.metainfo.xml usr/share/metainfo
cp ../AppRun .

# copy pyinstaller generated files
cp -r ../dist/quartz_browser usr/lib
# remove excess library files
rm -r usr/lib/quartz_browser/_internal/lib*.so.*
rm -r usr/lib/quartz_browser/_internal/PyQt5/Qt5/plugins/*
rm -r usr/lib/quartz_browser/_internal/PyQt5/Qt5/translations
# copy some required files we deleted earlier
cp ../dist/quartz_browser/_internal/libpython* usr/lib/quartz_browser/_internal
# ------- copy Qt5 Plugins ---------
QT_PLUGIN_PATH=${APPDIR}/usr/lib/quartz_browser/_internal/PyQt5/Qt5/plugins
QT_PLUGIN_SRC=${APPDIR}/../dist/quartz_browser/_internal/PyQt5/Qt5/plugins

# X11 support
mkdir -p ${QT_PLUGIN_PATH}/platforms
cp ${QT_PLUGIN_SRC}/platforms/libqxcb.so ${QT_PLUGIN_PATH}/platforms

# Wayland support
cp ${QT_PLUGIN_SRC}/platforms/libqwayland-generic.so ${QT_PLUGIN_PATH}/platforms
cp -r ${QT_PLUGIN_SRC}/wayland-shell-integration ${QT_PLUGIN_PATH}
cp -r ${QT_PLUGIN_SRC}/wayland-graphics-integration-client ${QT_PLUGIN_PATH}

# OpenGL support
cp -r ${QT_PLUGIN_SRC}/xcbglintegrations ${QT_PLUGIN_PATH}

# save as jpeg support
mkdir -p ${QT_PLUGIN_PATH}/imageformats
cp ${QT_PLUGIN_SRC}/imageformats/libqjpeg.so ${QT_PLUGIN_PATH}/imageformats

# print support
mkdir -p ${QT_PLUGIN_PATH}/printsupport
cp ${QT_PLUGIN_SRC}/printsupport/libcupsprintersupport.so ${QT_PLUGIN_PATH}/printsupport

# using Fusion theme does not require bundling any style plugin
mkdir -p ${QT_PLUGIN_PATH}/styles
cp ${QT_PLUGIN_SRC}/styles/libqt5ct-style.so ${QT_PLUGIN_PATH}/styles
mkdir -p ${QT_PLUGIN_PATH}/platformthemes
cp ${QT_PLUGIN_SRC}/platformthemes/libqt5ct.so ${QT_PLUGIN_PATH}/platformthemes

# Without it works fine, but youtube shows 'no network connection' message
mkdir -p ${QT_PLUGIN_PATH}/bearer
cp ${QT_PLUGIN_SRC}/bearer/libqgenericbearer.so ${QT_PLUGIN_PATH}/bearer


# ----- End of 'Copy Qt5 Plugins' ------

# copy ssl
cp /usr/${LIBDIR}/libssl.so.3 usr/lib
cp /usr/${LIBDIR}/libcrypto.so.3 usr/lib

# Copy Gstreamer plugins and binaries (for video support)
#mkdir -p ${APPDIR}/usr/lib/gstreamer-1.0
#cp /usr/${LIBDIR}/gstreamer-1.0/*.so usr/lib/gstreamer-1.0
#rm usr/lib/gstreamer-1.0/libgstgio.so
#rm usr/lib/gstreamer-1.0/libgstjack.so
#cp /usr/${LIBDIR}/gstreamer1.0/gstreamer-1.0/* usr/bin

# cleanup
rm -r ${APPDIR}/../dist

# Deploy dependencies (--appimage-extract-and-run option is for docker)
linuxdeploy --appimage-extract-and-run --appdir .  --icon-file=../../files/quartz-browser.png

# dump build info
#lsb_release -a > usr/share/BUILD_INFO
#ldd --version | grep GLIBC >> usr/share/BUILD_INFO
#python3 --version >> usr/share/BUILD_INFO

cd ..

# fixes firejail permission issue
chmod -R 0755 AppDir


#appimagetool AppDir
appimagetool --appimage-extract-and-run AppDir

