import ctypes
import enum
import re
from .exceptions import LexicalError
# from exceptions import LexicalError
import typing
from . import DynamicLibrary as dl
# import DynamicLibrary as dl
import os


class SGFTokenType(enum.Enum):
    LEFT_PAREN = 0
    RIGHT_PAREN = 1
    SEMICOLON = 2
    TAG = 3
    EMPTY_VALUE = 4
    VALUE = 5
    IGNORE = 6


SGFTokenRules = [
    (SGFTokenType.LEFT_PAREN, re.compile(r'\(')),
    (SGFTokenType.RIGHT_PAREN, re.compile(r'\)')),
    (SGFTokenType.SEMICOLON, re.compile(r';')),
    (SGFTokenType.TAG, re.compile(r'\w+')),
    (SGFTokenType.EMPTY_VALUE, re.compile(r'\[\]')),
    (SGFTokenType.VALUE, re.compile(r'\[[\S\s]*?[^\\]\]')),
    (SGFTokenType.IGNORE, re.compile(r'\s+')),
]


class SGFToken:
    def __init__(self, type: SGFTokenType, value: str, start: int, end: int):
        self.type = type
        self.value = value
        self.start = start
        self.end = end


class SGFLexer:
    def __init__(self, sgf: str, start: int = 0, progress_callback: typing.Optional[typing.Callable[[int, int], None]] = None):
        self.sgf = sgf
        self.index = start
        self.length = len(sgf)
        self.progress_callback = progress_callback

    def next_token(self):
        if self.index >= self.length:
            return None

        for token_type, pattern in SGFTokenRules:
            match = pattern.match(self.sgf, self.index)
            if match:
                value = match.group(0)
                token = SGFToken(token_type, value, self.index,
                                 self.index + len(value))
                self.index = token.end

                # track progress
                if self.progress_callback:
                    self.progress_callback(self.index, self.length)

                return token

        raise LexicalError('Invalid character', self.index,
                           self.index + 1, detail=True, sgf=self.sgf)


class BaseInputStream:
    def __init__(self):
        pass

    def peek(self) -> str:
        raise NotImplementedError()

    def get(self) -> str:
        raise NotImplementedError()

    def unget(self) -> None:
        raise NotImplementedError()

    def tellg(self) -> int:
        raise NotImplementedError()


class StringInputStream(BaseInputStream):
    def __init__(self, s: str):
        super().__init__()
        self.s = s
        self.index = 0

    def peek(self) -> str:
        if self.index >= len(self.s):
            return ''
        return self.s[self.index]

    def get(self) -> str:
        if self.index >= len(self.s):
            return ''
        c = self.s[self.index]
        self.index += 1
        return c

    def unget(self) -> None:
        self.index -= 1

    def tellg(self) -> int:
        return self.index


class SGFLexerManual:
    def __init__(self, sgf: str, start: int = 0, progress_callback: typing.Optional[typing.Callable[[int, int], None]] = None):
        self.length = len(sgf)
        self.input_stream = StringInputStream(sgf)
        self.progress_callback = progress_callback

    def next_token(self):
        token = self._next_token()
        if token is None:
            return None
        if self.progress_callback:
            self.progress_callback(self.input_stream.tellg(), self.length)
        return token

    def _next_token(self):
        while True:
            c = self.input_stream.get()
            if c == '':
                return None
            if c == '(':
                return SGFToken(SGFTokenType.LEFT_PAREN, c, self.input_stream.tellg() - 1, self.input_stream.tellg())
            if c == ')':
                return SGFToken(SGFTokenType.RIGHT_PAREN, c, self.input_stream.tellg() - 1, self.input_stream.tellg())
            if c == ';':
                return SGFToken(SGFTokenType.SEMICOLON, c, self.input_stream.tellg() - 1, self.input_stream.tellg())
            if c == '[':
                value = ''
                escape = False
                while True:
                    c = self.input_stream.get()
                    if c == '':
                        raise LexicalError('Unexpected end of file', self.input_stream.tellg(
                        ), self.input_stream.tellg(), detail=True)
                    if c == ']' and not escape:
                        break
                    if c == '\\' and not escape:
                        escape = True
                        continue
                    value += c
                    escape = False
                return SGFToken(SGFTokenType.VALUE, value, self.input_stream.tellg() - len(value) - 1, self.input_stream.tellg())
            if ord('a') <= ord(c) <= ord('z') or ord('A') <= ord(c) <= ord('Z') or ord('0') <= ord(c) <= ord('9') or c == '_':
                tag = c
                while True:
                    c = self.input_stream.peek()
                    if c == '':
                        break
                    if ord('a') <= ord(c) <= ord('z') or ord('A') <= ord(c) <= ord('Z') or ord('0') <= ord(c) <= ord('9') or c == '_':
                        tag += self.input_stream.get()
                    else:
                        break
                return SGFToken(SGFTokenType.TAG, tag, self.input_stream.tellg() - len(tag), self.input_stream.tellg())
            if c == ' ' or c == '\t' or c == '\n' or c == '\r':
                continue
            raise LexicalError('Invalid character', self.input_stream.tellg(
            ) - 1, self.input_stream.tellg(), detail=True)
