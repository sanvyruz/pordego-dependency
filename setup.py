from setuptools import setup, find_packages


with open('LICENSE') as f:
    LICENSE = f.read()


CLASSIFIERS = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7"
]

VERSION = "1.2.2"

setup(
    name='pordego-dependency3',
    version=VERSION,
    license=LICENSE,
    description='Pordego plugin for code complexity analysis using the snakefood library',
    author='Sandeep Cavale',
    author_email='sandeepcavale@gmail.com',
    url="https://github.com/sanvyruz/pordego-dependency",
    download_url="https://github.com/sanvyruz/pordego-dependency/tarball/{}".format(VERSION),
    packages=find_packages(exclude=('tests', 'docs', "tests.*")),
    install_requires=["snakefood", "requests"],
    classifiers=CLASSIFIERS,
    entry_points={'pordego.analysis': ["dependency = pordego_dependency.entry_point:analyze_dependency"]},
)
