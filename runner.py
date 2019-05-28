#!/usr/bin/env python3
# -*- coding: utf_8 -*-

"""
Recursive descent parser written by hand using plex module as scanner.
Part of my second assignment for my course "Compilers" of Ionian University.

This file is a language recognizer and interpreter.

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

        # Create a dictionary to store variables from file
        self.vars = {}


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
        """ Stmt_list  -> Stmt Stmt_list | .
        Start the next basic operation.
        """
        if self.la == 'id' or self.la == 'print':
            self.stmt()
            self.stmt_list()
            return
        elif self.la is None:
            return
        else:
            raise ParseError('in stmt_list: "id" or "print" expected')
        
    def stmt(self):
        """ Stmt -> id = Expr | print Expr.
        Operate on the finalized expression.
        Print its value in binary or assign it to a variable.
        """
        if self.la == 'id':
            val_id = self.val
            self.match('id')
            self.match('=')
            # Store value into a variable
            self.vars[val_id] = self.expr()
            return
        elif self.la == 'print':
            self.match('print')
            # Print in binary
            print( format(self.expr(), 'b') )
            return
        else:
            raise ParseError('in stmt: "id" or "print" expected')

    def expr(self):
        """ Expr -> Term Term_tail.
        Return finalized expression from lower levels one level up, to Stmt.
        """
        if self.la == '(' or self.la == 'id' or self.la == 'bin':
            # Get value from one level down (from Term_tail)
            val_term = self.term()
            val_term_tail = self.term_tail(val_term)
            # Move value one level up (to Stmt)
            return val_term_tail
        else:
            raise ParseError('in expr: "(", "id" or "bin" expected')

    def term_tail(self, val_expr):
        """ Term_tail -> xor Term Term_tail | .
        Get expression from one level up (Expr or another Term_tail).
        Return said expression back up, with 'xor' logical operations appended.
        Otherwise return the expression untouched.
        """
        if self.la == 'xor':
            self.match('xor')
            val_term = self.term()
            val_return = val_expr ^ self.term_tail(val_term)
            return val_return
        elif (self.la == ')' or self.la == 'id' or
                self.la == 'print' or self.la is None):     # from FOLLOW set!
            return val_expr
        else:
            raise ParseError('in term_tail: "xor", ")", '
                             + '"id" or "print" expected')

    def term(self):
        """ Term -> Factor Factor_tail.
        Return expression from lower levels one level up, to Expr
        or Term_tail.
        """
        if self.la == '(' or self.la == 'id' or self.la == 'bin':
            val_factor = self.factor()
            val_factor_tail = self.factor_tail(val_factor)
            return val_factor_tail
        else:
            raise ParseError('in term: "(", "id" or "bin" expected')

    def factor_tail(self, val_term):
        """ Factor_tail -> or Factor Factor_tail | .
        Get expression from one level up (Term or another Factor_tail).
        Return said expression back up, with 'or' logical operations appended.
        Otherwise return the expression untouched.
        """
        if self.la == 'or':
            self.match('or')
            val_factor = self.factor()
            val_return = val_term | self.factor_tail(val_factor)
            return val_return
        elif (self.la == ')' or self.la == 'xor' or self.la == 'id'
                or self.la == 'print' or self.la is None):  # from FOLLOW set!
            return val_term
        else:
            raise ParseError('in term_tail: "or", ")", "xor", '
                             + '"id" or "print" expected')

    def factor(self):
        """ Factor -> Atom Atom_tail. 
        Return expression from lower levels one level up, to Term
        or Factor_tail.
        """
        if self.la == '(' or self.la == 'id' or self.la == 'bin':
            val_atom = self.atom()
            val_atom_tail = self.atom_tail(val_atom)
            return val_atom_tail
        else:
            raise ParseError('in factor: "(", "id" or "bin" expected')

    def atom_tail(self, val_factor):
        """ Atom_tail -> and Atom Atom_tail | .
        Get expression from one level up (Factor or another Atom_tail).
        Return said expression back up, with 'and' logical operations appended.
        Otherwise return the expression untouched.
        """
        if self.la == 'and':
            self.match('and')
            val_atom = self.atom()
            val_return = val_factor & self.atom_tail(val_atom)
            return val_return
        elif (self.la == ')' or self.la == 'or' or self.la == 'xor'
                or self.la == 'id' or self.la == 'print'
                or self.la is None):                        # from FOLLOW set!
            return val_factor
        else:
            raise ParseError('in atom_tail: "and", ")", "or", "xor", '
                             + '"id" or "print" expected')

    def atom(self):
        """ Atom -> (Expr) | bin | id.
        Return a binary, a variable, or a new expression in parentheses one
        level up, to Factor or Atom_tail.
        Raise ParseError if the variable is undeclared.
        """
        if self.la == '(':
            self.match('(')
            val_expr = self.expr()
            self.match(')')
            return val_expr
        elif self.la == 'id':
            val_id = self.val
            self.match('id')
            if val_id in self.vars:
                return self.vars[val_id]
            else:
                raise ParseError('in atom: unrecognized variable name')
        elif self.la == 'bin':
            val_bin = int(self.val, 2)
            self.match('bin')
            return val_bin
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