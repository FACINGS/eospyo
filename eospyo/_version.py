from importlib.metadata import version

DEPRECATION_WARNING = (
    "eospyo have been renamed! "
    "It won't be maintained nor receive security updates. "
    "Please install and use pyntelope instead: "
    "https://pypi.org/project/pyntelope/ "
)

try:
    __version__ = version("eospyo")
except:  # NOQA: E722
    pass
