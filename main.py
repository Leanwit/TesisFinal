#!/usr/bin/python
#  -*- coding: utf-8 -*-
from preprocesamientoController import *
from RIController import *


#consulta = "Tea AND alternative AND new AND Value added AND patents OR paper OR cite"
consultaTree = ["Trees AND inserts AND avl AND create AND Balanced","Trees AND search AND balanced AND trim","B+ Tree AND remove AND pruning AND Balanced AND papers","trees AND recursive AND balanced AND nodes AND insert AND data structure AND patents OR paper OR cite","trees AND root AND node AND recursive AND optimization AND search AND b++ AND avl"]
consultaValueAdded = ["Tea AND alternative AND new AND Value added AND patents OR paper OR cite","sell OR buy AND Tea AND value added AND products AND alimentation","Tea AND products AND medicine AND health AND patents OR paper OR cite","Tea AND innovations AND competitive AND marketing AND strategies AND Value added AND patents OR paper OR cite","tea AND food AND black AND green AND exports AND value added AND patents OR paper OR cite"]
consultasTechnology = ["buy AND Tea AND Machinery AND Production","Tea AND machinery AND process AND harvest","buy AND Tea AND plantation AND Technology AND Machinery","tea AND system AND irrigation AND harvest AND production AND manufacturers AND technology AND patents OR paper OR cite","buy AND tea AND lower cost AND technology AND machinery AND harvest"]
consultasISP = ["bgp AND isp AND connection AND dual-homed AND patents OR paper OR cite","bgp AND isp AND keepalive AND messages","bgp AND Configurations AND Environments AND single isp AND multihoming","bgp AND routing AND wan AND configuration AND one isp AND two links AND patents OR paper OR cite.","bgp AND Dual Internet AND route AND connections AND patents OR paper OR cite"]


controladorRI = RIController()
controladorRI.iniciarRanking(consultasISP)

controladorRI.metodosAlternativos(consultasISP)
