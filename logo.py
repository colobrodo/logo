from enum import Enum
from turtle import Turtle


class Token:
   def __init__(self, kind, position, content=None):
      self.kind = kind
      self.position = position
      self.content = content

   def __str__(self):
      _str = '{}'.format(self.kind.name)
      if self.content:
         _str += '({})'.format(self.content)
      return _str

   __repr__ = __str__
 

class TokenKind(Enum):
   REPEAT     = "REPEAT"
   ROTATE     = "ROTATE"
   FORWARD    = "FORWARD"
   BACKWARD   = "BACKWARD"
   PENUP      = "PENUP"
   PENDOWN    = "PENDOWN"
   LBRACE     = "["
   RBRACE     = "]"
   NUMBER     = "NUMBER"
   SYMBOL     = "SYMBOL"
   IDENTIFIER = "IDENTIFIER"
   TO         = "TO"
   END        = "END"
   EOF        = "EOF"


class LogoParserError(Exception):
   def __init__(self, message, position):
      self.position = position
      self.message = message
      super().__init__(message)

   def __str__(self):
      return "{} at {}".format(self.message, self.position)


class FilePosition:
   def __init__(self, line_num, char):
      self.line_num = line_num
      self.char = char

   def at_new_line(self):
      self.line_num += 1
      self.char = 0

   def copy(self):
      return FilePosition(self.line_num, self.char)

   def __str__(self):
      return 'line {}: {}'.format(self.line_num, self.char)


class Lexer:
   def __init__(self, text):
      self.text = text
      self._text_len = len(text)
      self.position = FilePosition(1, 0)
      self._index = 0
      self._buffer = []

   def _peek_c(self, offset=0):
      if self._index + offset < self._text_len:
         return self.text[self._index + offset]

   def _create_token(self, kind, **kwargs):
      return Token(kind, self.position.copy(), **kwargs)

   def _advance(self, offset=1):
      end_i = self._index + offset
      for c in self.text[self._index: end_i]:
         self.position.char += 1
         if c == '\n':
            self.position.at_new_line()
      self._index = end_i
      if self._index > len(self.text):
         raise LogoParserError('Lexer cannot advance', self.position)

   def _pop_c(self, size=1):
      end_i = self._index + size
      if end_i > self._text_len:
         return None
      res = self.text[self._index: end_i]
      self._advance(size)
      return res

   def eat_spaces(self):
      # advance spaces and '#' inline comments
      while True:
         # eat all the space one line at time 
         spaces = self.get_while(str.isspace)
         next_char = self._peek_c()
         if not next_char:
            break
         if next_char == '#':
            self._advance()
            # single line comment
            while True:
               c = self._pop_c()
               if c == '\n':
                  break
         elif not spaces:
            break
   
   def get_while(self, cond):
      res = ''
      while True:
         c = self._peek_c()
         if not c:
            break
         if not cond(c):
            break
         res += c
         self._advance()
      return res      

   def match_c(self, chars):
      if type(chars) == tuple:
         for c in chars:
            match_res = self.match_c(c)
            if match_res:
               return match_res
         return None
      if self._peek_c() == chars:
         return self._pop_c()
      return None

   def pop(self):
      if self._buffer:
         return self._buffer.pop(0)
      
      _Token = self._create_token
      
      self.eat_spaces()

      c = self._pop_c()
      if not c:
         return _Token(TokenKind.EOF)

      if c == '[':
         return _Token(TokenKind.LBRACE)
      if c == ']':
         return _Token(TokenKind.RBRACE)

      def is_identifier_char(c):
         return c.isalnum() or c == '_'
      # matching identifier and axis literal
      identifier_content = ''
      if c.isalpha():
         identifier_content = c + self.get_while(is_identifier_char)
         if identifier_content.casefold() == 'repeat':
            return _Token(TokenKind.REPEAT)
         if identifier_content.casefold() == 'rotate':
            return _Token(TokenKind.ROTATE)
         if identifier_content.casefold() == 'backward':
            return _Token(TokenKind.BACKWARD)
         if identifier_content.casefold() == 'forward':
            return _Token(TokenKind.FORWARD)
         if identifier_content.casefold() == 'penup':
            return _Token(TokenKind.PENUP)
         if identifier_content.casefold() == 'pendown':
            return _Token(TokenKind.PENDOWN)
         if identifier_content.casefold() == 'to':
            return _Token(TokenKind.TO)
         if identifier_content.casefold() == 'end':
            return _Token(TokenKind.END)
         return _Token(TokenKind.IDENTIFIER, content=identifier_content)

      # matching symbols names starting with ':', usualy used for variables
      if c == ':':
         symbol_content = c + self.get_while(is_identifier_char)
         return _Token(TokenKind.SYMBOL, content=symbol_content)

      # matching numbers 
      is_negative = False
      if c == '-':
         is_negative = True
         c = self._pop_c()
      if c.isnumeric():
         number_literal = c + self.get_while(str.isnumeric)
         if self._peek_c() == '.':
            self._advance()
            number_literal += '.'
            rational_part = self.get_while(str.isnumeric)
            if not rational_part:
               return None
            number_literal += rational_part
         if is_negative:
            number_literal = '-' + number_literal
         return _Token(TokenKind.NUMBER, content=number_literal)
      assert not is_negative

   def peek(self):
      if self._buffer:
         return self._buffer[0]
      else:
         next_token = self.pop()
         self._buffer.append(next_token)
         return next_token

   def match(self, expected_kind):
      next_token = self.pop()
      if next_token is None:
         return None
      if next_token.kind != expected_kind:
         raise LogoParserError('Error trying to parse ppm file: expecting \'{}\' get a \'{}\''.format(expected_kind.name, next_token), self.position)
      return next_token
   
   def maybe_match(self, expected_kind):
      next_token = self.pop()
      if next_token is None:
         return None
      if next_token.kind != expected_kind:
         self._buffer.append(next_token)
         return None
      return next_token


class LogoAst:
   pass

class AstRotate(LogoAst):
   def __init__(self, n):
      self.n = n

class AstForward(LogoAst):
   def __init__(self, n):
      self.n = n

class AstBackward(LogoAst):
   def __init__(self, n):
      self.n = n

class AstPenUp(LogoAst):
   pass

class AstPenDown(LogoAst):
   pass

class AstRepeat(LogoAst):
   def __init__(self, times, block):
      self.times = times
      self.block = block

class AstBlock(LogoAst):
   def __init__(self, instructions):
      self.body = instructions

class AstProcedure(LogoAst):
   def __init__(self, name, arguments, instructions):
      self.name = name
      self.arguments = arguments
      self.body = AstBlock(instructions)

class AstProcedureCall(LogoAst):
   def __init__(self, procedure_name, arguments):
      self.procedure_name = procedure_name
      self.arguments = arguments

class AstSymbolReference(LogoAst):
   def __init__(self, name):
      self.name = name

class Environment:
   def __init__(self, parent=None):
      self._names = {}
      self.parent = parent

   def set(self, name, value):
      self._names[name] = value
   
   def resolve(self, name):
      if value := self._names.get(name):
         return value
      if self.parent:
         return self.parent.resolve(name)
      return None

   def create_child(self):
      return Environment(self)


class LogoParser:
   def __init__(self, f):
      self.lexer = Lexer(f.read())

   def parse(self):
      file_body = []
      while True:
         if self.lexer.maybe_match(TokenKind.EOF):
            break
         instruction = self.parse_instruction()
         file_body.append(instruction)
      return AstBlock(file_body)

   def parse_block(self):
      if self.lexer.maybe_match(TokenKind.LBRACE):
         instructions = []
         while not self.lexer.maybe_match(TokenKind.RBRACE):
            instructions.append(self.parse_instruction())
         return AstBlock(instructions)
      else:
         return self.parse_instruction()
   
   def parse_expression(self):
      if number_token := self.lexer.maybe_match(TokenKind.NUMBER):
         return float(number_token.content)
      if symbol_token := self.lexer.maybe_match(TokenKind.SYMBOL):
         return AstSymbolReference(symbol_token.content)
      return None

   def parse_number(self):
      number_token = self.lexer.match(TokenKind.NUMBER)
      return float(number_token.content)
   
   def parse_instruction(self):
      if self.lexer.maybe_match(TokenKind.TO):
         name_identifier = self.lexer.match(TokenKind.IDENTIFIER)
         arguments = []
         while symbol := self.lexer.maybe_match(TokenKind.SYMBOL):
            arguments.append(symbol.content)
         procedure_body = []
         while not self.lexer.maybe_match(TokenKind.END):
            instruction = self.parse_instruction()
            procedure_body.append(instruction)
         return AstProcedure(name_identifier.content, arguments, procedure_body)
      if self.lexer.maybe_match(TokenKind.ROTATE):
         n = self.parse_expression()
         return AstRotate(n)
      if self.lexer.maybe_match(TokenKind.FORWARD):
         n = self.parse_expression()
         return AstForward(n)
      if self.lexer.maybe_match(TokenKind.BACKWARD):
         n = self.parse_expression()
         return AstBackward(n)
      if self.lexer.maybe_match(TokenKind.PENDOWN):
         return AstPenDown()
      if self.lexer.maybe_match(TokenKind.PENUP):
         return AstPenUp()
      if self.lexer.maybe_match(TokenKind.REPEAT):
         times = self.parse_expression()
         block = self.parse_block()
         return AstRepeat(times, block)
      if name_token := self.lexer.maybe_match(TokenKind.IDENTIFIER):
         # TODO: add blocks to expressions
         arguments = []
         while expr := self.parse_expression():
            arguments.append(expr)
         return AstProcedureCall(name_token.content, arguments)


def evaluate_expression(expr, environment):
   if isinstance(expr, AstSymbolReference):
      symbol = expr
      return environment.resolve(expr.name)
   return expr

def run(node, environment, turtle):
   if isinstance(node, AstForward):
      n = evaluate_expression(node.n, environment)
      turtle.forward(n)
   elif isinstance(node, AstBackward):
      n = evaluate_expression(node.n, environment)
      turtle.backward(n)
   elif isinstance(node, AstRotate):
      n = evaluate_expression(node.n, environment)
      turtle.left(n)
      
   elif isinstance(node, AstPenUp):
      turtle.penup()
   elif isinstance(node, AstPenDown):
      turtle.pendown()
   elif isinstance(node, AstBlock):
      for instruction in node.body:
         run(instruction, environment, turtle)
   elif isinstance(node, AstRepeat):
      times = evaluate_expression(node.times, environment)
      n = int(times)
      for i in range(n):
         run(node.block, environment, turtle)
   elif isinstance(node, AstProcedure):
      procedure = node
      environment.set(procedure.name, procedure)
   elif isinstance(node, AstProcedureCall):
      call = node
      procedure = environment.resolve(call.procedure_name)
      if not procedure:
         raise LogoParserError('ERROR: cannot find the procedure {}'.format(call.procedure_name), None)

      function_arity = len(procedure.arguments)
      argument_passed = len(node.arguments)
      if function_arity != argument_passed:
         error_message = 'ERROR: wrong number of argument for the function \'{}\' (needed {}, passed {})'.format(procedure.name, function_arity, argument_passed)
         # TODO: use a way to retrive the error position here
         raise LogoParserError(error_message, None)
      
      child_env = environment.create_child()
      for name, argument in zip(procedure.arguments, call.arguments):
         value = evaluate_expression(argument, environment)
         child_env.set(name, value)
      
      run(procedure.body, child_env, turtle)
   else:
      raise RuntimeError('Unknow instruction {}'.format(type(node)))


def report_error(sourcefile, error):
   print(error.message)
   print('\n')

   with open(sourcefile, 'r') as f:
      for n in range(error.position.line_num):
         f.readline()

      line = f.readline()
      if not line:
         return
      
      print(line)
      print(' ' * error.position.char + '^')


if __name__ == '__main__':
   import argparse, sys

   parser = argparse.ArgumentParser()
   parser.add_argument('filepath', nargs='?', type=argparse.FileType('r'),
                       default=sys.stdin, help='the path of your logo program')
   args = parser.parse_args()

   ast = LogoParser(args.filepath).parse()

   ewd_turtle = Turtle()
   global_env = Environment()
   run(ast, global_env, ewd_turtle)