Headmouse
=========

Computer vision head tracking mouse software.

Usage
-----

`Mouse Keys <http://support.apple.com/kb/PH14235>`_ on Mac OS X may be useful. 

**Configuration**

``headmouse`` can be configured by placing an INI file in ``~/.headmouse``::

    [headmouse]

	acceleration = 10
	sensitivity = 2
	smoothing = 0.4

Install
-------

Install is messy. ``headmouse`` depends on OpenCV, which must be installed manually, 
and provides its own, non-PyPi based Python wrapper. Additionally, for direct mouse 
control, ``headmouse`` requires PyMouse, which, on OS X, requires compiling PyObjC.

**OpenCV**

The trickiest part of the install is compiling OpenCV, then making its ``cv2`` Python 
bindings available to the virtualenv containing ``headmouse``.

Generally, the steps are:

- Install OpenCV
- Install numpy
- Somehow link the ``cv2.so`` and ``cv2.py`` files into your PYTHONPATH. This can be via the 
  ``$PYTHONPATH`` evironment variable, which must be set each session, or by copying 
  or symlinking these files into a directory already on the PYTHONPATH.

**Mac OS X install**

First, install OpenCV using Homebrew::

    $ brew install opencv

Create a virtualenv for the ``headmouse`` program::

   $ mkvirtualenv headmouse

Next, copy or link the OpenCV python bindings into the virtualenv. Do one of:

1. Copy the files::

    cp $(brew --prefix)/lib/python2.7/site-packages/cv* \
    ${VIRTUAL_ENV}/lib/python*/site-packages/

or 

2. Symlink the files::

    ls $(brew --prefix)/lib/python2.7/site-packages/cv* |\
    xargs -I foo ln -s foo "${VIRTUAL_ENV}/lib/python2.7/site-packages/"

or

3. Each time you run the `headmouse` program, first
   ``export PYTHONPATH=$(brew --prefix)/lib/python2.7/site-packages:$PYTHONPATH``

Now install the ``headmouse`` package itself. In the project's `python/` directory::

    $ pip install -r requirements
    $ pip install headmouse

**Debian/Ubuntu install**

1. Packages::

    sudo aptitude install v4l2loopback-utils
    sudo aptitude install python-opencv
    sudo aptitude install python-pip
    sudo aptitude install python-dev
    sudo aptitude install python-tk
    sudo aptitude install ffmpeg

**PyMouse**

PyMouse is needed for direct mouse control. 

It may be possible with easy_install: http://www.slevenbits.com/blog/2012/05/pyobjc-on-mac-os-x-10-7.html

::

	mkvirtualenv myenv
	export MACOSX_DEPLOYMENT_TARGET=10.5
	easy_install pyobjc-core
	easy_install pyobjc

