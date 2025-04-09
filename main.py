#!/usr/bin/env python3
"""
Team Members:
    Alice (ID: A001)
    Bob   (ID: B002)
    Carol (ID: C003)
    
This file is the complete source code for the Recursive Descent Parser for the simplified Prolog grammar.
"""

import re
import os

# Set to True for detailed debugging output during development.
DEBUG = False

# ====================================
#           LEXER IMPLEMENTATION
# ====================================

class Lexer:
    def __init__(self, text):
        self.text = text
        self.tokens = []
        self.line = 1
        self.tokenize()

    def tokenize(self):
        # Define token specifications
        token_specification = [
            ('NUMBER',    r'\d+'),                                   # Numerals
            ('ATOM',      r'[a-z][a-zA-Z0-9_]*'),                     # Atoms (start with lowercase)
            ('VARIABLE',  r'[A-Z_][a-zA-Z0-9_]*'),                    # Variables (start with uppercase or _)
            ('SPECIAL',   r'(\?\-|\:\-|[\.,\(\),])'),                 # Special symbols, including '?-' and ':-'
            ('SKIP',      r'[ \t]+'),                                # Skip spaces and tabs
            ('NEWLINE',   r'\n'),                                    # Newlines (to update line numbers)
            ('MISMATCH',  r'.'),                                     # Any other character
        ]
        tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
        get_token = re.compile(tok_regex).match
        pos = 0
        while pos < len(self.text):
            m = get_token(self.text, pos)
            if m:
                kind = m.lastgroup
                value = m.group()
                if kind == 'NEWLINE':
                    self.line += 1
                elif kind == 'SKIP':
                    pass
                elif kind == 'MISMATCH':
                    # Record as an error token to be handled by the parser.
                    self.tokens.append(('ERROR', value, self.line))
                else:
                    self.tokens.append((kind, value, self.line))
                pos = m.end()
            else:
                break
        self.tokens.append(('EOF', '', self.line))

    def get_tokens(self):
        return self.tokens

# ====================================
#         PARSER IMPLEMENTATION
# ====================================

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.errors = []

    def current_token(self):
        return self.tokens[self.pos]

    def advance(self):
        if self.pos < len(self.tokens) - 1:
            self.pos += 1

    def match(self, expected_type, expected_value=None):
        token = self.current_token()
        if token[0] == expected_type and (expected_value is None or token[1] == expected_value):
            if DEBUG:
                print("Matched:", token)
            self.advance()
            return True
        else:
            self.error(f"Expected {expected_type} '{expected_value}' but found {token[0]} '{token[1]}'", token[2])
            return False

    def error(self, message, line):
        error_msg = f"Syntax Error at line {line}: {message}"
        self.errors.append(error_msg)

    # ---- Parsing functions based on the EBNF grammar ----

    def parse_program(self):
        # A program can be a clause-list optionally followed by a query or a single query.
        if self.current_token()[1] == '?-':
            self.parse_query()
        else:
            self.parse_clause_list()
            if self.current_token()[1] == '?-':
                self.parse_query()

    def parse_clause_list(self):
        # Parse one or more clauses until a query starts or EOF is reached.
        while self.current_token()[0] != 'EOF' and self.current_token()[1] != '?-':
            self.parse_clause()

    def parse_clause(self):
        # Clause: predicate "."  or  predicate ":-" predicate-list "."
        self.parse_predicate()
        if self.current_token()[1] == '.':
            self.match('SPECIAL', '.')
        elif self.current_token()[1] == ':-':
            self.match('SPECIAL', ':-')
            self.parse_predicate_list()
            self.match('SPECIAL', '.')
        else:
            self.error("Clause must end with '.' or use ':-' followed by a predicate list and a '.'", self.current_token()[2])
            self.advance()

    def parse_query(self):
        # Query: starts with "?-" predicate-list "."
        if self.current_token()[1] == '?-':
            self.match('SPECIAL', '?-')
            self.parse_predicate_list()
            self.match('SPECIAL', '.')
        else:
            self.error("Query should start with '?-'", self.current_token()[2])

    def parse_predicate_list(self):
        self.parse_predicate()
        while self.current_token()[1] == ',':
            self.match('SPECIAL', ',')
            self.parse_predicate()

    def parse_predicate(self):
        # Predicate: atom [ "(" term-list ")" ]
        if self.current_token()[0] == 'ATOM':
            self.parse_atom()
            if self.current_token()[1] == '(':
                self.match('SPECIAL', '(')
                self.parse_term_list()
                self.match('SPECIAL', ')')
        else:
            self.error("Predicate must start with an atom", self.current_token()[2])
            self.advance()

    def parse_term_list(self):
        self.parse_term()
        while self.current_token()[1] == ',':
            self.match('SPECIAL', ',')
            self.parse_term()

    def parse_term(self):
        # Term: atom | variable | structure | numeral
        token = self.current_token()
        if token[0] == 'ATOM':
            self.parse_atom()
            # Check for structure: atom "(" term-list ")"
            if self.current_token()[1] == '(':
                self.match('SPECIAL', '(')
                self.parse_term_list()
                self.match('SPECIAL', ')')
        elif token[0] == 'VARIABLE':
            self.match('VARIABLE')
        elif token[0] == 'NUMBER':
            self.match('NUMBER')
        else:
            self.error("Invalid term: expected atom, variable, numeral, or structure", token[2])
            self.advance()

    def parse_atom(self):
        # Atom: for now, we assume a simple atom is recognized by the lexer.
        if self.current_token()[0] == 'ATOM':
            self.match('ATOM')
        else:
            self.error("Expected an atom", self.current_token()[2])
            self.advance()

# ====================================
#         FILE PROCESSING ROUTINES
# ====================================

def process_file(filename):
    """
    Reads the file, runs the lexer and parser,
    and returns the list of syntax errors (empty if no errors).
    """
    try:
        with open(filename, 'r') as file:
            content = file.read()
    except IOError:
        return [f"File {filename} not found or could not be read."]
    # Lexical analysis
    lexer = Lexer(content)
    tokens = lexer.get_tokens()
    # Parsing
    parser = Parser(tokens)
    parser.parse_program()
    return parser.errors

def main():
    output_lines = []
    file_num = 1

    # Process sequential files named "1.txt", "2.txt", ..., until a file is missing.
    while True:
        filename = f"Prolog-Parser/{file_num}.txt"
        if not os.path.exists(filename):
            break
        errors = process_file(filename)
        if not errors:
            output_lines.append(f"{filename}: Syntactically Correct.")
        else:
            output_lines.append(f"{filename}: Syntax Errors:")
            for err in errors:
                output_lines.append("  " + err)
        file_num += 1

    # Write parser output to the required file.
    with open("parser_output.txt", 'w') as fout:
        for line in output_lines:
            fout.write(line + "\n")

    # Optionally, print the output to console.
    for line in output_lines:
        print(line)

if __name__ == '__main__':
    main()