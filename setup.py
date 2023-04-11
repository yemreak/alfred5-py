"""Setup script for package

References: 
    - https://github.com/openai/openai-python/blob/main/setup.cfg
"""

from glob import glob
from os.path import basename, splitext
from setuptools import find_packages, setup
from pathlib import Path

VERSION = "1.1.0"
DESCRIPTION = "Simple python wrapper for alfred5 workflow / snippets"
README_PATH = "docs/README.md"
USERNAME = "yedhrab"
REPOSITORY = "alfred5"
KEYWORDS = [
    "alfred",
    "alfred5",
    "workflow",
    "snippets",
    "alfred-workflows",
    "alfred-snippets",
]
INSTALL_REQUIRES = ["aiohttp==3.8.4", "ruamel.yaml==0.17.21"]
EXSTRAS_REQUIRE = {
    "dev": [
        "black==23.3.0",
        "autoflake==2.0.2",
        "pytest==7.3.0",
        "pytest-asyncio==0.21.0",
    ]
}

setup(
    name=REPOSITORY,
    version=VERSION,
    license="Apache Software License 2.0",
    description=DESCRIPTION,
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
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Utilities",
    ],
    project_urls={
        "Source": f"https://github.com/{USERNAME}/{REPOSITORY}/",
        "Changelog": f"https://github.com/{USERNAME}/{REPOSITORY}/releases",
        "Issue Tracker": f"https://github.com/{USERNAME}/{REPOSITORY}/issues",
    },
    keywords=KEYWORDS,
    python_requires=">=3.9.6",
    install_requires=INSTALL_REQUIRES,
    extras_require=EXSTRAS_REQUIRE,
    setup_requires=[],
    entry_points={},
)
