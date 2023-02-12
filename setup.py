from glob import glob
from os.path import basename, splitext
from setuptools import find_packages, setup
from pathlib import Path

VERSION = "1.0.5"
README_PATH = "docs/README.md"
USERNAME = "yedhrab"
REPOSITORY = "alfred5"

setup(
    name=REPOSITORY,
    version=VERSION,
    license="Apache Software License 2.0",
    description="Simple python wrapper for alfred workflow / snippets",
    long_description=Path(README_PATH).read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    author="Yunus Emre Ak",
    author_email="yemreak.com@gmail.com",
    url=f"https://github.com/{USERNAME}/{REPOSITORY}",
    packages=find_packages(),
    py_modules=[splitext(basename(path))[0] for path in glob(f"*.py")],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: Unix",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Utilities",
    ],
    project_urls={
        "Source": f"https://github.com/{USERNAME}/{REPOSITORY}/",
        "Documentation": f"https://github.com/{USERNAME}/{REPOSITORY}/wiki",
        "Changelog": f"https://github.com/{USERNAME}/{REPOSITORY}/releases",
        "Issue Tracker": f"https://github.com/{USERNAME}/{REPOSITORY}/issues",
    },
    keywords=[
        "alfred",
        "alfred5",
        "workflow",
        "snippets",
        "alfred-workflows",
        "alfred-snippets",
    ],
    python_requires=">=3.9.6",
    install_requires=["aiohttp==3.8.3", "ruamel.yaml==0.17.21"],
    extras_require={},
    setup_requires=[],
    entry_points={},
)
