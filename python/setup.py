#!/usr/bin/env python

from setuptools import setup, find_packages

required_modules = [
	"numpy",
	"psutil",
	]

readme = ""
try:
	with open("README.rst", "rb") as f:
		readme = f.read()
except:
	pass

setup(
	name="headmouse",
	version="0.0.1",
	description="",
	author="Carl Haken",
	author_email="",
	url="https://bitbucket.com/carlhaken/headmouse",

	packages=find_packages(exclude='tests'),
	install_requires=required_modules,

	package_data={
		'headmouse': ['data/cascades/*.xml'],
	},

	entry_points={
		"console_scripts": [
			"headmouse = headmouse:main"
		]
	},

	tests_require=["nose"],
	test_suite="nose.collector",

	long_description=readme,
	classifiers=[
		"Intended Audience :: End Users/Desktop",
		"Environment :: X11 Applications",
		"Environment :: MacOS X",
		"Environment :: Win32 (MS Windows)",
		"Topic :: System",
		"Topic :: Software Development :: User Interfaces",
	]
)

