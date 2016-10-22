#!/usr/bin/python
#  -*- coding: utf-8 -*-
from preprocesamientoController import *
from RIController import *


consulta = "Tea AND alternative AND new AND Value added AND patents OR paper OR cite "

controladorRI = RIController()
#controladorRI.initSVM('Entrada/svmEntrenamiento.txt')
#controladorRI.rankingSVM('Entrada/svmTesting.txt')
#controladorRI.crearListaConRelevancia('Entrada/listaRelevancia.txt')
controladorRI.initCrank("EP",consulta)