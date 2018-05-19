#!/usr/bin/env python
from setuptools import setup, find_packages
import kademlia

setup(
    name="kademlia",
    version='1.0.1',

    packages=find_packages(),
    install_requires=open('requirements.txt').readlines(),
    extras_require={
        'dev': [
            'vmnet'
        ]
    },
    include_package_data=True,

    long_description=open('README.md').read(),
    url="https://github.com/Lamden/kademlia",
    author='Lamden',
    email='team@lamden.io',
    license="MIT",
    classifiers=[
        'Programming Language :: Python :: 3.6',
    ],
)
