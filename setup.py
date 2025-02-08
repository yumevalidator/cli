from setuptools import setup, find_packages

setup(
    name="yumevalidator",  # Change to your package name
    version="0.1.0",
    packages=find_packages(),
    install_requires=[],  # Add dependencies if needed
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "yumevalidator=src.main:main", # Command name -> Function to run
        ],
    },
    author="Victor Mak",
    author_email="programmer.htetaung@proton.me",
    description="An experiment that displays 'Hello World' from an executable package",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/DreamerChaserHAH/python-executable-pypi-experiment",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)