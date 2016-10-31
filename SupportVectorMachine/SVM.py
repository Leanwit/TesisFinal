from Model.mongodb import *
from preprocesamientoController import *
from pattern.vector import Document,Model
from Atributos import *
import re
import numpy as np
from sklearn import svm


class SVM:
    mongodb = MongoDb()
    preprocesamiento = preprocesamientoController()

    instanciaSVM = None

    X = []
    Y = []

    xEntrenamiento = []
    xTest = []

    yEntrenamiento = []
    yTest = []


    def __init__(self):
        pass

    def definirTestOptimo(self,c,kernel,gamma):
        self.instanciaSVM = svm.SVC(C=c, kernel=kernel, gamma=gamma)


    def ajustarParametros(self,c,kernel,entrenamiento,test,X=[],Y=[],gamma = 1):
        self.X = np.array(X)
        self.Y = np.array(Y)
        self.definirConjuntos(entrenamiento,test)
        if kernel == "poly":
            self.instanciaSVM = svm.SVC(C=c, kernel=kernel, degree=3, gamma=gamma)
        else:
            self.instanciaSVM = svm.SVC(C=c, kernel=kernel, gamma=gamma)

    def training(self):
        self.instanciaSVM.fit(self.xEntrenamiento,self.yEntrenamiento)

    def agregarDocumentosEntrenamiento(self,X,Y):
        self.instanciaSVM.fit(np.array(X),np.array(Y))

    def testing(self):
        aciertos = 0
        prediccion = self.predecir(self.xTest)
        cantidadTotal = len(self.xTest)
        for unaClase,unaPrediccion in zip(self.yTest,prediccion):
            if unaClase == unaPrediccion:
                aciertos +=1
        return float(aciertos)/float(cantidadTotal)

    def predecir(self,conjunto):
        if len(conjunto):
            if len(conjunto) == 1:
                return self.instanciaSVM.predict(conjunto.reshape(1,-1))
            else:
                return self.instanciaSVM.predict(conjunto)

    def definirConjuntos(self,cantEntrenamiento,cantTest):
        self.xEntrenamiento = self.X[:int(cantEntrenamiento*len(self.X))]
        self.xTest = self.X[int(cantTest*len(self.X))*int(-1):]
        self.yEntrenamiento = self.Y[:int(cantEntrenamiento*len(self.Y))]
        self.yTest = self.Y[int(cantTest*len(self.Y))*int(-1):]


    def setearAtributos(self,listaUrls):
        listaAtributos = []
        listaConsultas = []
        for documento in listaUrls:
            url = documento[0]
            consulta = documento[1]
            if not consulta in listaConsultas:
                listaConsultas.append(consulta)
            documento = self.mongodb.getDocumento(url)
            if documento:
                atributo = self.getAtributo(documento['consultasClase'],consulta)
                if atributo:
                    listaAtributos.append(atributo)
                else:
                    print "Creando atributo", documento['url']
                    atributo = self.crearAtributosSingulares(documento, consultaClase['consulta'])
                    self.mongodb.agregarDatosAtributos(documento, consultaClase['consulta'], atributo)
                    listaAtributos.append(atributo)

        print "Init Atributos Grupales"
        self.crearAtributosGrupales(listaAtributos,listaConsultas)

    def getAtributo(self,lista,consulta):
        for unaConsultaClase in lista:
            if consulta == unaConsultaClase['consulta']:
                return unaConsultaClase['atributos']
        return False

    def setearAtributosRanking(self,listaUrls,consulta):
        listaAtributos = []
        listaProcesados = []
        for url in listaUrls:
            documento = self.mongodb.getDocumento(url)
            if documento:
                if 'consultasClase' in documento:
                    if not consulta.name in documento['consultasClase']:
                        atributo = self.crearAtributosSingulares(documento,consulta.name)
                        self.mongodb.agregarDatosAtributos(documento,consulta.name,atributo)
                        listaAtributos.append(atributo)
                        listaProcesados.append(url)



        self.crearAtributosGrupalesRanking(listaUrls,consulta.name)
        return listaProcesados

    def crearAtributosSingulares(self,documento,consulta):
        unDocumentoPattern = self.preprocesamiento.getDocumentoPattern(documento['_id'])
        html = unDocumentoPattern

        titulo = ""
        if "titulo" in documento:
            titulo = documento['titulo']
        titulo = self.preprocesamiento.crearDocumentoPattern(titulo)

        body = ""
        if "body" in documento:
            body = documento['body']
        body = self.preprocesamiento.crearDocumentoPattern(body)

        urlValues = ""
        if "urlValues" in documento:
            urlValues = documento['urlValues']
        urlValues = self.preprocesamiento.crearDocumentoPattern(urlValues)

        pdf = self.preprocesamiento.isPDF(documento['url'])
        url = self.urlDocumento(unDocumentoPattern)

        consultaDocumento = self.preprocesamiento.crearDocumentoPattern(consulta, "consulta")
        unAtributo = Atributos(html,url,titulo,urlValues,body,consultaDocumento,pdf)
        unAtributo.calcularAtributos()
        return unAtributo


    def crearAtributosGrupales(self,listaAtributos,listaConsultas):
        #consultas = self.mongodb.obtenerTodasLasConsultas()
        for consulta in listaConsultas:
            listaDocumentosHtml, listaDocumentosBody, listaDocumentosUrlValues, listaDocumentosTitle, listaDocumentosID = ([] for i in range(5))
            listaAtributos = self.mongodb.getAtributosPorConsulta(consulta)
            listaDocumentos = []
            for unAtributo in listaAtributos:
                documento = self.mongodb.getDocumento(unAtributo['doc'])
                if 'html' in documento:
                    listaDocumentosHtml.append(self.preprocesamiento.crearDocumentoPattern(documento['html']))
                    listaDocumentosBody.append(self.preprocesamiento.crearDocumentoPattern(documento['body']))
                    listaDocumentosUrlValues.append(self.preprocesamiento.crearDocumentoPattern(documento['urlValues']))
                    listaDocumentosTitle.append(self.preprocesamiento.crearDocumentoPattern(documento['titulo']))
                    listaDocumentos.append(documento)



            print "Inicio Modelos"
            modelos = {}
            modelos['documento'] = self.preprocesamiento.crearModelo(listaDocumentosHtml)
            modelos['body'] = self.preprocesamiento.crearModelo(listaDocumentosBody)
            modelos['urlValues'] = self.preprocesamiento.crearModelo(listaDocumentosUrlValues)
            modelos['title'] = self.preprocesamiento.crearModelo(listaDocumentosTitle)

            consulta = self.preprocesamiento.crearDocumentoPattern(consulta,consulta)
            unAtributo = Atributos()
            print "Inicio Calculo de Atributos Corpus", consulta
            unAtributo.calcularAtributosCorpus(modelos,consulta.name,listaDocumentos)

    def crearAtributosGrupalesRanking(self,listaUrls,consulta):
        print "init1"
        listaAtributos = []
        for url in listaUrls:
            documento = self.mongodb.getDocumento(url)
            if documento:
                if 'consultasClase' in documento:
                    for unaConsulta in documento['consultasClase']:
                        if unaConsulta['consulta'] == consulta:
                            atributos = {}
                            atributos['doc'] = documento['id']
                            atributos['atributo'] = unaConsulta['atributos']
                            listaAtributos.append(atributos)
        print "init2"


        listaDocumentosHtml, listaDocumentosBody, listaDocumentosUrlValues, listaDocumentosTitle, listaDocumentosID = ([] for i in range(5))
        listaDocumentos = []
        for unAtributo in listaAtributos:
            documento = self.mongodb.getDocumentoParam({'id':unAtributo['doc']})
            if 'html' in documento:
                listaDocumentosHtml.append(self.preprocesamiento.crearDocumentoPattern(documento['html']))
                listaDocumentosBody.append(self.preprocesamiento.crearDocumentoPattern(documento['body']))
                listaDocumentosUrlValues.append(self.preprocesamiento.crearDocumentoPattern(documento['urlValues']))
                listaDocumentosTitle.append(self.preprocesamiento.crearDocumentoPattern(documento['titulo']))
                listaDocumentos.append(documento)

        print "init3"
        modelos = {}
        modelos['documento'] = self.preprocesamiento.crearModelo(listaDocumentosHtml)
        modelos['body'] = self.preprocesamiento.crearModelo(listaDocumentosBody)
        modelos['urlValues'] = self.preprocesamiento.crearModelo(listaDocumentosUrlValues)
        modelos['title'] = self.preprocesamiento.crearModelo(listaDocumentosTitle)
        print "init4"

        consulta = self.preprocesamiento.crearDocumentoPattern(consulta,consulta)
        unAtributo = Atributos()

        unAtributo.calcularAtributosCorpus(modelos,consulta,listaDocumentos)
        print "init5"

    def urlDocumento(self,unDocumentoPattern):
        '''Expresion regular para separar en una lista los fragmentos de la url'''
        url = re.split('(\/)|(-)|(\.)', unDocumentoPattern.name)
        listaPartes = []
        palabrasVacias = [None,"/",".","-","www","com",""]
        for x in url:
            if not x in palabrasVacias:
                listaPartes.append(x)
        return self.preprocesamiento.crearDocumentoPattern(listaPartes)

    def obtenerAtributos(self, relevancia,listaUrls):
        puntos = {}
        X = []
        Y = []
        for doc in listaUrls:
            consulta = doc[1]
            documento = doc[0]
            doc = self.mongodb.getDocumento(documento)
            if doc:
                for consultaClase in doc['consultasClase']:
                    if consulta == consultaClase['consulta']:
                        if 'clase' in consultaClase:
                            aux = []
                            for atributo in consultaClase['atributos']:
                                aux.append(consultaClase['atributos'][atributo])
                            if len(aux) == 30:
                                print doc['url']
                            X.append(aux)
                            if int(consultaClase['clase']) > relevancia :
                                y = 1
                            else:
                                y = 0
                            Y.append(y)

        puntos['X'] = X
        puntos['Y'] = Y
        return puntos


    def dividirConjuntoTesting(self,puntos,cantEntrenamiento,cantTest):
        conjuntos = {}
        conjuntos['xEntrenamiento'] = puntos['X'][:int(cantEntrenamiento * len(puntos['X']))]
        conjuntos['xTest'] = puntos['X'][int(cantTest * len(puntos['X'])) * int(-1):]
        conjuntos['yEntrenamiento'] = puntos['Y'][:int(cantEntrenamiento * len(puntos['Y']))]
        conjuntos['yTest'] = puntos['Y'][int(cantTest * len(puntos['Y'])) * int(-1):]
        return conjuntos

    def desordenarLista(self,lista):
        from random import shuffle
        x = [[i] for i in lista]
        shuffle(x)
        return x

    def getAtributosRanking(self, listaUrls,consulta):
        X = []
        name = []
        for url in listaUrls:
            doc = self.mongodb.getDocumento(url)
            if doc:
                for consultaClase in doc['consultasClase']:
                    if consultaClase['consulta'] == consulta:
                        aux = []
                        for atributo in consultaClase['atributos']:
                            aux.append(consultaClase['atributos'][atributo])
                        if aux:
                            X.append(aux)
                            name.append(url)

                            if len(aux) == 30:
                                print doc['url'],consulta
                        else:
                            print "Sin Atributos" + url

        puntos = {}
        puntos['X'] = X
        puntos['name'] = name
        return puntos
