from setuptools import setup, find_packages

with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(
    name='open-deepsearch',
    version='0.1.0',
    author='Jason Chuang',
    author_email='chuangtcee@gmail.com',
    description='Deep Research but Open-Sourced, called open-deepsearch',
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
            'deepsearch = open_deepsearch.run:main',
        ],
    },
    install_requires=[
        "python-dotenv>=1.0.1",
        "openai==1.63.2",
        "aiohttp>=3.9.0",
        "aiofiles>=23.2.1",
        "tiktoken>=0.5.0",
        "firecrawl-py>=1.12.0",
        "tavily-python==0.5.1",
        "Crawl4AI==0.4.248",
        "typer>=0.9.0",
        "prompt-toolkit>=3.0.0",
        "pydantic==2.10.6",
        "pypdf2==3.0.1",
        "html2text==2024.2.26"
    ],
    # This line enables editable installs
    # With 'pip install -e .' equivalent
    # to install your package in editable mode
    # so changes in your source code are immediately reflected
    # without needing to reinstall
    options={'bdist_wheel': {'universal': False}},
    setup_requires=['setuptools>=70.0.0', 'wheel']
)