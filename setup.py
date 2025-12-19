#!/usr/bin/env python3
"""Setup script for comux."""

from setuptools import setup, find_packages

setup(
    name="comux",
    version="1.0.0",
    description="Interactive Command-Line Coding Assistant",
    author="Comux Team",
    py_modules=["comux"],
    install_requires=["requests>=2.31.0"],
    entry_points={
        "console_scripts": [
            "comux=comux:main",
        ],
    },
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
)