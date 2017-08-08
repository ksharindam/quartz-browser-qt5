#!/usr/bin/env python

from setuptools import setup
from quartz_browser import __version__

def readme():
    with open('README.rst') as f:
        return f.read()

setup(
      name='quartz-browser',
      version=__version__,
      description='Fast Lightweight web browser written in PyQt5',
      long_description=readme(),
      keywords='pyqt pyqt5 browser qtwebkit',
      url='http://github.com/ksharindam/quartz-browser-qt5',
      author='Arindam Chaudhuri',
      author_email='ksharindam@gmail.com',
      license='GNU GPLv3',
#      install_requires=['PyQt5',      ],
      classifiers=[
      'Development Status :: 5 - Production/Stable',
      'Environment :: X11 Applications :: Qt',
      'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
      'Operating System :: POSIX :: Linux',
      'Programming Language :: Python :: 2.7',
      'Topic :: Internet :: WWW/HTTP :: Browsers',
      ],
      packages=['quartz_browser', 'quartz_browser.pytube'],
      entry_points={
          'console_scripts': ['quartz=quartz_browser.main:main',
                              'pytube=quartz_browser.pytube.__main__:main'],
      },
      data_files=[
                 ('share/applications', ['files/quartz.desktop']),
                 ('share/icons', ['files/quartz-browser.png'])
      ],
      include_package_data=True,
      zip_safe=False)
