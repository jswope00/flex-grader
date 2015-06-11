"""Setup for flexible_grader XBlock."""

import os
from setuptools import setup


def package_data(pkg, roots):
    """Generic function to find package_data.

    All of the files under each of the `roots` will be declared as package
    data for package `pkg`.

    """
    data = []
    for root in roots:
        for dirname, _, files in os.walk(os.path.join(pkg, root)):
            for fname in files:
                data.append(os.path.relpath(os.path.join(dirname, fname), pkg))

    return {pkg: data}


setup(
    name='flexible_grader-xblock',
    version='0.1',
    description='flexible_grader XBlock',   # TODO: write a better description.
    packages=[
        'flexible_grader',
    ],
    install_requires=[
        'XBlock',
    ],
    entry_points={
        'xblock.v1': [
            'flexible_grader = flexible_grader:FlexibleGradingXBlock',
        ]
    },
    package_data=package_data("flexible_grader", ["static", "templates"]),
)
