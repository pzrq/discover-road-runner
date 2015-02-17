Discover Road Runner
====================

*Running tests should be a fun voyage of learning and discovery*


Another test runner?
--------------------

Yes. Why?

*   Maxim: Productivity
*   Maxim: App-based breakdown
*   Maxim: Multiprocessing by default

Features:

*   Traffic-light red / yellow / green feedback
*   Cyan for fast repro strings

Hence prioritised actionable information should be (reverse order to command line):

    1. Print overall
    2. Print last test failure
    3. Print minimal app-reproduction summary, i.e. failing apps on one line, i.e. ./manage.py test mathspace.blog mathspace.schools
    4. Print skipped tests apps on one line.
    5: Alphabetical order app summary.
    6. Print full test failures.

Take full control over DiscoverRunner output? Then I could print failures immediately rather than on app completion.
Definitely needs tests.


But please feel free to check out other awesome test runners:

* tox
* nose
* etc


Support
-------

Tested under OSX, Linux (Ubuntu). YMMV with other platforms.

Python 2.7+, 3.4+
Django 1.6.10+

Please feel free to open issues or contribute back patches via GitHub
`pull requests <https://help.github.com/articles/creating-a-pull-request/>`_.
