#!/usr/bin/python
#  -*- coding: utf-8 -*-
from preprocesamientoController import *
from RIController import *


'''
Temas:
Value : Tea value addded
Tech : Technology machinery production tea
Tree : Tree balanced nodes
BGP : Dual Home BGP
'''


tema = "Tree"
controladorRI = RIController()
parametrosCrank = 0.2
parametrosSVM = [1,2,3]
controladorRI.iniciarRanking(parametrosSVM,parametrosCrank,tema)
controladorRI.metodosAlternativos(tema)

