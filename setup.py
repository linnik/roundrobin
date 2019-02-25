import pathlib

import setuptools

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setuptools.setup(
    name="roundrobin",
    version="0.0.1",
    description="Collection of roundrobin utilities",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/linnik/roundrobin",
    author="Vyacheslav Linnik",
    author_email="hello@slavalinnik.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
    ],
    packages=setuptools.find_packages(),
)
