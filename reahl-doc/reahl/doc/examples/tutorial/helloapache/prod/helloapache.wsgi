
# Activate your virtual env
virtualenv_dir = u'/usr/local/helloapache/virtualenv'
activate_env="%s/bin/activate_this.py" % virtualenv_dir
execfile(activate_env, dict(__file__=activate_env))

from reahl.web.fw import ReahlWebApplication
application = ReahlWebApplication.from_directory('/etc/reahl.d/helloapache')
application.start()


