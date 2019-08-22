'''
Creates and tracks a lock file
'''
# import argparse
import errno
# import inspect
import os
import shutil
import sys
import time
from datetime import timedelta

LOCK_DEFAULT_MAX_AGE = timedelta(hours=2)


class LockedException(Exception):
    '''
    Exception raised when scoring harness is already running
    '''
    pass


def acquire_lock_or_fail(name, max_age=LOCK_DEFAULT_MAX_AGE):
    '''
    Acquire lock file or determine that lock file exists

    Args:
        name: Name of lock file
        max_age: The amount of time the lock file will live
    '''
    lock = Lock(name, max_age=max_age)
    if lock.acquire():
        return lock
    raise LockedException(f"A lock exists named {name} who's age is: {lock.get_age()}")


class Lock:
    """
    Implements a lock by making a directory named [lockname].lock
    """
    SUFFIX = 'lock'

    def __init__(self, name, directory=None, max_age=LOCK_DEFAULT_MAX_AGE):
        self.name = name
        self.held = False
        self.directory = directory if directory else os.path.dirname(os.path.abspath(__file__))
        self.lock_dir_path = os.path.join(self.directory,
                                          ".".join([name, Lock.SUFFIX]))
        self.max_age = max_age

    def get_age(self):
        '''
        Get amount of time lock file has existed in seconds
        '''
        age = timedelta(seconds=time.time() - os.path.getmtime(self.lock_dir_path))
        return age

    def acquire(self, break_old_locks=True):
        '''Try to acquire lock. Return True on success or False otherwise'''
        try:
            os.makedirs(self.lock_dir_path)
            self.held = True
            # Make sure the modification times are correct
            # On some machines, the modification time could be seconds off
            os.utime(self.lock_dir_path, (0, time.time()))
        except OSError as err:
            if err.errno != errno.EEXIST and err.errno != errno.EACCES:
                raise
            # already locked...
            if break_old_locks and self.get_age() > self.max_age:
                sys.stderr.write("Breaking lock who's age is: {}\n".format(
                    self.get_age()))
                self.held = True
                # Make sure the modification times are correct
                # On some machines, the modification time could be seconds off
                os.utime(self.lock_dir_path, (0, time.time()))
            else:
                self.held = False
        return self.held

    def release(self):
        """Release lock or do nothing if lock is not held"""
        if self.held:
            try:
                shutil.rmtree(self.lock_dir_path)
                self.held = False
            except OSError as err:
                if err.errno != errno.ENOENT:
                    raise


# def _sleep(seconds=0):
#     print("sleeping", seconds, "seconds")
#     for _ in range(seconds):
#         time.sleep(1)
#         sys.stdout.write('.')
#         sys.stdout.flush()
#     print("\ndone sleeping")


# def main():
#     lock = acquire_lock_or_fail('foo', max_age=timedelta(seconds=10))
#     try:
#         parser = argparse.ArgumentParser()

#         subparsers = parser.add_subparsers(title="subcommand")

#         parser_sleep = subparsers.add_parser('sleep')
#         parser_sleep.add_argument("seconds", type=int, default=0)
#         parser_sleep.set_defaults(func=_sleep)

#         args = parser.parse_args()

#         # get a subset of the dictionary containing just the arguments of func
#         arg_spec = inspect.getargspec(args.func)

#         args_for_func = {k: getattr(args, k) for k in arg_spec.args}

#         args.func(**args_for_func)

#     finally:
#         lock.release()

# if __name__ == "__main__":
#     main()
