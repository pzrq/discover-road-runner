from celery import task
import time


def queue_tasks():
    for i in range(1, 21):
        build_text_file('file_{}.txt'.format(i))


@task
def build_text_file(file_name):
    with open(file_name, 'w') as out:
        print('building {}'.format(file_name))
        time.sleep(2)
        out.write('some text')
