from setuptools import setup, find_packages

setup(
    name='sf1-package2',
    version='1.0.0',
    description='Test package',
    author='Nokia',
    url='http://www.nokia.com',
    packages=find_packages(exclude=["test", "test.*"])
)
