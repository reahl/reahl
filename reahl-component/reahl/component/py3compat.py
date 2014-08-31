from __future__ import print_function, unicode_literals, absolute_import, division

import six

def old_str(something):
    if six.PY2:
        return something.encode('utf-8')
    else:
        return something


def ascii_as_bytes_or_str(unicode_str):
    if six.PY2:
        return unicode_str.encode('ascii')
    else:
        return unicode_str


def _html_escape_function():
    if six.PY2:
        import cgi
        def html_escape(s, quote=True):
            return cgi.escape(s, quote=quote)
        return html_escape
    else:
        import html
        return html.escape


html_escape = _html_escape_function()
