from setuptools import setup, find_packages

with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(
    name='open_deepsearch',
    version='0.0.2',
    author='Jason Chuang',
    author_email='chuangtcee@gmail.com',
    description='Open DeepResearch',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/aidatatools/open-deepsearch',
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
    entry_points={
        'console_scripts': [
            'deepsearch = open_deepsearch.main:main',
        ],
    },
    # This line enables editable installs
    # With 'pip install -e .' equivalent
    # to install your package in editable mode
    # so changes in your source code are immediately reflected
    # without needing to reinstall
    options={'bdist_wheel': {'universal': False}},
    setup_requires=['setuptools>=70.0.0', 'wheel']
)