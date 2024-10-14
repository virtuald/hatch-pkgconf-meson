project('portfwds', 'cpp', default_options: ['cpp_std=c++20'])

py = import('python').find_installation(pure: false)

wpinet = dependency('wpinet')
pybind11 = dependency('robotpy-pybind11')

py.extension_module(
    'port',
    'port.cpp',
    install: true,
    dependencies: [wpinet, pybind11],
)