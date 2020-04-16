from bowler import Query
import sys



def inline(node, capture, filename):
    print(type(node))
    print(type(capture))
    return capture.get('function_arguments')

(
    Query(""+sys.argv[1])
    .select_function('ascii_as_bytes_or_str')
    .modify(inline)
    .execute(interactive = True)
)
