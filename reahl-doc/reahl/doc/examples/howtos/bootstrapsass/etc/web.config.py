from reahl.web.libraries import LibraryIndex, JQuery, JsCookie, JQueryUI, Underscore, HTML5Shiv, IE9, Reahl, Holder, ReahlBootstrap4Additions

from reahl.doc.examples.howtos.bootstrapsass.bootstrapsass import ThemedUI, CompiledBootstrap


web.site_root = ThemedUI
web.frontend_libraries = LibraryIndex(JQuery(), JsCookie(), JQueryUI(), Underscore(), HTML5Shiv(), IE9(), Reahl(), Holder(),
                         CompiledBootstrap(), ReahlBootstrap4Additions())

