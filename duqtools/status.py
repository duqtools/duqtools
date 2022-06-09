from logging import debug, info
from os import scandir
from pathlib import Path

from pydantic import BaseModel

import duqtools.config as config


class Status_config(BaseModel):
    """Status_config."""

    msg_completed: str = 'Status : Completed successfully'
    msg_failed: str = 'Status : Failed'
    msg_running: str = 'Status : Running'


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
    return (dir / config.Config().submit.submit_script_name).exists()


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
    return (dir / config.Config().submit.status_file).exists()


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
    sf = (dir / config.Config().submit.status_file)
    with open(sf, 'r') as f:
        content = f.read()
        debug('Checking if content of %s file: %s contains %s' %
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
    return status_file_contains(dir, config.Config().status.msg_completed)


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
    return status_file_contains(dir, config.Config().status.msg_failed)


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
    return status_file_contains(dir, config.Config().status.msg_running)


def status(**kwargs):
    """status."""
    cfg = config.Config()
    if not cfg.submit:
        raise Exception('submit field required in config file')
    debug('Submit config: %s' % cfg.submit)

    dirs = [Path(entry) for entry in scandir(cfg.workspace) if entry.is_dir()]
    debug('Case directories: %s' % dirs)

    info('Total number of directories: %i' % len(dirs))

    dirs_submit = [dir for dir in dirs if has_submit_script(dir)]
    dirs_status = [dir for dir in dirs if has_status(dir)]

    dirs_completed = [dir for dir in dirs_status if is_completed(dir)]
    dirs_failed = [dir for dir in dirs_status if is_failed(dir)]
    dirs_running = [dir for dir in dirs_status if is_running(dir)]

    dirs_unknown = [
        dir for dir in dirs_status if not (
            dir in dirs_completed or dir in dirs_failed or dir in dirs_running)
    ]

    info('Total number of directories with submission script : %i' %
         len(dirs_submit))
    info('      number of not submitted jobs                 : %i' %
         (len(dirs_submit) - len(dirs_status)))
    info('Total number of directories with status     script : %i' %
         len(dirs_status))
    info('Total number of directories with Completed status  : %i' %
         len(dirs_completed))
    info('Total number of directories with Failed    status  : %i' %
         len(dirs_failed))
    info('Total number of directories with Running   status  : %i' %
         len(dirs_running))
    info('Total number of directories with Unknown   status  : %i' %
         len(dirs_unknown))
