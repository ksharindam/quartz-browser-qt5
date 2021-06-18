from setuptools import setup
import platform
from quartz_browser import __version__

def readme():
    with open('README.md') as f:
        return f.read()

if platform.system()=='Linux':
    app_data = [('share/applications', ['files/quartz-browser.desktop']),
                ('share/icons', ['files/quartz-browser.png'])]
else:
    app_data = []

setup(
    name='quartz-browser',
    version=__version__,
    description='Fast Lightweight web browser written in PyQt5',
    long_description=readme(),
    long_description_content_type = 'text/markdown',
    keywords='pyqt pyqt5 browser qtwebkit',
    url='http://github.com/ksharindam/quartz-browser-qt5',
    author='Arindam Chaudhuri',
    author_email='ksharindam@gmail.com',
    license='GNU GPLv3',
    #install_requires=['PyQt5',],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: X11 Applications :: Qt',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Browsers',
    ],
    packages=['quartz_browser'],
    entry_points={
      'console_scripts': ['quartz_browser=quartz_browser.main:main'],
    },
    data_files = app_data,
    include_package_data=True,
    zip_safe=False
    )
