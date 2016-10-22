#!/usr/bin/python
#  -*- coding: utf-8 -*-
from preprocesamientoController import *
from RIController import *


consulta = "Tea AND alternative AND new AND Value added AND patents OR paper OR cite"

controladorRI = RIController()
controladorRI.iniciarRanking(consulta)
#controladorRI.metodosAlternativos(consulta)