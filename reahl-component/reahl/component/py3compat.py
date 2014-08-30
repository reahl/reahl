from __future__ import print_function, unicode_literals, absolute_import, division

import six

def old_str(something):
    if six.PY2:
        return something.encode('utf-8')
    return something
