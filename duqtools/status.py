import duqtools.config
from pydantic import BaseModel
from logging import debug, info
from os import scandir, path
from pathlib import Path


class Status_config(BaseModel):
    msg_completed: str = "Status : Completed successfully"
    msg_failed: str = "Status : Failed"
    msg_running: str = "Status : Running"


def has_submit_script(dir):
    return (dir / cfg.submit.submit_script_name).exists()


def has_status(dir):
    return (dir / cfg.submit.status_file).exists()


def status_file_contains(dir, msg):
    sf = (dir / cfg.submit.status_file)
    with open(sf, "r") as f:
        content = f.read()
        debug("Checking if content of %s file: %s contains %s" %
              (sf, content, msg))
        return msg in content


def is_completed(dir):
    return status_file_contains(dir, cfg.status.msg_completed)


def is_failed(dir):
    return status_file_contains(dir, cfg.status.msg_failed)


def is_running(dir):
    return status_file_contains(dir, cfg.status.msg_running)


def status():
    global cfg
    cfg = duqtools.config.Config()
    if not cfg.submit:
        raise Exception("submit field required in config file")
    debug("Submit config: %s" % cfg.submit)

    dirs = [Path(entry) for entry in scandir(cfg.workspace) if entry.is_dir()]
    debug("Case directories: %s" % dirs)

    info("Total number of directories: %i" % len(dirs))

    dirs_submit = [dir for dir in dirs if has_submit_script(dir)]
    dirs_status = [dir for dir in dirs if has_status(dir)]

    dirs_completed = [dir for dir in dirs_status if is_completed(dir)]
    dirs_failed = [dir for dir in dirs_status if is_failed(dir)]
    dirs_running = [dir for dir in dirs_status if is_running(dir)]

    dirs_unknown = [dir for dir in dirs_status if not (dir in dirs_completed
                                                       or dir in dirs_failed
                                                       or dir in dirs_running)]

    info("Total number of directories with submission script : %i" %
         len(dirs_submit))
    info("      number of not submitted jobs                 : %i" %
         (len(dirs_submit)-len(dirs_status)))
    info("Total number of directories with status     script : %i" %
         len(dirs_status))
    info("Total number of directories with Completed status  : %i" %
         len(dirs_completed))
    info("Total number of directories with Failed    status  : %i" %
         len(dirs_failed))
    info("Total number of directories with Running   status  : %i" %
         len(dirs_running))
    info("Total number of directories with Unknown   status  : %i" %
         len(dirs_unknown))
