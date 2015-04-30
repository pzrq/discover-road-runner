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
*   Fast repro strings - if you can't reproduce it, you can't fix it
*   Full stack trace as soon as that error occurs, without `--verbosity=2`
*   MARS: Minimal app reproduction summary, for faster copy/paste test repro

But please feel free to check out other awesome test runners:

* `tox <https://tox.readthedocs.org/en/latest/>`_
* `nose <http://nose.readthedocs.org/en/latest/index.html>`_
* `DiscoverRunner (built into Django) <https://docs.djangoproject.com/en/dev/topics/testing/advanced/#using-different-testing-frameworks>`_


Getting it
----------

pip install -e git+https://github.com/pzrq/discover-road-runner.git#egg=discover_road_runner

Then in your `settings.py` file::

    TEST_RUNNER = 'discover_road_runner.runners.DiscoverRoadRunner'


Settings
--------

Place in your `settings.py` file like every other Django setting.

*   `LOCAL_CACHE` - Path where `--ramdb` databases get stored.
    Defaults to `local_cache` inside your repository
    (you might wish to gitignore this).

*   `TEST_RUNNER_EXCLUDE_APPS` - setting to exclude problematic apps
    such as third party apps that don't play nice, or slow / god apps, e.g. ::

        TEST_RUNNER_EXCLUDE_APPS = (
            # Would like it if this ran faster,
            # trust the authors to get it right
            'django.contrib.auth',
        )

*   `TEST_RUNNER_RAMDB` - setting to work around PyCharm's test runner
    not allowing options like
    `--nomigrations <https://pypi.python.org/pypi/django-test-without-migrations/>`_
    or `--ramdb`::

        TEST_RUNNER_RAMDB = 'r123'


Support
-------

TODO: Add TravisCI integration to validate this all the time?

Tested under OSX, Linux (Ubuntu). YMMV with other platforms.

Python 2.7+, 3.4+
Django 1.6.10+

Please feel free to open issues or contribute back patches via GitHub
`pull requests <https://help.github.com/articles/creating-a-pull-request/>`_.


License
-------

TODO


Known issues
------------

* Only supports the SQLite3 `:memory:` backend.
* Incorrectly reporting OVERALL (run=0, ...) if running a single app.
* Does not tally expected failures / unexpected successes (yet!)
* Doesn't work nicely with coverage
* Doesn't support fuzzy matching like tox does
* Probably won't work with TransactionTestCase
* `./manage.py test typo` shouldn't print in nice green...
* If run for a single test_label, MARS should print the just the individual failing tests
* Ironically DRR has no meta test suite to test the test suite is doing what
  it is supposed to be doing...
