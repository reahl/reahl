from reahl.web.fw import ReahlWebApplication
application = ReahlWebApplication.from_directory('/etc/reahl.d/hellonginx', dangerous_defaults_allowed=False)
application.start()

