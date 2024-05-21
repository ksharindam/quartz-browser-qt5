![License](https://img.shields.io/github/license/ksharindam/quartz-browser-qt5)
![Release](https://img.shields.io/github/v/release/ksharindam/quartz-browser-qt5)
![Release Date](https://img.shields.io/github/release-date/ksharindam/quartz-browser-qt5)
![Downloads Total](https://img.shields.io/github/downloads/ksharindam/quartz-browser-qt5/total)
![Downloads Latest](https://img.shields.io/github/downloads/ksharindam/quartz-browser-qt5/latest/total)

# Quartz Browser

A useful fast Web Browser for Windows and Linux written in pyqt5 webkit  

### Description

This browser is aimed at ease of use, faster page loading, very short startup time.  
This has minimal settings to avoid confusion.Yet it has most useful settings, such as load images on/off, javascript on/off, change font.  
To save pages to read later, print feature can be used to save as pdf. And it can also export the whole page as png image.  

### Installation

For linux you can download AppImage from releases page. Dont need to install any dependencies, just mark it executable and double click to run.  

If you wan to install using pip, first install these dependencies...  

* python3  
* python3-pyqt5  
* python3-pyqt5.qtwebkit  
* gstreamer1.0-plugins-base, gstreamer1.0-plugins-good, gstreamer1.0-alsa, gstreamer1.0-libav (Optional, for video support)  

To Install the browser open terminal inside quartz-browser-qt5 directory. 
And then run following command..  
`$ sudo pip3 install .`  

Quartz Browser will be automatically added to applications menu.  

To uninstall run..  
`$ sudo pip3 uninstall quartz-browser`    

### Usage

To run after installing, type command..  
`$ quartz_browser`  

Or  

`$ quartz_browser http://www.google.com`  

If you want to run the browser without/before installing, then  
Open terminal and change directory to quartz-browser-qt5 and run  
`$ ./quartz`  

Or  

`$ ./quartz http://www.google.com`  

### Command Line Options
--kiosk = Enable kiosk mode  

### Important Features :

* Auto Refresh Mode, Kiosk Mode  
* Turn Javascript, Load Images on/off  option in main menu  
* Save as PDF, Save as HTML  
* Export full page as PNG/JPEG image, HTML file  
* Custom User Agent  
* Internal Download Manager with pause/resume support  
* Download remaining file that was partially downloaded in another browser  
* External Download Manager support (e.g - wget, uGet )  
* Play video with RTSP protocol using a media player (e.g omxplayer, mplayer)  
* YouTube video download support. (Download button automatically appears)  
* HTML5 Video download support.  

### Screenshot

![Main Window](files/Screenshot.jpg)
