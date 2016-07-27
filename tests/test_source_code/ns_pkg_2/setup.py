from setuptools import setup, find_packages

setup(
    name='ns_pkg_2',
    version='1.0.0',
    description='Test package',
    author='Nokia',
    url='http://www.nokia.com',
    packages=find_packages(exclude=["test", "test.*"]),
    namespace_packages=['namespacepkg']
)
