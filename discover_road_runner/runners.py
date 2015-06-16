import os
import subprocess
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
from django import VERSION as DJANGO_VERSION
from django.conf import settings
from django.db import connections

if DJANGO_VERSION[1] >= 8:
    from django.db.backends.base.base import BaseDatabaseWrapper
else:
    from django.db.backends import BaseDatabaseWrapper

from django.db.models import get_apps
from django.test.runner import DiscoverRunner, dependency_ordered
from termcolor import colored


class DiscoverRoadRunner(DiscoverRunner):

    @classmethod
    def add_arguments(cls, parser):
        super(DiscoverRoadRunner, cls).add_arguments(parser)
        parser.add_argument(
            '-c', '--concurrency',
            action='store', dest='concurrency', default=None,
            help='Number of additional parallel processes to run. '
                 '--concurrency=0 is thus special - it means run in the '
                 'same Python process.',
        )
        parser.add_argument(
            '-m', '--ramdb', action='store', dest='ramdb', default='',
            help='Preserve the :memory:, '
                 'or RAM test database between runs.'
        )
    if DJANGO_VERSION[1] < 8:
        option_list = DiscoverRunner.option_list + (
            make_option(
                '-c', '--concurrency',
                action='store', dest='concurrency', default=None,
                help='Number of additional parallel processes to run. '
                     '--concurrency=0 is thus special - it means run in the '
                     'same Python process.'),
            make_option(
                '-m', '--ramdb', action='store', dest='ramdb', default='',
                help='Preserve the :memory:, '
                     'or RAM test database between runs.')
        )
    DEFAULT_TAG_HASH = 'default'

    def __init__(self, *args, **options):
        concurrency = options.get('concurrency', 0)
        if concurrency is None or int(concurrency) < 0:
            concurrency = cpu_count()
        self.concurrency = int(concurrency)
        self.stream = sys.stderr
        self.original_stream = self.stream
        try:
            self.ramdb = settings.TEST_RUNNER_RAMDB
        except AttributeError:
            self.ramdb = options.get('ramdb', '')
        try:
            save = settings.LOCAL_CACHE
        except AttributeError:
            save = 'local_cache'
        self.ramdb_saves = os.path.join(os.getcwd(), save)
        super(DiscoverRoadRunner, self).__init__(*args, **options)

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

    @classmethod
    def get_source_control_tag_hash(cls):
        try:
            # Try git
            out = subprocess.Popen(
                ['git', 'describe', '--always'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            tag_hash = out.communicate()[0]
            return tag_hash.decode('utf8').strip()
        except OSError:
            pass

        try:
            # Try hg
            # http://stackoverflow.com/questions/6693209/is-there-an-equivalent-to-gits-describe-function-for-mercurial
            out = subprocess.Popen(
                ['hg', 'log', '-r' '.' '--template',
                 "'{latesttag}-{latesttagdistance}-{node|short}\n'"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            tag_hash = out.communicate()[0]
            return tag_hash.decode('utf8').strip()
        except OSError:
            pass

        return cls.DEFAULT_TAG_HASH

    def get_db_path(self, db_name, tag_hash):
        return os.path.join(self.ramdb_saves, tag_hash, db_name + '.sql')

    def db_file_paths(self):
        return [
            self.get_db_path(db_name, tag_hash=self.ramdb)
            for db_name in settings.DATABASES
        ]

    def db_files_exist(self):
        return all(
            os.path.exists(db_path)
            for db_path in self.db_file_paths()
        )

    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        extra = 1 if extra_tests else 0
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
        source_queue = Queue(maxsize=len(test_labels) + extra)

        for label in test_labels:
            suite = self.build_suite([label])
            source_queue.put((label, suite))
        if extra_tests:
            source_queue.put(
                ('extra_tests', self.build_suite(None, extra_tests))
            )

        if self.ramdb and self.db_files_exist():
            # Have run before, reuse the RAM DB.
            in_files = self.db_file_paths()
            print('Reusing database files: \n{}'.format('\n'.join(in_files)))
            queries = []
            for in_file_name in in_files:
                with open(in_file_name) as infile:
                    queries.append('\n'.join(infile.readlines()))
            if DJANGO_VERSION[1] >= 7:
                hijack_setup_databases(self.verbosity, self.interactive)
            else:
                self.setup_databases()
        else:
            start = time.time()
            tag_hash = self.get_source_control_tag_hash()
            if tag_hash == self.DEFAULT_TAG_HASH:
                print('git or hg source control not found, '
                      'only most recent migration saved')
            print('Running (often slow) migrations... \n'
                  'Hint: Use --ramdb={} to reuse the final stored SQL later.'
                  .format(tag_hash))
            tag_hash = os.path.join(self.ramdb_saves, tag_hash)
            if not os.path.exists(tag_hash):
                os.makedirs(tag_hash)
            # Only run the slow migrations if --ramdb is not specified,
            # or running for first time
            old_config = self.setup_databases()
            queries = []
            for database_wrapper in connections.all():
                connection = database_wrapper.connection
                sql = '\n'.join(line for line in connection.iterdump())
                queries.append(sql)
                # Work around :memory: in django/db/backends/sqlite3/base.py
                BaseDatabaseWrapper.close(database_wrapper)
                mem, db_name = database_wrapper.creation.test_db_signature()
                with open(self.get_db_path(db_name, tag_hash), 'w') as outfile:
                    outfile.write(sql)
            self.teardown_databases(old_config)
            msg = 'Setup, migrations, ... completed in {:.3f} seconds'.format(
                time.time() - start
            )
            print(msg)

        result_queue = Queue(maxsize=len(test_labels) + extra)
        process_args = (self, source_queue, result_queue, queries)
        for _ in range(min(self.concurrency, len(test_labels) + extra)):
            p = Process(target=multi_proc_run_tests, args=process_args)
            p.start()
            processes.append(p)
        else:
            # Concurrency == 0 - run in same process
            multi_proc_run_tests(*process_args)

        for p in processes:
            p.join()

        results = []
        retrieved_labels = []
        while not result_queue.empty():
            retrieved_label, result = result_queue.get()
            results.append(result)
            retrieved_labels.append(retrieved_label)
        not_covered = set(test_labels) - set(retrieved_labels)
        if not_covered:
            msg = (
                'Tests that did not return results under --concurrency={} '
                '(try running separately, or with --concurrency=0): {}'.format(
                    self.concurrency,
                    ' '.join(sorted(not_covered)),
                ))
            print(msg)

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
            'expected_fail_count': sum([r['expected_fail_count'] for r in results]),
            'unexpected_success_count': sum([r['unexpected_success_count'] for r in results]),
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
        self.teardown_test_environment()


def build_short_summary(extra_msg_dict):
    short_summary = []
    failed = extra_msg_dict['fail_count']
    errored = extra_msg_dict['error_count']
    skipped = extra_msg_dict['skip_count']
    expected_fail = extra_msg_dict['expected_fail_count']
    unexpected_success = extra_msg_dict['unexpected_success_count']
    if failed:
        short_summary.append('failures=%s' % failed)
    if errored:
        short_summary.append('errors=%s' % errored)
    if skipped:
        short_summary.append('skipped=%s' % skipped)
    if expected_fail:
        short_summary.append('expected failures=%s' % expected_fail)
    if unexpected_success:
        short_summary.append('unexpected successes=%s' % unexpected_success)
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
        'expected_fail_count': len(result.expectedFailures),
        'unexpected_success_count': len(result.unexpectedSuccesses),
    }
    extra_msg_dict['short_summary'] = build_short_summary(extra_msg_dict)
    return extra_msg_dict


def get_colour(extra_msg_dict):
    if extra_msg_dict['error_count'] or extra_msg_dict['fail_count']:
        colour = 'red'
    elif (extra_msg_dict['skip_count'] or
          extra_msg_dict['expected_fail_count'] or
          extra_msg_dict['unexpected_success_count']):
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

        result_queue.put((test_label, extra_msg_dict))


def create_cloned_sqlite_db(queries):
    """
    Magic. Inspired by:
    http://stackoverflow.com/questions/8045602/how-can-i-copy-an-in-memory-sqlite-database-to-another-in-memory-sqlite-database
    http://stackoverflow.com/questions/8242837/django-multiprocessing-and-database-connections
    """
    for query_list, database_wrapper in zip(queries, connections.all()):
        # Work around :memory: in django/db/backends/sqlite3/base.py
        BaseDatabaseWrapper.close(database_wrapper)

        cursor = database_wrapper.cursor()
        for sql in query_list.split(';'):
            sql += ';'
            cursor.execute(sql)
        database_wrapper.connection.commit()


def hijack_setup_databases(verbosity, interactive, **kwargs):
    from django.db import connections, DEFAULT_DB_ALIAS

    # First pass -- work out which databases actually need to be created,
    # and which ones are test mirrors or duplicate entries in DATABASES
    mirrored_aliases = {}
    test_databases = {}
    dependencies = {}
    default_sig = connections[DEFAULT_DB_ALIAS].creation.test_db_signature()
    for alias in connections:
        connection = connections[alias]
        test_settings = connection.settings_dict['TEST']
        if test_settings['MIRROR']:
            # If the database is marked as a test mirror, save
            # the alias.
            mirrored_aliases[alias] = test_settings['MIRROR']
        else:
            # Store a tuple with DB parameters that uniquely identify it.
            # If we have two aliases with the same values for that tuple,
            # we only need to create the test database once.
            item = test_databases.setdefault(
                connection.creation.test_db_signature(),
                (connection.settings_dict['NAME'], set())
            )
            item[1].add(alias)

            if 'DEPENDENCIES' in test_settings:
                dependencies[alias] = test_settings['DEPENDENCIES']
            else:
                if alias != DEFAULT_DB_ALIAS and connection.creation.test_db_signature() != default_sig:
                    dependencies[alias] = test_settings.get('DEPENDENCIES', [DEFAULT_DB_ALIAS])

    # Second pass -- actually create the databases.
    old_names = []
    mirrors = []

    for signature, (db_name, aliases) in dependency_ordered(
            test_databases.items(), dependencies):
        test_db_name = None
        # Actually create the database for the first connection
        for alias in aliases:
            connection = connections[alias]
            if test_db_name is None:

                # TODO: ALL I WANT TO HIJACK IS THIS SO I CAN
                # TODO: ... SKIP SLOW call_command('migrations', ...)
                # TODO: ... replacing it with my faster version if on 2nd run

                c_self = connection.creation
                # test_db_name = connection.creation.create_test_db(
                test_database_name = c_self._create_test_db(
                    verbosity,
                    autoclobber=not interactive,
                    # TODO: This probably means I don't need other TODOs for TransactionTestCase...
                    # serialize=connection.settings_dict.get("TEST", {}).get("SERIALIZE", True),
                )
                c_self.connection.close()
                settings.DATABASES[c_self.connection.alias]["NAME"] = test_database_name
                c_self.connection.settings_dict["NAME"] = test_database_name
                destroy = True
            else:
                connection.settings_dict['NAME'] = test_db_name
                destroy = False
            old_names.append((connection, db_name, destroy))

    for alias, mirror_alias in mirrored_aliases.items():
        mirrors.append((alias, connections[alias].settings_dict['NAME']))
        connections[alias].settings_dict['NAME'] = (
            connections[mirror_alias].settings_dict['NAME'])

    return old_names, mirrors
