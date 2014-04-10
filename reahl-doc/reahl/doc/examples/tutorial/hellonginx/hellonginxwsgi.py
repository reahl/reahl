from reahl.web.fw import ReahlWebApplication
application = ReahlWebApplication.from_directory('/etc/reahl.d/hellonginx')
application.start()

