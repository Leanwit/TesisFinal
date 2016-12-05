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


tema = ""
controladorRI = RIController()
parametrosRC = {"niveles": 5, "AC": 1, "AP": 0.3, "AN": 0.1, "factorContribucion": 0.1}
parametrosSVM = [1,2,3]
controladorRI.iniciarRanking(parametrosSVM,parametrosRC,tema)

parametrosCrank = {"niveles": 3, "AC": 1, "AP": 0.75, "AN": 0.5, "factorContribucion": 0.2}

controladorRI.metodosAlternativos(tema,parametrosCrank)
