from ez_setup import use_setuptools
use_setuptools()

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
    scripts = ["bin/eddie-agent"],
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
    ],
    entry_points={
        'console_scripts': [
            'eddie-agent = eddietool.commands:agent',
        ],
    },
    data_files = [
        ('config-sample', ['config-sample/eddie.cf']),
        ('config-sample/rules', [
            'config-sample/rules/cache.rules',
            'config-sample/rules/common.rules',
            'config-sample/rules/dns.rules',
            'config-sample/rules/host.rules',
            'config-sample/rules/message.rules',
            'config-sample/rules/news.rules',
            'config-sample/rules/rrd.rules',
            'config-sample/rules/sys_linux.rules',
            'config-sample/rules/sys_solaris.rules',
            'config-sample/rules/win32_sample.rules',
        ]),
        ('doc', ['doc/manual.html']),
    ],
)
