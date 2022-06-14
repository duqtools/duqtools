import logging
from os import scandir
from pathlib import Path

from .config import Config as cfg

logger = logging.getLogger(__name__)


def has_submit_script(dir: Path) -> bool:
    """has_submit_script.

    Parameters
    ----------
    dir : Path
        dir

    Returns
    -------
    bool
    """
    return (dir / cfg().submit.submit_script_name).exists()


def has_status(dir: Path) -> bool:
    """has_status.

    Parameters
    ----------
    dir : Path
        dir

    Returns
    -------
    bool
    """
    return (dir / cfg().submit.status_file).exists()


def status_file_contains(dir: Path, msg) -> bool:
    """status_file_contains.

    Parameters
    ----------
    dir : Path
        dir
    msg :
        msg

    Returns
    -------
    bool
    """
    sf = (dir / cfg().submit.status_file)
    with open(sf, 'r') as f:
        content = f.read()
        logger.debug('Checking if content of %s file: %s contains %s' %
                     (sf, content, msg))
        return msg in content


def is_completed(dir: Path) -> bool:
    """is_completed.

    Parameters
    ----------
    dir : Path
        dir

    Returns
    -------
    bool
    """
    return status_file_contains(dir, cfg().status.msg_completed)


def is_failed(dir: Path) -> bool:
    """is_failed.

    Parameters
    ----------
    dir : Path
        dir

    Returns
    -------
    bool
    """
    return status_file_contains(dir, cfg().status.msg_failed)


def is_running(dir: Path) -> bool:
    """is_running.

    Parameters
    ----------
    dir : Path
        dir

    Returns
    -------
    bool
    """
    return status_file_contains(dir, cfg().status.msg_running)


def status(**kwargs):
    """status."""
    if not cfg().submit:
        raise Exception('submit field required in config file')
    logger.debug('Submit config: %s' % cfg().submit)

    dirs = [
        Path(entry) for entry in scandir(cfg().workspace) if entry.is_dir()
    ]
    logger.debug('Case directories: %s' % dirs)

    logger.info('Total number of directories: %i' % len(dirs))

    dirs_submit = [dir for dir in dirs if has_submit_script(dir)]
    dirs_status = [dir for dir in dirs if has_status(dir)]

    dirs_completed = [dir for dir in dirs_status if is_completed(dir)]
    dirs_failed = [dir for dir in dirs_status if is_failed(dir)]
    dirs_running = [dir for dir in dirs_status if is_running(dir)]

    dirs_unknown = [
        dir for dir in dirs_status if not (
            dir in dirs_completed or dir in dirs_failed or dir in dirs_running)
    ]

    logger.info('Total number of directories with submission script : %i' %
                len(dirs_submit))
    logger.info('      number of not submitted jobs                 : %i' %
                (len(dirs_submit) - len(dirs_status)))
    logger.info('Total number of directories with status     script : %i' %
                len(dirs_status))
    logger.info('Total number of directories with Completed status  : %i' %
                len(dirs_completed))
    logger.info('Total number of directories with Failed    status  : %i' %
                len(dirs_failed))
    logger.info('Total number of directories with Running   status  : %i' %
                len(dirs_running))
    logger.info('Total number of directories with Unknown   status  : %i' %
                len(dirs_unknown))
