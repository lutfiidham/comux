#!/usr/bin/env python3
"""Setup script for comux."""

import os
import sys
from setuptools import setup, find_packages
from setuptools.command.install import install


class PostInstallCommand(install):
    """Post-installation for alias setup."""

    def run(self):
        install.run(self)
        # Run post-install script
        post_install_path = os.path.join(os.path.dirname(__file__), 'post_install.py')
        if os.path.exists(post_install_path):
            import subprocess
            subprocess.check_call([sys.executable, post_install_path])


setup(
    name="comux",
    version="1.0.0",
    description="Interactive Command-Line Coding Assistant",
    author="Comux Team",
    py_modules=["comux", "post_install", "quick_update"],
    install_requires=["requests>=2.31.0"],
    entry_points={
        "console_scripts": [
            "comux=comux:main",
        ],
    },
    cmdclass={
        'install': PostInstallCommand,
    },
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
)