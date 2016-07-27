from setuptools import setup, find_packages

setup(
    name='third_party_import_pkg',
    version='1.0.0',
    description='Test package',
    author='Nokia',
    url='http://www.nokia.com',
    packages=find_packages(exclude=["test", "test.*"]),
    install_requires=["snakefood"]
)
