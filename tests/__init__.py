"""Test package marker.

Required so that ``tests.support.custom_filters`` is importable by name from
the CLI ``--filter-module`` integration tests. Pytest itself does not need
this file (rootdir discovery suffices); the import path does.
"""
