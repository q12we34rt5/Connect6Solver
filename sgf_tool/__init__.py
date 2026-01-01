from .parser import NodeAllocator, SGFParser
from .lexer import SGFToken, SGFTokenType, SGFLexer
from .node import BaseSGFNode, SGFNode
from .exceptions import LexicalError, SGFError
from . import utils
from . import games
import warnings

try:
    from . import cparser
except ImportError:
    warnings.warn("Failed to import cparser", ImportWarning)
    cparser = None
