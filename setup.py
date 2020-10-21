import os
import setuptools

README_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "README.md")


def setup():
    readme_content = ''
    with open(README_PATH, "r") as fp:
        readme_content = fp.read()
    setuptools.setup(
        name="roundrobin",
        version="0.0.2",
        description="Collection of roundrobin utilities",
        long_description=readme_content,
        long_description_content_type="text/markdown",
        url="https://github.com/linnik/roundrobin",
        author="Vyacheslav Linnik",
        author_email="hello@slavalinnik.com",
        license="MIT",
        classifiers=[
            "License :: OSI Approved :: MIT License",
            'Programming Language :: Python',
            "Programming Language :: Python :: 2",
            "Programming Language :: Python :: 2.7",
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Operating System :: OS Independent',
        ],
        packages=setuptools.find_packages(),
    )


if __name__ == "__main__":
    setup()
