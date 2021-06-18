#!/bin/bash

check_dep()
{
  DEP=$1
  if [ -z $(which $DEP) ] ; then
    echo "Error : $DEP command not found"
    exit 0
  fi
}

check_dep appimagetool
check_dep linuxdeploy
check_dep gcc

MULTIARCH=`gcc -dumpmachine`
LIBDIR=lib/${MULTIARCH}

mkdir -p AppDir/usr/bin
mkdir -p AppDir/usr/share/applications
mkdir -p AppDir/usr/share/icons/hicolor/scalable/apps

cd AppDir

APPDIR=`pwd`

# copy executable, icon and desktop file
cp ../../files/quartz-browser.png usr/share/icons/hicolor/scalable/apps
cp ../../files/quartz-browser.desktop usr/share/applications
cp ../AppRun .
chmod +x AppRun

# create required directories
mkdir -p ${APPDIR}/usr/lib/python3.5
mkdir -p ${APPDIR}/usr/lib/python3/PyQt5
mkdir -p ${APPDIR}/usr/lib/gstreamer-1.0
mkdir -p ${APPDIR}/usr/lib/gstreamer1.0/gstreamer-1.0

# copy main program
cp ../../quartz usr/bin/quartz_browser
chmod +x usr/bin/quartz_browser
cp -r ../../quartz_browser usr/lib/python3
# copy python3 and python3-stdlib
cp /usr/bin/python3 usr/bin

cd /usr/lib/python3.5
cat ${APPDIR}/../python3.5-stdlib.txt | sed -e "s/arm-linux-gnueabihf/${MULTIARCH}/" | xargs -I % cp -r --parents % ${APPDIR}/usr/lib/python3.5

# copy sip module
cd /usr/lib/python3/dist-packages
cp sipconfig_nd5.py sipconfig.py sip.cpython*.so sip.pyi ${APPDIR}/usr/lib/python3

# copy PyQt5 module
cd PyQt5
cp Qt.* QtCore.* QtGui.* QtWidgets.* QtPrintSupport.* \
   QtNetwork.* QtWebKit.* QtWebKitWidgets.* QtXml.* \
   __init__.py ${APPDIR}/usr/lib/python3/PyQt5

cd $APPDIR

# copy qt plugins
mkdir -p usr/lib/qt5/plugins/imageformats
cp /usr/${LIBDIR}/qt5/plugins/imageformats/libqjpeg.so usr/lib/qt5/plugins/imageformats

mkdir -p usr/lib/qt5/plugins/platforms
cp /usr/${LIBDIR}/qt5/plugins/platforms/libqxcb.so usr/lib/qt5/plugins/platforms

mkdir -p usr/lib/qt5/plugins/styles
cp /usr/${LIBDIR}/qt5/plugins/styles/libqgtk2style.so usr/lib/qt5/plugins/styles
cp /usr/${LIBDIR}/qt5/plugins/styles/libqcleanlooksstyle.so usr/lib/qt5/plugins/styles

cp /usr/${LIBDIR}/libssl.so.1.0.2 usr/lib
cp /usr/${LIBDIR}/libcrypto.so.1.0.2 usr/lib

# Copy Gstreamer plugins
cp /usr/${LIBDIR}/gstreamer-1.0/*.so usr/lib/gstreamer-1.0

cp /usr/${LIBDIR}/gstreamer1.0/gstreamer-1.0/* usr/lib/gstreamer1.0/gstreamer-1.0

# Deploy dependencies
linuxdeploy --appdir .

# compile python bytecodes
find usr/lib -iname '*.py' -exec python3 -m py_compile {} \;

cd ..
appimagetool AppDir
