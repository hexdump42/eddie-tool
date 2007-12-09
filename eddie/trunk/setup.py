from setuptools import setup, find_packages
import sys, os

from eddietool.version import version

setup(name='Eddie-Tool',
    version=version,
    description="System monitoring agent.",
    long_description="""
""",
    classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='Chris Miles',
    author_email='miles.chris@gmail.com',
    url='http://eddie-tool.net/',
    download_url='http://eddie-tool.net/download/download.html',
    license='GPL',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
    ],
    entry_points="""
    # -*- Entry points: -*-
    """,
)
