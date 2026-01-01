#pragma once

#include "exceptions.hpp"
#include <functional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>

enum class SGFTokenType : int {
    LEFT_PAREN,
    RIGHT_PAREN,
    SEMICOLON,
    TAG,
    VALUE,
    IGNORE,
    ENDOFFILE,
    NONE,
};

class SGFToken {
public:
    SGFToken(SGFTokenType type, const std::string& value, int start, int end)
        : type(type), value(value), start(start), end(end) {}

    SGFTokenType type;
    std::string value;
    size_t start;
    size_t end;
};

class BaseInputStream {
public:
    virtual ~BaseInputStream() = default;
    virtual char peek() = 0;
    virtual char get() = 0;
    virtual void unget() = 0;
    virtual int tellg() = 0;
};

class StringInputStream : public BaseInputStream {
public:
    explicit StringInputStream(const std::string& s)
        : s(s), index(0) {}

    char peek() override
    {
        if (index >= s.length()) {
            return '\0';
        }
        return s[index];
    }

    char get() override
    {
        if (index >= s.length()) {
            return '\0';
        }
        return s[index++];
    }

    void unget() override
    {
        if (index > 0) {
            --index;
        }
    }

    int tellg() override
    {
        return index;
    }

private:
    std::string s;
    size_t index;
};

class SGFLexer {
public:
    SGFLexer(std::string sgf, size_t start = 0, std::function<void(int, int)> progress_callback = nullptr)
        : length(sgf.length()), input_stream(std::move(sgf)), last_token(SGFTokenType::NONE, "", start, start), progress_callback(std::move(progress_callback)) {}

    const SGFToken& next_token()
    {
        _next_token();
        if (last_token.type != SGFTokenType::ENDOFFILE && progress_callback) {
            progress_callback(input_stream.tellg(), length);
        }
        return last_token;
    }

    const SGFToken& current_token() const
    {
        return last_token;
    }

private:
    void _next_token()
    {
        while (true) {
            char c = input_stream.get();
            if (c == '\0') {
                last_token = SGFToken(SGFTokenType::ENDOFFILE, "", input_stream.tellg(), input_stream.tellg());
                return;
            }
            if (c == '(') {
                // return std::make_unique<SGFToken>(SGFTokenType::LEFT_PAREN, std::string(1, c), input_stream.tellg() - 1, input_stream.tellg());
                last_token = SGFToken(SGFTokenType::LEFT_PAREN, std::string(1, c), input_stream.tellg() - 1, input_stream.tellg());
                return;
            }
            if (c == ')') {
                // return std::make_unique<SGFToken>(SGFTokenType::RIGHT_PAREN, std::string(1, c), input_stream.tellg() - 1, input_stream.tellg());
                last_token = SGFToken(SGFTokenType::RIGHT_PAREN, std::string(1, c), input_stream.tellg() - 1, input_stream.tellg());
                return;
            }
            if (c == ';') {
                // return std::make_unique<SGFToken>(SGFTokenType::SEMICOLON, std::string(1, c), input_stream.tellg() - 1, input_stream.tellg());
                last_token = SGFToken(SGFTokenType::SEMICOLON, std::string(1, c), input_stream.tellg() - 1, input_stream.tellg());
                return;
            }
            if (c == '[') {
                std::string value;
                bool escape = false;
                while (true) {
                    c = input_stream.get();
                    if (c == '\0') {
                        throw LexicalError("Unexpected end of file", input_stream.tellg(), input_stream.tellg());
                    }
                    if (c == ']' && !escape) {
                        break;
                    }
                    if (c == '\\' && !escape) {
                        value += c; // Add the escape character
                        escape = true;
                        continue;
                    }
                    value += c;
                    escape = false;
                }
                // return std::make_unique<SGFToken>(SGFTokenType::VALUE, value, input_stream.tellg() - value.size() - 1, input_stream.tellg());
                last_token = SGFToken(SGFTokenType::VALUE, value, input_stream.tellg() - value.size() - 1, input_stream.tellg());
                return;
            }
            if (is_alnum(c) || c == '_') {
                std::string tag(1, c);
                while (true) {
                    c = input_stream.peek();
                    if (c == '\0' || !is_alnum(c) && c != '_') {
                        break;
                    }
                    tag += input_stream.get();
                }
                // return std::make_unique<SGFToken>(SGFTokenType::TAG, tag, input_stream.tellg() - tag.size(), input_stream.tellg());
                last_token = SGFToken(SGFTokenType::TAG, tag, input_stream.tellg() - tag.size(), input_stream.tellg());
                return;
            }
            if (isspace(c)) {
                continue; // Skip whitespace
            }
            throw LexicalError("Invalid character", input_stream.tellg() - 1, input_stream.tellg());
        }
    }

    static bool is_alnum(char c)
    {
        return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9');
    }

    int length;
    StringInputStream input_stream;
    SGFToken last_token;
    std::function<void(int, int)> progress_callback;
};
