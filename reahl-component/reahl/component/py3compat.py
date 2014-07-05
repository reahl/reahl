
import six

def old_str(something):
    if six.PY2:
        return six.binary_type(something)
    return six.text_type(something)
