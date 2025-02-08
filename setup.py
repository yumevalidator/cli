from setuptools import setup, find_packages

setup(
    name="yumevalidator",  # Change to your package name
    version="0.1.6",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        '': ['public/*'],
    },
    install_requires=[
        'readchar',
        'smolagents',
        'selenium',
        'helium',
        'pillow',
        'openai'
    ],  # Add dependencies if needed
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "yumevalidator=src.main:main", # Command name -> Function to run
        ],
    },
    author="Victor Mak",
    author_email="contact@htetaung.com",
    description="A GenAI-based UI Validation tool for Deriv AI Hackathon in 2025 Feburary",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yumevalidator/cli",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)