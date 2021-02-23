# setup.py
# Copyright 2011 Roger Marsh
# Licence: See LICENCE (BSD licence)

from setuptools import setup

if __name__ == '__main__':

    long_description = open('README').read()

    setup(
        name='chesstab',
        version='4.3',
        description='Database for chess games',
        author='Roger Marsh',
        author_email='roger.marsh@solentware.co.uk',
        url='http://www.solentware.co.uk',
        packages=[
            'chesstab',
            'chesstab.core', 'chesstab.basecore', 'chesstab.gui',
            'chesstab.help',
            'chesstab.db', 'chesstab.dpt', 'chesstab.sqlite', 'chesstab.apsw',
            'chesstab.unqlite', 'chesstab.vedis',
            'chesstab.gnu', 'chesstab.ndbm',
            'chesstab.fonts',
            'chesstab.tools',
            ],
        package_data={
            'chesstab.fonts': ['*.TTF', '*.zip'],
            'chesstab.help': ['*.rst', '*.html'],
            },
        long_description=long_description,
        license='BSD',
        classifiers=[
            'License :: OSI Approved :: BSD License',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Operating System :: OS Independent',
            'Topic :: Games/Entertainment :: Board Games',
            'Intended Audience :: End Users/Desktop',
            'Development Status :: 3 - Alpha',
            ],
        install_requires=[
            'solentware-base==4.1.2',
            'chessql==2.0',
            'solentware-grid==2.0',
            'pgn-read==2.0',
            'solentware-misc==1.2',
            'uci-net==1.2',
            ],
        dependency_links=[
            'http://solentware.co.uk/files/solentware-base-4.1.2.tar.gz',
            'http://solentware.co.uk/files/chessql-2.0.tar.gz',
            'http://solentware.co.uk/files/solentware-grid-2.0.tar.gz',
            'http://solentware.co.uk/files/pgn-read-2.0.tar.gz',
            'http://solentware.co.uk/files/solentware-misc-1.2.tar.gz',
            'http://solentware.co.uk/files/uci-net-1.2.tar.gz',
            ],
        )
