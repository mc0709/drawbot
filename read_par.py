# -*- coding: utf-8 -*-
#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2013 Gael Ecorchard <galou_breizh@yahoo.fr>             *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************

__title__="DrawBot v 1.0 beta for Symoro+"
__author__ = "Gael Ecorchard <galou_breizh@yahoo.fr>"

import ply.lex as lex
import ply.yacc as yacc
import wx

def input_new(name):
#    while True:
#        try:
#            v = float(raw_input('Value for "' + name + '": '))
#        except ValueError:
#            pass
#        else:
#            break
#    return v
    ask = AskVariables(parent=None, variable=name)
    if ask.ShowModal() == wx.ID_OK:
        print("Got value")
        value = ask.GetValues()
    ask.Destroy()
    return value


class AskVariables(wx.Dialog):

    def __init__(self, parent=None, variable=None):
            super(AskVariables, self).__init__(parent, style=wx.SYSTEM_MENU|wx.CAPTION)
            self.variable = variable
            self.InitUI()
            self.SetTitle("Symbolic Variable Detected")

    def InitUI(self):
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.p = wx.Panel(self)

        #Instruction
        instr = wx.StaticText(self, label="A symbolic variable was detected\nwhile loading the .par file. Please provide\na numerical value for the following:")

        #input
        Grid = wx.GridBagSizer(hgap=5, vgap=5)
        var_lbl = wx.StaticText(self, label=self.variable+":", style=wx.ALIGN_RIGHT)
        self.var_val = wx.SpinCtrlDouble(self, initial=0, value="0", size=(100,-1), min=-999999, max=999999)
        self.var_units = wx.ComboBox(self, size=(50,-1), choices=["mm", unichr(186)], style=wx.CB_READONLY)
        Grid.Add(var_lbl, pos=(0,0), flag=wx.ALIGN_RIGHT)
        Grid.Add(self.var_val, pos=(0,1), flag=wx.ALIGN_LEFT)
        Grid.Add(self.var_units, pos=(0,2), flag=wx.ALIGN_LEFT)
        
        #OK button
        okButton = wx.Button(self, wx.ID_OK, "OK")
        okButton.Bind(wx.EVT_BUTTON, self.OnOK)

        #layout elements
        self.mainSizer.Add(instr, flag=wx.ALL|wx.ALIGN_CENTER, border = 20)
        self.mainSizer.AddSpacer(10)
        self.mainSizer.Add(Grid, flag=wx.ALIGN_CENTER)
        self.mainSizer.AddSpacer(20)
        self.mainSizer.Add(okButton, flag=wx.ALL|wx.ALIGN_RIGHT, border = 20)

        self.SetSizerAndFit(self.mainSizer)

    def OnOK(self, e):
        print("OK pressed")
        self.EndModal(wx.ID_OK)

    def GetValues(self):
        if (self.var_units.GetSelection() == 1):
            from math import pi
            return self.var_val.GetValue()*pi/180
        else:
            return self.var_val.GetValue()


class ParLexer(object):
    def __init__(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)
        self.lookup = {}
        self.geo_done = False

	#keywords to look out for in the .par file
    keywords = [
        'NF', 'NL', 'NJ', 'Type',
        'Ant', 'Sigma', 'B', 'd', 'R',
        'gamma', 'Alpha', 'Mu', 'Theta',
        'XX', 'XY', 'XZ', 'YY', 'YZ', 'ZZ',
        'MX', 'MY', 'MZ', 'M',
        'IA', 'FV', 'FS', 'FX', 'FY', 'FZ',
        'CX', 'CY', 'CZ', 'QP', 'QDP',
        'W0', 'WP0', 'V0', 'VP0',
        'Z', 'G',
        ]

    tokens = [
        'COMMENT', 'KEYWORD', 'INTEGER', 'FLOAT', 'Pi', 'NEWLINE',
        'LBRACE',
        'RBRACE',
        'NAME', 'JOINTVAR',
        ]

    literals = ['=','+','-','*','/', '(', ')', ',']

    # Many keywords are defined as brace-enclosed vectors (parameter list).
    # Inside braces, NEWLINE are ignored.
    states = (
        ('paramlist', 'inclusive'),
    )


    t_ignore = " \t\r"

    # TODO: propose a modification to the official to explain how to switch
    # state AND return a token.
    def t_LBRACE(self, t):
        r'\{'
        t.lexer.push_state('paramlist')
        return t

    def t_RBRACE(self, t):
        r'\}'
        t.lexer.pop_state()
        return t

    def t_COMMENT(self, t):
        r'\(\*.*'
        pass

    _keyword_pattern = '|'.join([r'\b' + k + r'\b' for k in keywords])
    from ply.lex import TOKEN
    @TOKEN(_keyword_pattern)
    def t_KEYWORD(self, t):
        #set flag to stop asking for values once geom.par. are read
        print(t.value)
        if t.value=='XX':
            self.geo_done = True
            print('found XX')
        return t

    # Within braces keywords are treated as names, though this is not supported
    # by Symoro+.
    @TOKEN(_keyword_pattern)
    def t_paramlist_KEYWORD(self, t):
        return self.t_NAME(t)

    def t_Pi(self, t):
        r'Pi'
        from math import pi
        t.value = pi
        t.type = 'FLOAT'
        return t

    def t_FLOAT(self, t):
        r'[0-9]+[.eE]+[0-9eE]*'
        t.value = float(t.value)
        return t

    def t_INTEGER(self, t):
        r'\d+'
        t.value = int(t.value)
        return t

    def t_JOINTVAR(self, t):
        r'q[0-9]*\b'
        t.value = 0
        t.type = 'FLOAT'
        return t

    def t_NAME(self, t):
        r'[a-zA-Z_][a-zA-Z0-9_]*'
        try:
            t.value = self.lookup[t.value]
        except KeyError:
            if self.geo_done == False:
                val = input_new(t.value)
            else:
                val = t.value
            self.lookup[t.value] = val
            t.value = val
            t.type = 'NAME'
            return t
        t.type = 'FLOAT'
        return t

    # NEWLINE are needed to mark the end of an assignment.
    def t_NEWLINE(self, t):
        r'[\n]+'
        t.lexer.lineno += t.value.count("\n")
        return t

    # NEWLINE are ignored within parameter lists.
    def t_paramlist_NEWLINE(self, t):
        r'[\n]+'
        t.lexer.lineno += t.value.count("\n")

    def t_error(self, t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)


class ParParser(object):
    def __init__(self):
        self.lexer = ParLexer()
        self.tokens = self.lexer.tokens
        self.lookup = self.lexer.lookup
        #self.parser = yacc.yacc(module=self,write_tables=0,debug=False)
        self.parser = yacc.yacc(module=self, debug=1)
        self.robot_definition = {}

    def parse(self, data):
        if data:
            return self.parser.parse(data, self.lexer.lexer,
                    False, 0, None)
        else:
            return []

    precedence = (
        ('left', ','),
        ('left','+','-'),
        ('left','*','/'),
        ('right','UMINUS'),
        )

    def p_input(self, p):
        """input :
                | input line"""
        pass

    # TODO: propose a modification to the official documentation to explain how
    # to deal with newlines in input.
    def p_line(self, p):
        """line : assignment NEWLINE
                | NEWLINE"""
        pass

    def p_assignment(self, p):
        """assignment : KEYWORD '=' param
                      | KEYWORD '=' LBRACE paramlist RBRACE"""
        #print('in p_assignment, p = {}'.format(list(p)))
        if len(p) == 4:
            # assignment : KEYWORD '=' param
            self.robot_definition[p[1]] = p[3]
        else:
            # assignment : KEYWORD '=' '{' paramlist '}'
            self.robot_definition[p[1]] = p[4]

    def p_paramlist(self, p):
        """paramlist : param
                     | param ',' paramlist"""
        #print('in p_paramlist, p = {}'.format(list(p)))
        if len(p) == 2:
            # paramlist : param
            p[0] = [p[1]]
        elif len(p) == 4:
            # paramlist : param ',' paramlist
            p[0] = [p[1]] + p[3]

    def p_param(self, p):
        """param : expression
                 | '(' expression ')'"""
        #print('in p_param, p = {}'.format(list(p)))
        index = 1 if len(p) == 2 else 2
        p[0] = p[index]

    def p_expression_binop(self, p):
        """expression : expression '+' expression
                    | expression '-' expression
                    | expression '*' expression
                    | expression '/' expression"""
        #print('in p_expression_binop, p = {}'.format(list(p)))
        if p[2] == '+'  :
            p[0] = p[1] + p[3]
        elif p[2] == '-':
            p[0] = p[1] - p[3]
        elif p[2] == '*':
            p[0] = p[1] * p[3]
        elif p[2] == '/':
            p[0] = p[1] / p[3]
        elif p[1] == '(' and p[3] == ')':
            p[0] = p[2]

    def p_expression_uminus(self, p):
        """expression : '-' expression %prec UMINUS"""
        #print('in p_expression_uminus, p = {}'.format(list(p)))
        p[0] = -p[2]

    def p_expression_term(self, p):
        """expression : INTEGER
                    | FLOAT
                    | Pi
                    | NAME
                    | JOINTVAR"""
        #print('in p_expression_term, p = {}'.format(list(p)))
        p[0] = p[1]

    def p_error(self, p):
        print 'Error!'
        print p
        print


def _get_varname(name='robot'):
    name = ''.join([c if c.isalnum() else '_' for c in name])
    if name[0].isdigit():
        name = '_' + name
    return name


def par_reader(fname):
    """Return a description table from a Symoro+ robot description file"""
    robot_name = 'robot'
    with open(fname, 'r') as f:
        par_content = f.read()
        f.seek(0)
        for l in f.readlines():
            import re
            match = re.match(r'^\(\* Robotname = \'(.*)\' \*\)', l)
            if match:
                robot_name = match.group(1)
    robot_name = _get_varname(robot_name)
    parser = ParParser()
    parser.parse(par_content)
    robdef = parser.robot_definition

    table = []
    # antecedant, sameas, mu, sigma,
    #   gamma, b, alpha, d, theta, r
    for i in range(robdef['NF']):
        table.append((
            robdef['Ant'][i],
            0,
            robdef['Mu'][i],
            robdef['Sigma'][i],
            robdef['gamma'][i],
            robdef['B'][i],
            robdef['Alpha'][i],
            robdef['d'][i],
            robdef['Theta'][i],
            robdef['R'][i],
        ))
    return robot_name, table, robdef['NF'], robdef['NJ']
