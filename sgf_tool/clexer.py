import enum
import typing
from . import DynamicLibrary as dl
import os


class SGFTokenType(enum.Enum):
    LEFT_PAREN = 0
    RIGHT_PAREN = 1
    SEMICOLON = 2
    TAG = 3
    VALUE = 4
    IGNORE = 5
    END = 6
    NONE = 7


class SGFToken:
    def __init__(self, type: SGFTokenType, value: str, start: int, end: int):
        self.type = type
        self.value = value
        self.start = start
        self.end = end


# C++ implementation of SGFLexer
base_dir = os.path.dirname(os.path.abspath(__file__))
lib = dl.DynamicLibrary(extra_compile_flags=['-I' + base_dir])
lib.compile_string(
    r'''
#include "lexer.hpp"
#include <iostream>
#include <cstring>

API SGFToken* create_token() {
    return new SGFToken(SGFTokenType::NONE, "", 0, 0);
}

API void delete_token(SGFToken* token) {
    delete token;
}

API SGFLexer* create_lexer(const char* sgf, int start, void (*progress_callback)(int, int)) {
    return new SGFLexer(sgf, start, progress_callback);
}

API void delete_lexer(SGFLexer* lexer) {
    delete lexer;
}

API void next_token(SGFLexer* lexer, SGFToken* token) {
    auto& t = lexer->next_token();
    token->type = t.type;
    token->value = t.value;
    token->start = t.start;
    token->end = t.end;
}

API int get_token_type(SGFToken* token) {
    return static_cast<int>(token->type);
}

API size_t get_token_value_length(SGFToken* token) {
    return token->value.length();
}

API void get_token_value(SGFToken* token, char* buffer) {
    strcpy(buffer, token->value.c_str());
}

API int get_token_start(SGFToken* token) {
    return token->start;
}

API int get_token_end(SGFToken* token) {
    return token->end;
}

API void print_token(SGFToken* token) {
    std::cout << static_cast<int>(token->type) << " " << token->value << " " << token->start << " " << token->end << std::endl;
}
''', functions={
        'create_token': {'argtypes': [], 'restype': dl.void_p},
        'delete_token': {'argtypes': [dl.void_p], 'restype': dl.void},
        'create_lexer': {'argtypes': [dl.char_p, dl.int32, dl.void_p], 'restype': dl.void_p},
        'delete_lexer': {'argtypes': [dl.void_p], 'restype': dl.void},
        'next_token': {'argtypes': [dl.void_p, dl.void_p], 'restype': dl.void},
        'get_token_type': {'argtypes': [dl.void_p], 'restype': dl.int32},
        'get_token_value_length': {'argtypes': [dl.void_p], 'restype': dl.uint64},
        'get_token_value': {'argtypes': [dl.void_p, dl.int8_p], 'restype': dl.void},
        'get_token_start': {'argtypes': [dl.void_p], 'restype': dl.int32},
        'get_token_end': {'argtypes': [dl.void_p], 'restype': dl.int32},
        'print_token': {'argtypes': [dl.void_p], 'restype': dl.void},
    })


class SGFLexer:
    def __init__(self, sgf: str, start: int = 0, progress_callback: typing.Optional[typing.Callable[[int, int], None]] = None):
        self.length = len(sgf)
        self.token = lib.create_token()
        self.lexer = lib.create_lexer(sgf.encode(), start, 0)
        self.progress_callback = progress_callback

    def __del__(self):
        lib.delete_token(self.token)
        lib.delete_lexer(self.lexer)

    def next_token(self):
        lib.next_token(self.lexer, self.token)
        token_type = lib.get_token_type(self.token)
        value_length = lib.get_token_value_length(self.token)
        value = bytearray(value_length)
        lib.get_token_value(self.token, value)
        start = lib.get_token_start(self.token)
        end = lib.get_token_end(self.token)
        if self.progress_callback:
            self.progress_callback(end, self.length)
        return SGFToken(SGFTokenType(token_type), value.decode(), start, end)
