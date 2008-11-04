from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages
import sys, os

from eddietool.version import version

setup(name='EDDIE-Tool',
    version=version,
    description="The EDDIE Tool is a system and network monitoring, security, and performance analysis agent developed entirely in threaded Python. Its key features are portability, extendibility, and powerful configuration.",
    long_description="""\
The EDDIE Tool can perform all basic system monitoring checks, such as: filesystem; processes; system load; and network configuration. It can also perform such network monitoring tasks as: ping checks; HTTP checks; POP3 tests; SNMP queries; RADIUS authentication tests; and customized TCP port checks. Finally, a few checks lend themselves to security monitoring: watching files for changes; and scanning logfiles. The EDDIE Tool can also send any collected statistic to RRD files to be displayed graphically by any standard RRD tool. No need to run multiple monitoring and data collection agents. Monitoring rules are just like Python expressions and can be as simple or as complex as needed. Advanced alert control functionality such as exponential back-off and dependencies are also standard.""",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: No Input/Output (Daemon)",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: BSD :: FreeBSD",
        "Operating System :: POSIX :: BSD :: OpenBSD",
        "Operating System :: POSIX :: HP-UX",
        "Operating System :: POSIX :: Linux",
        "Operating System :: POSIX :: SunOS/Solaris",
        "Programming Language :: Python",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Networking :: Monitoring",
        "Topic :: System :: Systems Administration",
    ], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='Chris Miles',
    author_email='miles.chris@gmail.com',
    url='http://eddie-tool.net/',
    download_url='http://pypi.python.org/pypi/EDDIE-Tool',
    license='GPL',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
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
