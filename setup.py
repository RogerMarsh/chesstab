# setup.py
# Copyright 2011 Roger Marsh
# Licence: See LICENCE (BSD licence)
"""chesstab setup file.

Retained so 'python setup.py ...' can be used by my build scripts until
conversion to 'python -m pip ...'.

All setup() arguments except dependency_links are set in setup.cfg file.
"""

from setuptools import setup
import configparser

if __name__ == "__main__":

    setup_args = {}

    # Derive dependency_links from install_requires for use by setup().
    # dependency_links is ignored by non-legacy pip commands; and these
    # packages have to be installed by separate commands quoting the URL
    # in the command line.  This code works because all version conditions
    # are '=='.
    parser = configparser.ConfigParser()
    parser.read("setup.cfg")
    for section in parser.sections():
        if section != "options":
            continue
        for key, value in parser.items(section):
            if key == "install_requires":
                install_requires = [v for v in value.splitlines() if v]
                setup_args["dependency_links"] = [
                    "-".join(required.split("==")).join(
                        ("http://solentware.co.uk/files/", ".tar.gz")
                    )
                    for required in install_requires
                ]
                break

    setup(**setup_args)
