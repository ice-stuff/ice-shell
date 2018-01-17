import os
import setuptools

setuptools.setup(
    # Metadata
    name='iCE_shell',
    version='2.1.0',
    author='George Lestaris',
    author_email='glestaris@gmail.com',
    description='Interactive cloud experiments and monitoring',

    # Packages
    packages=setuptools.find_packages(exclude=['test']),
    scripts=[
        os.path.join(os.path.dirname(__file__), 'bin', 'ice-shell'),
    ],

    # Dependencies
    install_requires=[
        'iCE>=2.1.1',
        'IPython>=5.1.0'
    ],

    # Configuration
    data_files=[
        (
            'etc/ice', [
                'config/default/ice.ini',
                'config/default/logging.ini'
            ]
        )
    ]
)
