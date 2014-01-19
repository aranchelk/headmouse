Headmouse
=========

Computer vision head tracking mouse software.

Install
-------

Install is messy. ``headmouse`` depends on OpenCV, which must be installed manually, 
and provides its own, non-PyPi based Python wrapper. 

**OpenCV**

To get the OpenCV official ``cv2`` wrapper:

- Install OpenCV
- Install numpy
- Link the cv2.so and cv2.py files into your PYTHONPATH

On Mac OS X::

	pip install headmouse

	brew install opencv
	export PYTHONPATH=/usr/local/lib/python2.7/site-packages:$PYTHONPATH

Or, if you have a ``headmouse`` virtualenv::

	cd ~/.virtualenvs/headmouse/lib/python2.7/site-packages
	ln -s /usr/local/Cellar/opencv/2.4.7.1/lib/python2.7/site-packages/cv.py
	ln -s /usr/local/Cellar/opencv/2.4.7.1/lib/python2.7/site-packages/cv2.so

**PyMouse/PyUserinput**

PyMouse is needed for direct mouse control. I've been unable to get it to run in a
virtualenv due to its needing PyObjC.

