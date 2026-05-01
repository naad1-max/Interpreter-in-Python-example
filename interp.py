"""PGL Interpreter built for parsing (.mol files)
Source:
PRINT 'Hello, World!'
Math 2 + 3
"""

import string

# Errors

class Error:
    def __init__(self, line, col, error):
        self.line  = line
        self.col   = col
        self.error = error

    def __repr__(self):
        return f"Line {self.line}, Col {self.col}\n\033[1;31m{self.error}\033[0m"


# Position

class Position:
    def __init__(self, idx, line, col, source):
        self.idx     = idx
        self.line    = line
        self.col     = col
        self.source  = source

    def advance(self, current_char=None):
        self.idx += 1
        self.col += 1
        if current_char == "\n":
            self.line += 1
            self.col = 0


# Tokens

class Token:
    def __init__(self, type_, value=None):
        self.type   = type_
        self.value  = value

    def __repr__(self):
        return f"{self.type}:{self.value}" if self.value is not None else self.type


NUMBERS = string.digits
LETTERS = string.ascii_letters + "_"
ALPHANUM = LETTERS + NUMBERS

PRINT       = "PRINT"
STRING      = "STRING"
MATH        = "MATH"
NUM         = "NUM"
PLUS        = "PLUS"
MINUS       = "MINUS"
MUL         = "MUL"
DIV         = "DIV"
EOP         = "EOP" # End Of Program
IDENTIFIER  = "IDENTIFIER"
ASSIGN      = "ASSIGN"
LPAREN      = "LPAREN"
RPAREN      = "RPAREN"

# Tokenizer

class Tokenizer:
    def __init__(self, source):
        self.source        = source
        self.pos           = Position(-1, 0, -1, self.source)
        self.current_char  = None
        self.advance()

    def advance(self):
        self.pos.advance(self.current_char)
        if self.pos.idx < len(self.source):
            self.current_char = self.source[self.pos.idx]
        else:
            self.current_char = None

    def tokenize(self):
        tokens = []

        while self.current_char is not None:
            if self.current_char in " \t":
                self.advance()

            elif self.current_char == "\n":
                self.advance()

            elif self.current_char in LETTERS:
                ident = ""
                while self.current_char and self.current_char in ALPHANUM:
                    ident += self.current_char
                    self.advance()

                if ident == "PRINT":
                    tokens.append(Token(PRINT))
                    while self.current_char == " ":
                        self.advance()

                    if self.current_char != "'":
                        return [], Error(self.pos.line, self.pos.col, "Expected quote after PRINT")

                    self.advance()
                    start = self.pos.idx

                    while self.current_char and self.current_char != "'":
                        self.advance()

                    if self.current_char != "'":
                        return [], Error(self.pos.line, self.pos.col, "Unclosed string")

                    string_value = self.source[start:self.pos.idx]
                    tokens.append(Token(STRING, string_value))
                    self.advance()

                elif ident == "MATH":
                    tokens.append(Token(MATH))

                else:
                    tokens.append(Token(IDENTIFIER, ident))

            elif self.current_char in NUMBERS:
                num_str = ""
                while self.current_char and self.current_char in NUMBERS:
                    num_str += self.current_char
                    self.advance()
                tokens.append(Token(NUM, int(num_str)))

            elif self.current_char == "+":
                tokens.append(Token(PLUS))
                self.advance()

            elif self.current_char == "-":
                tokens.append(Token(MINUS))
                self.advance()

            elif self.current_char == "*":
                tokens.append(Token(MUL))
                self.advance()

            elif self.current_char == "/":
                tokens.append(Token(DIV))
                self.advance()

            elif self.current_char == "=":
                tokens.append(Token(ASSIGN))
                self.advance()

            elif self.current_char == "(":
                tokens.append(Token(LPAREN))
                self.advance()

            elif self.current_char == ")":
                tokens.append(Token(RPAREN))
                self.advance()

            else:
                return [], Error(self.pos.line, self.pos.col, f"Token not recognised: {self.current_char}")

        tokens.append(Token(EOP))
        return tokens, None


# Nodes

class ASTNode:
    pass


class Program(ASTNode):
    def __init__(self, statements):
        self.statements = statements


class PrintNode(ASTNode):
    def __init__(self, expr):
        self.expr = expr


class StringNode(ASTNode):
    def __init__(self, value):
        self.value = value


class MathNode(ASTNode):
    def __init__(self, expr):
        self.expr = expr


class NumberNode(ASTNode):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return str(self.value)


class BinOpNode(ASTNode):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right


class VarAssignNode(ASTNode):
    def __init__(self, name, value):
        self.name = name
        self.value = value


class VarAccessNode(ASTNode):
    def __init__(self, name):
        self.name = name


# Parser

class Parser:
    def __init__(self, tokens):
        self.idx = -1
        self.tokens = tokens
        self.advance()

    def advance(self):
        self.idx += 1
        if self.idx < len(self.tokens):
            self._current = self.tokens[self.idx]
        else:
            self._current = None
        return self._current

    @property
    def current(self):
        return self._current

    def parse_factor(self):
        token = self.current

        if token.type == NUM:
            self.advance()
            return NumberNode(token.value)

        elif token.type == IDENTIFIER:
            self.advance()
            return VarAccessNode(token.value)

        elif token.type == LPAREN:
            self.advance()
            expr = self.parse_expr()
            if self.current.type != RPAREN:
                raise Exception("Expected ')'")
            self.advance()
            return expr

        return None

    def parse_term(self):
        left = self.parse_factor()

        while self.current and self.current.type in (MUL, DIV):
            op = self.current
            self.advance()
            right = self.parse_factor()
            left = BinOpNode(left, op, right)

        return left

    def parse_expr(self):
        left = self.parse_term()

        while self.current and self.current.type in (PLUS, MINUS):
            op = self.current
            self.advance()
            right = self.parse_term()
            left = BinOpNode(left, op, right)

        return left

    def parse_statement(self):
        token = self.current

        if token.type == PRINT:
            self.advance()
            string_token = self.current
            self.advance()
            return PrintNode(StringNode(string_token.value))

        elif token.type == MATH:
            self.advance()
            expr = self.parse_expr()
            return MathNode(expr)

        elif token.type == IDENTIFIER:
            name = token.value
            self.advance()

            if self.current and self.current.type == ASSIGN:
                self.advance()
                expr = self.parse_expr()
                return VarAssignNode(name, expr)

            return VarAccessNode(name)

        return None

    def parse(self):
        statements = []

        while self.current and self.current.type != EOP:
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)

        return Program(statements)


# Interpreter

class Interpreter:
    def __init__(self):
        self.variables = {}

    def visit(self, node):
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, self.no_visit_method)
        return method(node)

    def no_visit_method(self, node):
        print(f"\033[1;31mNo visit method for {type(node).__name__}\033[0m")

    def visit_Program(self, node):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_PrintNode(self, node):
        value = self.visit(node.expr)
        print(value)

    def visit_StringNode(self, node):
        return node.value

    def visit_MathNode(self, node):
        result = self.visit(node.expr)
        print(result)

    def visit_NumberNode(self, node):
        return node.value

    def visit_BinOpNode(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)

        if node.op.type == PLUS:
            return left + right
        elif node.op.type == MINUS:
            return left - right
        elif node.op.type == MUL:
            return left * right
        elif node.op.type == DIV:
            return left / right

    def visit_VarAssignNode(self, node):
        value = self.visit(node.value)
        self.variables[node.name] = value

    def visit_VarAccessNode(self, node):
        if node.name not in self.variables:
            raise Exception(f"Undefined variable '{node.name}'")
        return self.variables[node.name]


def run(source, interpreter):
    source = source.strip()

    if source == "":
        return

    if not source.startswith(("PRINT", "MATH")):
        source = "MATH " + source

    tokenizer = Tokenizer(source)
    tokens, error = tokenizer.tokenize()

    if error:
        print(repr(error))
        return

    parser = Parser(tokens)
    tree = parser.parse()

    interpreter.visit(tree)


if __name__ == "__main__":
    interpreter = Interpreter()
    source = """PRINT 'Hello, World!'
MATH 2 + 3"""
    run(source, interpreter)
else:
    import sys
    interpreter = Interpreter()
    run(sys.argv[1], interpreter)