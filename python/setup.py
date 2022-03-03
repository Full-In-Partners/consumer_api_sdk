import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="Harmonic SDK",
    version="0.0.2",
    author="Ronald Yang",
    author_email="ronald@harmonic.ai",
    description="python SDK for Harmonic Consumer APIs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/harmonicai/consumer_api_sdk.git",
    install_requires=["requests"],
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
