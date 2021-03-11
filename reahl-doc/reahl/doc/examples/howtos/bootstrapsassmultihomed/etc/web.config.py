from reahl.web.libraries import Library, Bootstrap4, LibraryIndex, JQuery, JsCookie, JQueryUI, Underscore, HTML5Shiv, IE9, Reahl, Holder, Popper, ReahlBootstrap4Additions

from reahl.doc.examples.howtos.bootstrapsassmultihomed import ResponsiveUI, CompiledBootstrap


web.site_root = ResponsiveUI
web.frontend_libraries = LibraryIndex(JQuery(), JsCookie(), JQueryUI(), Underscore(), HTML5Shiv(), IE9(), Reahl(), Holder(),
                         CompiledBootstrap(), ReahlBootstrap4Additions())

