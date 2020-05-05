pordego-dependency3
===================

Summary
-------
`Pordego <https://github.com/ttreptow/pordego>`_ plugin that analyzes package dependencies using the `Snakefood <https://pypi.python.org/pypi/snakefood>`_ library.

Forked for Python3 support.

Configuration
-------------

source_paths
^^^^^^^^^^^^
There is one required parameter "source_paths". This parameter should be a list of paths to directories containing Python source code (other types of code are ignored). The paths are searched recursively, so only the top level folder need be specified.
The paths can be absolute or relative to the directory where pordego is run.

ignore (optional)
^^^^^^^^^^^^^^^^^
The ignore parameter is used to specify a list of file patterns to exclude from the analysis. Glob style patterns are accepted.

Example::

  ignore:
      - "*test*"

This will ignore all files and directories containing "test"

analysis_packages (optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The analysis_packages parameter can be use to limit the dependency analysis to a list of packages.
The package names must match the one specified in the setup.py "name" field.

dependency_map (optional)
^^^^^^^^^^^^^^^^^^^^^^^^^
This parameter is used to specify a list of acceptable dependencies for a package.
An error will be thrown if the package imports any package other than the ones in the list.
Only local packages (in source dirs) are considered, not dependencies downloaded from pypi.
An empty list means that the package cannot depend on any other package.
If a package is not in dependency_map, it may depend on any package.

Example::

  dependency_map:
    my-package-name:
       - some-package
    my-no-depend-package: []

In this case, my-package-name can only import from some-package, while my-no-depend-package may not import from any other package (other than ones found on pypi)

check_requirements (optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
If check_requirements is true, the requirements from the package setup will be compared against the actual dependencies.
Any missing or extraneous requirements will cause a failure.

"Local" packages (those that can be found in the source_paths) are detected fairly reliably, assuming that all possible local requirements can be found in those paths.

Packages downloaded from pypi are included in the analysis with some caveats.
The required package must be either installed in the environment the plugin is executing in or downloadable from pypi.
You might have to use the package_server_url and pip_options configuration parameters to specify additional options if you are behind a corporate firewall or have a local package server.

