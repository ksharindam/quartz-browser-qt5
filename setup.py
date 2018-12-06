from setuptools import setup
import platform
from quartz_browser import __version__

def readme():
    with open('README.rst') as f:
        return f.read()

if platform.system()=='Linux':
    app_data = [('share/applications', ['files/quartz.desktop']),
                ('share/icons', ['files/quartz-browser.png'])]
else:
    app_data = []

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
    #install_requires=['PyQt5',      ],
    classifiers=[
    'Development Status :: 5 - Production/Stable',
    'Environment :: X11 Applications :: Qt',
    'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
    'Operating System :: POSIX :: Linux',
    'Operating System :: Windows',
    'Programming Language :: Python :: 3.5',
    'Topic :: Internet :: WWW/HTTP :: Browsers',
    ],
    packages=['quartz_browser', 'quartz_browser.pytube', 'quartz_browser.pytube.contrib'],
    entry_points={
      'console_scripts': ['quartz=quartz_browser.main:main',
                          'pytube=quartz_browser.pytube.__main__:main'],
    },
    data_files = app_data,
    include_package_data=True,
    zip_safe=False
    )
