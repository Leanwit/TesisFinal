#!/usr/bin/python
#  -*- coding: utf-8 -*-
from preprocesamientoController import *
from RIController import *


consulta = "Tree Structures badges"

controladorRI = RIController()
#controladorRI.initSVM('Entrada/svmEntrenamiento.txt')
#controladorRI.rankingSVM('Entrada/svmTesting.txt')
#controladorRI.crearListaConRelevancia('Entrada/listaRelevancia.txt')
controladorRI.initCrank("Crank",consulta)