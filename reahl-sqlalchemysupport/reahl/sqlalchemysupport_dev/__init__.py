
from reahl.dev.fixtures import CleanDatabase
from reahl.tofu.nosesupport import set_run_fixture

set_run_fixture(CleanDatabase(None), locals())

