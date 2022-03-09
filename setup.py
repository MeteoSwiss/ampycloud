"""
Copyright (c) 2021-2022 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

"""

# Import from python packages
from pathlib import Path
from setuptools import setup, find_packages  # Always prefer setuptools over distutils

# Run the version file
with open(Path('.') / 'src' / 'ampycloud' / 'version.py') as fid:
    version = next(line.split("'")[1] for line in fid.readlines() if 'VERSION' in line)

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    dependency_links=[],
    name="ampycloud",
    version=version,
    license='BSD-3-Clause',

    # Include all packages under src
    packages=find_packages(where="src"),
    # Tell setuptools packages are under src
    package_dir={"": "src"},

    url="https://meteoswiss.github.io/ampycloud",
    project_urls={
        'Source': 'https://github.com/MeteoSwiss/ampycloud/',
        'Changelog': 'https://meteoswiss.github.io/ampycloud/changelog.html',
        'Issues': 'https://github.com/MeteoSwiss/ampycloud/issues'
    },
    author="Frédéric P.A. Vogt",
    author_email="frederic.vogt@meteoswiss.ch",
    description="Characterization of cloud layers from ceilometer measurements",
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires='>=3.8.0',
    install_requires=[
        "matplotlib >= 3.4.2",
        "numpy >= 1.20.3",
        "scikit-learn >= 0.24.2",
        "pandas >= 1.3.1",
        "pyyaml",
        "ruamel.yaml"
    ],
    extras_require={
        'dev': ['sphinx', 'sphinx-rtd-theme', 'pylint', 'pytest']
    },
    # Setup entry points to use ampycloud directly from a terminal
    entry_points={
        'console_scripts': ['ampycloud_speed_test=ampycloud.__main__:ampycloud_speed_test',
                            'ampycloud_copy_prm_file=ampycloud.__main__:ampycloud_copy_prm_file']},
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',
        # Indicate who your project is intended for
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Atmospheric Science',
        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: BSD License',
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3.8',
    ],
    # Let's make sure the parameter non-py files get included in the wheels on pypi.
    include_package_data=True
)
