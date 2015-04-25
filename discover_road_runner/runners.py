import sys

# queue.Empty seems to have moved
if sys.version_info[0] >= 3:
    import queue
else:
    from multiprocessing import queues as queue

import time
import unittest
from multiprocessing import Process, Queue
from optparse import make_option

from billiard import cpu_count
from django.conf import settings
from django.db import connections
from django.db.backends import BaseDatabaseWrapper
from django.db.models import get_apps
from django.test.runner import DiscoverRunner
from termcolor import colored


class DiscoverRoadRunner(DiscoverRunner):
    option_list = DiscoverRunner.option_list + (
        make_option(
            '-c', '--concurrency',
            action='store', dest='concurrency', default=None,
            help='Number of additional parallel processes to run. '
                 '--concurrency=0 is thus special - it means run in the '
                 'same Python process.'),
    )

    def __init__(self, concurrency, *args, **kwargs):
        if concurrency is None or int(concurrency) < 0:
            concurrency = cpu_count()
        self.concurrency = int(concurrency)
        self.stream = sys.stderr
        self.original_stream = self.stream
        super(DiscoverRoadRunner, self).__init__(*args, **kwargs)

    @staticmethod
    def get_apps_after_exclusions():
        """
        Lists all apps in the active Django project, but excluding any
        listed in ``TEST_RUNNER_EXCLUDE_APPS``.
        """
        exclude_apps = getattr(settings, 'TEST_RUNNER_EXCLUDE_APPS', ())
        excluded_names = ['%s.models' % app for app in exclude_apps]
        is_not_excluded = lambda app: app.__name__ not in excluded_names
        return filter(is_not_excluded, get_apps())

    def run_suite(self, suite, **kwargs):

        class HijackTextTestResult(unittest.TextTestResult):

            @staticmethod
            def repro(test):
                """
                String designed to be copied and pasted
                directly after `manage.py test`.
                """
                fast_repro = '.'.join((
                    test.__module__,
                    test.__class__.__name__,
                    test._testMethodName,
                ))
                return colored(fast_repro, 'red')

            def addError(self, test, err):
                super(HijackTextTestResult, self).addError(test, err)
                write = self._original_stderr.write
                error_str = self._exc_info_to_string(err, test)
                write('\n%s %s' % ('ERROR:', self.repro(test)))
                write('\n%s' % error_str)

            def addFailure(self, test, err):
                super(HijackTextTestResult, self).addFailure(test, err)
                write = self._original_stderr.write
                error_str = self._exc_info_to_string(err, test)
                write('\n%s %s' % ('FAIL:', self.repro(test)))
                write('\n%s' % error_str)

        class HijackMoreOutputTestRunner(unittest.TextTestRunner):
            resultclass = HijackTextTestResult

        class HijackUnitTestOutput(object):
            """
            Modify unit test output so only the valuable actionable information
            is printed to the stream, as soon as it is known,
            to boost developer productivity.
            """

            def __init__(self, original_stream):
                self.original_stream = original_stream

            def flush(self):
                pass

            def write(self, string):
                pass

            def writeln(self, string):
                pass

        if kwargs.get('stream', None):
            self.stream = HijackUnitTestOutput(self.original_stream)

        # Need to pass the stream in to silence the output,
        # then use the result to print relevant output fast
        return HijackMoreOutputTestRunner(
            stream=self.stream,
            verbosity=self.verbosity,
            failfast=self.failfast,
        ).run(suite)

    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        start = time.time()
        if not test_labels:
            # If no test labels were provided, provide them
            # and remove our custom exclusions
            test_labels = [
                # Don't double-discover tests?
                app.__name__.replace('.models', '')
                for app in self.get_apps_after_exclusions()
            ]
            # Hide most of the test output so we can focus on failures,
            # unless the user wanted to see the full output per app.
            if self.verbosity == 1:
                self.verbosity = 0

        self.setup_test_environment()

        # Prepare (often many) test suites to be run across multiple processes
        # suite = self.build_suite(test_labels, extra_tests)
        processes = []
        source_queue = Queue(maxsize=len(test_labels) + 1)

        for label in test_labels:
            suite = self.build_suite([label])
            source_queue.put((label, suite))
        if extra_tests:
            source_queue.put(
                ('extra_tests', self.build_suite(None, extra_tests))
            )

        # Run slow migrations first, then copy resulting DB later
        # to get most of the performance boost in downstream projects
        old_config = self.setup_databases()
        queries = []
        for database_wrapper in connections.all():
            queries.append(
                ''.join(line
                        for line in database_wrapper.connection.iterdump())
            )
            # Work around :memory: in django/db/backends/sqlite3/base.py
            BaseDatabaseWrapper.close(database_wrapper)

        result_queue = Queue(maxsize=len(test_labels) + 1)
        process_args = (self, source_queue, result_queue, queries)
        for _ in range(min(self.concurrency, len(test_labels))):
            p = Process(target=multi_proc_run_tests, args=process_args)
            p.start()
            processes.append(p)
        else:
            # Concurrency == 0 - run in same process
            multi_proc_run_tests(*process_args)

        for p in processes:
            p.join()

        results = []
        while not result_queue.empty():
            results.append(result_queue.get())

        mars = [
            r['test_label']
            for r in results
            if r['fail_count'] or r['error_count']
        ]
        skippy = [
            r['test_label']
            for r in results
            if r['skip_count'] and r['test_label'] not in mars
        ]
        if mars or skippy:
            line = ''.join((
                '---Copy/Paste-after-manage-py-test---',
                colored('Skipped', 'yellow'),
                '-or-',
                colored('MARS', 'red'),
                '-' * 28,
            ))
            print(line)
            if skippy:
                print(colored(' '.join(skippy), 'yellow'))
            if mars:
                print(colored(' '.join(mars), 'red'))

        merged = {
            'test_label': 'OVERALL',
            'run': sum([r['run'] for r in results]),
            'fail_count': sum([r['fail_count'] for r in results]),
            'error_count': sum([r['error_count'] for r in results]),
            'skip_count': sum([r['skip_count'] for r in results]),
        }
        merged['short_summary'] = build_short_summary(merged)
        end = time.time()
        merged['took'] = end - start

        final_result = ''.join((
            '_  \~ ', '-meep-meep', '-' * 64, '\n',
            ' `=/  ', build_message(merged), '\n',
            '~` `~ ', '-' * 74,
        ))
        msg = colored(final_result, color=get_colour(merged), attrs=['bold'])
        print(msg)
        self.teardown_databases(old_config)
        self.teardown_test_environment()


def build_short_summary(extra_msg_dict):
    short_summary = []
    failed = extra_msg_dict['fail_count']
    errored = extra_msg_dict['error_count']
    skipped = extra_msg_dict['skip_count']
    if failed:
        short_summary.append('failures=%s' % failed)
    if errored:
        short_summary.append('errors=%s' % errored)
    if skipped:
        short_summary.append('skipped=%s' % skipped)
    if short_summary:
        # Add extra , into printed message formatting
        short_summary.append('')
    return ', '.join(short_summary)


def extra_msg_dict_from(test_label, result):
    # Add some often useful details into the message
    extra_msg_dict = {
        'test_label': test_label,
        'run': result.testsRun,
        'fail_count': len(result.failures),
        'error_count': len(result.errors),
        'skip_count': len(result.skipped),
    }
    extra_msg_dict['short_summary'] = build_short_summary(extra_msg_dict)
    return extra_msg_dict


def get_colour(extra_msg_dict):
    if extra_msg_dict['error_count'] or extra_msg_dict['fail_count']:
        colour = 'red'
    elif extra_msg_dict['skip_count']:
        colour = 'yellow'
    else:
        colour = 'green'
    return colour


def build_message(extra_msg_dict):
    msg = (
        '{test_label} '
        '(run={run}, '
        '{short_summary}'
        'took={took:.3f}s)'
    ).format(**extra_msg_dict)
    return msg


def multi_proc_run_tests(pickled_self, source_queue, result_queue, queries):
    """
    This is a version of `DiscoverRunner.run_tests` that is written to be
    run as a single thread, but run in parallel with other test processes.
    It has also been augmented to provide informative breakdowns for each of
    the test_label(s) placed into the source_queue.
    """
    # Get any test apps / labels in the source_queue until it is empty
    while True:
        try:
            test_label, suite = source_queue.get(block=False)
        except queue.Empty:
            return

        # Set up and run the suite, capturing most of the stream output
        # Printing here can't be made atomic cleanly at verbosity >= 2,
        # i.e. without hacks I don't want to do and it's off the default flows
        start = time.time()

        # Can't safely setup_databases until after suites have been built
        create_cloned_sqlite_db(queries)

        stream = getattr(pickled_self, 'stream', sys.stderr)
        result = pickled_self.run_suite(suite, stream=stream)

        # Build the final message
        extra_msg_dict = extra_msg_dict_from(test_label, result)
        end = time.time()
        extra_msg_dict['took'] = end - start
        msg = build_message(extra_msg_dict)
        msg_coloured = colored(msg, color=get_colour(extra_msg_dict))
        full_msg = msg_coloured

        # Only one print statement so it is atomic
        # i.e. no annoying interleaving of test output should be possible
        print(full_msg)

        result_queue.put(extra_msg_dict)


def create_cloned_sqlite_db(queries):
    """
    Magic. Inspired by:
    http://stackoverflow.com/questions/8045602/how-can-i-copy-an-in-memory-sqlite-database-to-another-in-memory-sqlite-database
    """
    for query_list, database_wrapper in zip(queries, connections.all()):
        # Work around :memory: in django/db/backends/sqlite3/base.py
        BaseDatabaseWrapper.close(database_wrapper)

        cursor = database_wrapper.cursor()
        for sql in query_list.split(';'):
            sql += ';'
            cursor.execute(sql)
        database_wrapper.connection.commit()
