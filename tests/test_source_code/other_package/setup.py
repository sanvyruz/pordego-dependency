from setuptools import setup, find_packages

setup(
    name='other_package',
    version='1.0.0',
    description='Test package',
    author='Nokia',
    url='http://www.nokia.com',
    packages=find_packages(exclude=["test", "test.*"])
)
