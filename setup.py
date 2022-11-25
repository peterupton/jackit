#!/usr/bin/env python3
""" setup.py for JackIt Improved """
# -*- encoding: utf-8 -*-
from distutils.core import setup

setup(
    name='JackIt Improved',
    version='0.0.1',
    author='JackIt contributors, nrf-research-firmware contributors, Peter Upton',
    packages=['jackit', 'jackit.lib', 'jackit.plugins'],
    scripts=['bin/jackit'],
    url='https://github.com/peterupton/jackit',
    license='BSD',
    description='Exploit framework for MouseJack vulnerability.',
    install_requires=[
        "click==5.1",
        "pyusb==1.0.0",
        "tabulate==0.7.5",
        "six==1.10.0"
    ],
)
