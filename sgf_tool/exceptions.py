class BaseSGFException(Exception):
    def __init__(self, message, start, end, detail=False, sgf=None, offset=20, highlight_start='\033[1;31m', highlight_end='\033[0m'):
        self.message = message
        self.start = start
        self.end = end
        self.detail = detail
        self.sgf = sgf
        self.offset = offset
        self.highlight_start = highlight_start
        self.highlight_end = highlight_end

    def __str__(self):
        if not self.detail:
            return f'{self.message} at {self.start}:{self.end}'
        else:
            if self.sgf is None:
                return f'{self.message} at {self.start}:{self.end}'
            s = max(0, self.start - self.offset)
            e = min(len(self.sgf), self.end + self.offset)
            return (
                f'{self.message} at {self.start}:{self.end}\n'
                f'{self.sgf[s:self.start]}{self.highlight_start}'
                f'{self.sgf[self.start:self.end]}{self.highlight_end}'
                f'{self.sgf[self.end:e]}'
            )


class LexicalError(BaseSGFException):
    pass


class SGFError(BaseSGFException):
    pass
