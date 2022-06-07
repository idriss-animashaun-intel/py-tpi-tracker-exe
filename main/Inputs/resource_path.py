from pathlib import Path
import inspect

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    caller_path = inspect.stack()[1].filename
    path = Path(caller_path).parent / relative_path
    return str(path)
