# setup.py
# Copyright 2011 Roger Marsh
# Licence: See LICENCE (BSD licence)
"""chesstab setup file."""

from setuptools import setup

if __name__ == "__main__":

    long_description = open("README").read()
    install_requires = [
        "solentware-base==4.1.6",
        "chessql==2.0.2",
        "solentware-grid==2.1.4",
        "pgn-read==2.1.2",
        "solentware-misc==1.3.2",
        "uci-net==1.2.3",
    ]

    setup(
        name="chesstab",
        version="5.0.3",
        description="Database for chess games",
        author="Roger Marsh",
        author_email="roger.marsh@solentware.co.uk",
        url="http://www.solentware.co.uk",
        packages=[
            "chesstab",
            "chesstab.core",
            "chesstab.basecore",
            "chesstab.gui",
            "chesstab.help",
            "chesstab.berkeleydb",
            "chesstab.db",
            "chesstab.dpt",
            "chesstab.sqlite",
            "chesstab.apsw",
            "chesstab.unqlite",
            "chesstab.vedis",
            "chesstab.gnu",
            "chesstab.ndbm",
            "chesstab.fonts",
            "chesstab.tools",
            "chesstab.samples",
        ],
        package_data={
            "chesstab.fonts": ["*.TTF", "*.zip"],
            "chesstab.help": ["*.rst"],
        },
        long_description=long_description,
        license="BSD",
        classifiers=[
            "License :: OSI Approved :: BSD License",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Operating System :: OS Independent",
            "Topic :: Games/Entertainment :: Board Games",
            "Intended Audience :: End Users/Desktop",
            "Development Status :: 3 - Alpha",
        ],
        install_requires=install_requires,
        dependency_links=[
            "-".join(required.split("==")).join(
                ("http://solentware.co.uk/files/", ".tar.gz")
            )
            for required in install_requires
        ],
    )
