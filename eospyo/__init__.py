import logging

from . import exc, types
from ._version import DEPRECATION_WARNING, __version__
from .net import *  # NOQA: F403
from .transaction import *  # NOQA: F403

print(DEPRECATION_WARNING)
logging.warning(DEPRECATION_WARNING)
