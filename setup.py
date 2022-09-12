from setuptools import setup, find_packages

setup(
    name='extractnum',
    version="1.0.0",
    description='A CLI for extracting number arrays from an unstructured log file and plotting results.',
    author="Keytoyze",
    author_email='cmx_1007@foxmail.com',
    packages=find_packages(where='.', exclude=(), include=('*',)),
    entry_points={
        'console_scripts': [
            'extractnum=extractnum.main:main'
        ]
    },
    install_requires=[
        'numpy',
        'matplotlib'
    ]
)