from setuptools import setup, find_packages
import sys, os

version = '0.37'

setup(name='Eddie-Tool',
      version=version,
      description="System monitoring agent.",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Chris Miles',
      author_email='miles.chris@gmail.com',
      url='http://eddie-tool.net/',
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
