#!/usr/bin/env python3
# -*- coding: utf_8 -*-

"""
Recursive descent parser written by hand using plex module as scanner.
Part of my second assignment for my course "Compilers" of Ionian University.

This file is a language recognizer only.

Heavily based on:
https://gist.github.com/mixstef/946fce67f49f147991719bfa4d0101fa


Grammar:
----------
Stmt_list   →   Stmt Stmt_list
            |   .
Stmt        →   id assign Expr
            |   print Expr.
Expr        →   Term Term_tail.
Term_tail   →   xor Term Term_tail
            |   .
Term        →   Factor Factor_tail.
Factor_tail →   or Factor Factor_tail
            |   .
Factor      →   Atom Atom_tail.
Atom_tail   →   and Atom Atom_tail
            |   .
Atom        →   (Expr)
            |   bin
            |   id.


FIRST sets:
----------
Stmt_list:      id print
Stmt:           id print
Expr:           (Expr) bin id
Term_tail:      xor
Term:           (Expr) bin id
Factor_tail:    or
Factor:         (Expr) bin id
Atom_tail:      and
Atom:           (Expr) bin id

FOLLOW sets:
-----------
Stmt_list:      ∅
Stmt:           id print
Expr:           id print
Term_tail:      id print
Term:           xor id print
Factor_tail:    xor id print
Factor:         or xor id print
Atom_tail:      or xor id print
Atom:           and or xor id print


I used an online tool to confirm that the grammar is LL(1), as well as
generating the First and Follow sets:
http://smlweb.cpsc.ucalgary.ca/start.html

"""


import plex


class ParseError(Exception):
    pass


class MyParser:
    """ A class encapsulating all parsing functionality 
    for a particular grammar.
    """
    def create_scanner(self, fp):
        """ Creates a plex scanner for a particular grammar 
        to operate on file object fp.
        """        
        # Define some pattern constructs
        and_op = plex.Str('and')
        or_op = plex.Str('or')
        xor_op = plex.Str('xor')
        assignment_op = plex.Str('=')
        print_op = plex.Str('print')

        space = plex.Any(' \t\n')
        parenthesis_open = plex.Str('(')
        parenthesis_close = plex.Str(')')
        binary = plex.Rep1(plex.Range('01'))
        digit = plex.Range('09')
        letter = plex.Range('AZaz')        
        variable = letter + plex.Rep(letter|digit)

        # The scanner lexicon - constructor argument is
        # a list of (pattern, action) tuples
        lexicon = plex.Lexicon([
            (and_op, 'and'),
            (or_op, 'or'),
            (xor_op, 'xor'),
            (assignment_op, '='),
            (print_op, 'print'),            
            (space, plex.IGNORE),
            (parenthesis_open, '('),
            (parenthesis_close, ')'),
            (binary, 'bin'),
            (variable, 'id')            
            ])

        # Create and store the scanner object, and get initial lookahead
        self.scanner = plex.Scanner(lexicon, fp)
        self.la, self.val = self.next_token()


    def next_token(self):
        """ Returns tuple (next_token, matched-text). """
        return self.scanner.read()

    def position(self):
        """ Utility function that returns position in text in case of errors.
        Here it simply returns the scanner position.
        """
        return self.scanner.position()

    def match(self, token):
        """ Consumes (matches with current lookahead) an expected token.
        Raises ParseError if anything else is found. Acquires new lookahead.
        """ 
        if self.la == token:
            self.la, self.val = self.next_token()
        else:
            raise ParseError('found {} instead of {}'.format(self.la, token))

    def parse(self, fp):
        """ Creates scanner for input file object fp and
        calls the parse logic code.
        """
        self.create_scanner(fp)
        self.stmt_list()

    def stmt_list(self):
        """ Stmt_list  -> Stmt Stmt_list | . """
        if self.la == 'id' or self.la == 'print':
            self.stmt()
            self.stmt_list()
            return
        elif self.la is None:
            return
        else:
            raise ParseError('in stmt_list: "id" or "print" expected')
        
    def stmt(self):
        """ Stmt -> id = Expr | print Expr. """
        if self.la == 'id':
            self.match('id')
            self.match('=')
            self.expr()
            return
        elif self.la == 'print':
            self.match('print')
            self.expr()
            return
        else:
            raise ParseError('in stmt: "id" or "print" expected')

    def expr(self):
        """ Expr -> Term Term_tail. """
        if self.la == '(' or self.la == 'id' or self.la == 'bin':
            self.term()
            self.term_tail()
            return
        else:
            raise ParseError('in expr: "(", "id" or "bin" expected')

    def term_tail(self):
        """ Term_tail -> xor Term Term_tail | . """
        if self.la == 'xor':
            self.match('xor')
            self.term()
            self.term_tail()
            return
        elif (self.la == ')' or self.la == 'id' or
                self.la == 'print' or self.la is None):     # from FOLLOW set!
            return
        else:
            raise ParseError('in term_tail: "xor", ")", '
                             + '"id" or "print" expected')

    def term(self):
        """ Term -> Factor Factor_tail. """
        if self.la == '(' or self.la == 'id' or self.la == 'bin':
            self.factor()
            self.factor_tail()
            return
        else:
            raise ParseError('in term: "(", "id" or "bin" expected')

    def factor_tail(self):
        """ Factor_tail -> or Factor Factor_tail | . """
        if self.la == 'or':
            self.match('or')
            self.factor()
            self.factor_tail()
            return
        elif (self.la == ')' or self.la == 'xor' or self.la == 'id'
                or self.la == 'print' or self.la is None):  # from FOLLOW set!
            return
        else:
            raise ParseError('in term_tail: "or", ")", "xor", '
                             + '"id" or "print" expected')

    def factor(self):
        """ Factor -> Atom Atom_tail. """
        if self.la == '(' or self.la == 'id' or self.la == 'bin':
            self.atom()
            self.atom_tail()
            return
        else:
            raise ParseError('in factor: "(", "id" or "bin" expected')

    def atom_tail(self):
        """ Atom_tail -> and Atom Atom_tail | . """
        if self.la == 'and':
            self.match('and')
            self.atom()
            self.atom_tail()
            return
        elif (self.la == ')' or self.la == 'or' or self.la == 'xor'
                or self.la == 'id' or self.la == 'print'
                or self.la is None):                        # from FOLLOW set!
            return
        else:
            raise ParseError('in atom_tail: "and", ")", "or", "xor", '
                             + '"id" or "print" expected')

    def atom(self):
        """ Atom -> (Expr) | bin | id. """
        if self.la == '(':
            self.match('(')
            self.expr()
            self.match(')')
            return
        elif self.la == 'id':
            self.match('id')
            return
        elif self.la == 'bin':
            self.match('bin')
            return
        else:
            raise ParseError('in atom: "(", "id" or "bin" expected')


# The main part of program
parser = MyParser()
with open("binfile.txt", "r") as fp:
	try:
		parser.parse(fp)
	except plex.errors.PlexError:
		_, lineno, charno = parser.position()	
		print("Scanner Error: at line {} char {}".format(lineno, charno+1))
	except ParseError as perr:
		_, lineno, charno = parser.position()	
		print("Parser Error: {} at line {} char {}"\
              .format(perr, lineno, charno+1))