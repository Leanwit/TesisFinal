#!/usr/bin/python
#  -*- coding: utf-8 -*-
from preprocesamientoController import *
from RIController import *


#consulta = "Tea AND alternative AND new AND Value added AND patents OR paper OR cite"

controladorRI = RIController()
#controladorRI.iniciarRanking(consulta)

consultas = []
consultas.append("Tea AND alternative AND new AND Value added AND patents OR paper OR cite")
consultas.append("sell OR buy AND Tea AND value added AND products AND alimentation")
consultas.append("Tea AND products AND medicine AND health AND patents OR paper OR cite")
consultas.append("Tea AND innovations AND competitive AND marketing AND strategies AND Value added AND patents OR paper OR cite")
consultas.append("tea AND food AND black AND green AND exports AND value added AND patents OR paper OR cite")
for unaConsulta in consultas:
    print unaConsulta
    controladorRI.metodosAlternativos(unaConsulta)
