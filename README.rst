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

* Ironically DRR has no meta test suite to test the test suite is doing what
  it is supposed to be doing... hence no TravisCI, etc.
* If I get this far, should compare meta results against
  django.test.runner.py: DiscoverRunner for correctness.
* Sometimes fails to report results (3/70 apps on a specific large project),
  however it does report that it did not report results.
* Sometimes get "IOError: [Errno 32] Broken pipe"
  - not sure if its related to the OSX Python 2.7.6 with SQLite 3.8.5 crash
  or something different (that was fixed in SQLite 3.8.6_1).
  There's a Django issue for it somewhere...
* Inspect test suite to be run to determine if we can skip even setting up
  the databases saving another ~100ms?
* Only supports the SQLite3 `:memory:` backend.
  Should test against others or be clearer.
* Doesn't work nicely with coverage (requires running with `--concurrency=0`)
* Doesn't support fuzzy matching like tox does
* Probably won't work with TransactionTestCase
  (refer to bunch of hacks to save slow migrations, i.e. --ramdb)?
* If run for a single test_label, MARS should print the just the individual
  failing tests
* Remember and print slowest individual tests like the one I added to SymPy
  Original thought "Print 3 slowest tests and % of overall time taken."
* Investigate if it is worthwhile trade off to introspect an app for
  no or only SimpleTestCase(s) before setting up and tearing down the test DB.
  Could save like 100ms per affected app.
  https://docs.djangoproject.com/en/1.4/topics/testing/#django.test.SimpleTestCase
* --rerun=10 or --batch=10  # Run test labels 10x, need to think about name
* with self.subTest() in Python 3+?
