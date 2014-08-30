from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from __future__ import unicode_literals

import six

def old_str(something):
    if six.PY2:
        return something.encode('utf-8')
    return something
