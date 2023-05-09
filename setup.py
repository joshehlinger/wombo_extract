import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='wombo-extractor',
    version="1.0.0",
    author="Joshua Ehlinger",
    install_requires=open('requirements.txt').read(),
    description='Grabs the downloadable URL from wombo',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/joshehlinger/wombo_extract",
    py_modules=['wombo'],
    entry_points={
        'console_scripts': [
            'wombo-extract = run:main'
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)