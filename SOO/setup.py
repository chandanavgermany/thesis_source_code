#!/usr/bin/env python

import os
from setuptools import  setup, Extension

__version__ = '1.1.0'

class NumpyExtension(Extension):
    # setuptools calls this function after installing dependencies
    def _convert_pyx_sources_to_lang(self):
        import numpy
        self.include_dirs.append(numpy.get_include())
        # include libraries and compile flags if not on Windows
        if os.name != 'nt':
            self.libraries.append('m')
            self.extra_compile_args.append('-ffast-math')
        super()._convert_pyx_sources_to_lang()


ext_modules = [NumpyExtension('Optimizer.Genetic_alg._ga_helpers',
                              ['Optimizer/Genetic_alg/_ga_helpers.pyx']),
               NumpyExtension('Optimizer.solution._makespan',
                              ['Optimizer/solution/_makespan.pyx']),
               NumpyExtension('Optimizer.Tabu_Search._generate_neighbor',
                              ['Optimizer/Tabu_Search/_generate_neighbor.pyx']),
               NumpyExtension('Optimizer.Simulated_Annealing._generate_neighbor',
                              ['Optimizer/Simulated_Annealing/_generate_neighbor.pyx'])
               ]

setup(
    name='Optimizer',
    version=__version__,
    description='Package for solving the job shop schedule problem with sequence dependent set up times.',
    author='Chandan',
    refered_from = 'https://job-shop-schedule-problem.readthedocs.io/en/stable/',
    author_email='chandanav8421@gmail.com',
    python_requires='>=3.6.0',
    classifiers=[
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Cython',
    ],
    setup_requires=['numpy==1.16.*', 'cython==0.29.*'],
    include_package_data=True,
    ext_modules=ext_modules,
)
