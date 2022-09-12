from setuptools import setup, find_packages

from pathlib import Path
long_description = (Path(__file__).parent / "README.md").read_text()

setup(
    name='extractnum',
    version="1.0.1",
    description='A CLI for extracting number arrays from an unstructured log file and plotting results.',
    author="Keytoyze",
    author_email='cmx_1007@foxmail.com',
    license='MIT',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(where='.', exclude=(), include=('*',)),
    url='https://github.com/Keytoyze/ExtractNum',
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