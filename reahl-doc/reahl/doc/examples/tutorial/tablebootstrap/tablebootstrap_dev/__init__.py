from reahl.webdev.fixtures import BrowserSetup
from reahl.tofu.nosesupport import set_run_fixture

set_run_fixture(BrowserSetup(None), locals())
