"""
Name = Quartz Browser
Executable Command = quartz
Package Name = quartz-browser
Python Module Name = quartz-browser
Debian Dependency = python3-pyqt5, python3-pyqt5.qtwebkit

Description = A Light Weight Internet Browser
Features =  Change User agent to mobile/desktop
            Print Page to PDF
            Save page as JPG, html
            Turn Javascript, Load Images on/off
            Find Text inside page
            Easy accessible toolbar
            Tabbed browsing
            Download Manager with pause/resume support
            Youtube Video and HTML5 video downloader.
Last Update :
            HTML5 video downloader dialog added
            Youtube Video is parsed in separate thread

...........................................................................
|   Copyright (C) 2017-2018 Arindam Chaudhuri <ksharindam@gmail.com>            |
|                                                                          |
|   This program is free software: you can redistribute it and/or modify   |
|   it under the terms of the GNU General Public License as published by   |
|   the Free Software Foundation, either version 3 of the License, or      |
|   (at your option) any later version.                                    |
|                                                                          |
|   This program is distributed in the hope that it will be useful,        |
|   but WITHOUT ANY WARRANTY; without even the implied warranty of         |
|   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          |
|   GNU General Public License for more details.                           |
|                                                                          |
|   You should have received a copy of the GNU General Public License      |
|   along with this program.  If not, see <http://www.gnu.org/licenses/>.  |
...........................................................................
"""
# TODO : 
#       Facebook sidebar
#       Multiple search engines
#       View source in context menu
# FIXME : 
#       

import os

__version__ = "2.2.1"

homedir = os.environ['HOME']
downloaddir = homedir+"/Downloads/"
program_dir = os.path.dirname(os.path.abspath(__file__)) + '/'
