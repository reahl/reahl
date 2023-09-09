#https://stackoverflow.com/questions/50174130/how-do-i-pytest-a-project-using-pep-420-namespace-packages
#https://github.com/pytest-dev/pytest/issues/6966
#For pytest >= 6.0 we need to fix a namespace issue. In some tests we create stub classes.
#The module path for these classes upon inspection seem to be sans the namespace prefix.
#The monkey patch below fixes the pytest issue

import re
from typing import Optional
import pathlib
import _pytest.pathlib

def apply_patch_for(root_dir_name):
    resolve_pkg_path_orig = _pytest.pathlib.resolve_package_path

    root_dir = pathlib.Path(root_dir_name).parent.resolve()
    namespace_pkg_dirs = [str(d) for d in root_dir.iterdir() if d.is_dir() and not (re.match(r'((^(\.|__))|.*egg-info$)', d.name)) ]

    def resolve_package_path(path: pathlib.Path) -> Optional[pathlib.Path]:
        result = resolve_pkg_path_orig(path)
        if result is None:
            result = path  
        for parent in result.parents:
            if str(parent) in namespace_pkg_dirs:
                return parent
        return None

    _pytest.pathlib.resolve_package_path = resolve_package_path


