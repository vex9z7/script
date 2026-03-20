import fcntl


def acquire_lock(file_obj):
    fcntl.flock(file_obj.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def release_lock(file_obj):
    try:
        fcntl.flock(file_obj.fileno(), fcntl.LOCK_UN)
    except OSError:
        pass
