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
*   Cyan for fast repro strings - if you can't reproduce it, you can't fix it
*   Full stack trace as soon as that error occurs, without `--verbosity=2`
*   MARS: Minimal app reproduction summary, for faster copy/paste test repro
*   `TEST_RUNNER_EXCLUDE_APPS` - setting to exclude problematic apps
    such as third party apps that don't play nice, or slow / god apps, e.g. ::

        TEST_RUNNER_EXCLUDE_APPS = (
            # Would like it if this ran faster, assume everyone else tests it
            'django.contrib.auth',
        )

But please feel free to check out other awesome test runners:

* tox
* nose
* etc


Getting it
----------

pip install -e git+https://github.com/pzrq/discover-road-runner.git#egg=drr


Support
-------

TODO: Add TravisCI integration to validate this all the time?

Tested under OSX, Linux (Ubuntu). YMMV with other platforms.

Python 2.7+, 3.4+
Django 1.6.10+

Please feel free to open issues or contribute back patches via GitHub
`pull requests <https://help.github.com/articles/creating-a-pull-request/>`_.


Known issues
------------

* Doesn't work nicely with coverage
* Doesn't work nicely with PyCharm's unit test runner
* Doesn't support fuzzy matching like tox does
* `./manage.py test typo` shouldn't print in nice green...
