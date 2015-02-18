from setuptools import find_packages, setup


install_requires = [
    'Django>=1.6.10',
    'billiard>=3.3.0.19',
    'termcolor>=1.1.0',
]


setup(
    name='Discover Road Runner',
    version='0.1',
    url='https://github.com/pzrq/discover-road-runner',
    author='Peter Schmidt',
    author_email='peter@peterjs.com',
    description=('Running tests should be a fun voyage of '
                 'learning and discovery. Built on the maxims of productivity, '
                 'the Django app and multiprocessing.'),
    license='',  # TODO: Investigate and specify licence
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    scripts=[],
    entry_points={},
    extras_require={},
    zip_safe=False,
    classifiers=[
        'Development Status :: 3 - Alpha',
        # 'Environment :: Web Environment',
        # 'Framework :: Django',
        'Intended Audience :: Developers',
        # 'License :: OSI Approved :: BSD License',  # TODO
        # 'Operating System :: OS Independent',  # TODO
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        # 'Topic :: Internet :: WWW/HTTP',
        # 'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        # 'Topic :: Internet :: WWW/HTTP :: WSGI',
        # 'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
