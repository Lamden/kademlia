#!/usr/bin/env python
from setuptools import setup, find_packages
import kademlia

setup(
    name="kademlia",
    version='1.0.1',
    description="Kademlia is a distributed hash table for decentralized peer-to-peer computer networks.",
    author="Brian Muller",
    author_email="bamuller@gmail.com",
    license="MIT",
    url="https://github.com/Lamden/kademlia",
    packages=find_packages(),
    install_requires=["rpcudp>=3.0.0"],
    package_data={
        'world': 'discovery/data/world.csv'
    }
)
