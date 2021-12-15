from importlib.metadata import version

try:
    __version__ = version("eospyo")
except:  # NOQA: E722
    pass
