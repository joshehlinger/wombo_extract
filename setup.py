import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='wombo-extractor',
    version="0.0.1",
    author="Joshua Ehlinger",
    install_requires=open('requirements.txt').read(),
    description='Grabs the downloadable URL from wombo',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/joshehlinger/wombo_extract",
    py_modules=['extract'],
    entry_points={
        'console_scripts': [
            'wombo-extract = extract:main'
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)