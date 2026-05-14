def bad_function(a, b, c, d, e, f, g):
    """A function with too many arguments and other issues."""
    try:
        for i in range(10):
            for j in range(10):
                for k in range(10):
                    if i > j:
                        pass
    except:
        pass


def no_docstring_function(x):
    return x * 2


class NoDocstringClass:
    def method_without_docs(self):
        pass
