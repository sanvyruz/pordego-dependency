from setuptools import setup, find_packages


with open('LICENSE') as f:
    LICENSE = f.read()


CLASSIFIERS = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2.7"
]

VERSION = "1.2.0"

setup(
    name='pordego-dependency',
    version=VERSION,
    license=LICENSE,
    description='Pordego plugin for code complexity analysis using the snakefood library',
    author='Tim Treptow',
    author_email='tim.treptow@gmail.com',
    url="https://github.com/ttreptow/pordego-dependency",
    download_url="https://github.com/ttreptow/pordego-dependency/tarball/{}".format(VERSION),
    packages=find_packages(exclude=('tests', 'docs', "tests.*")),
    install_requires=["snakefood", "requests"],
    classifiers=CLASSIFIERS,
    entry_points={'pordego.analysis': ["dependency = pordego_dependency.entry_point:analyze_dependency"]},
)
