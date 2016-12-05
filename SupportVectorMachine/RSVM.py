from sklearn.externals import joblib

from preprocesamientoController import *
from pattern.vector import Document,Model, distance, COSINE
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

        modelos = {}
        modelos['documento'] = self.preprocesamiento.crearModelo(listaDocumentosHtml)
        modelos['body'] = self.preprocesamiento.crearModelo(listaDocumentosBody)
        modelos['urlValues'] = self.preprocesamiento.crearModelo(listaDocumentosUrlValues)
        modelos['title'] = self.preprocesamiento.crearModelo(listaDocumentosTitle)

        consulta = self.preprocesamiento.crearDocumentoPattern(consulta,consulta)
        unAtributo = Atributos()

        unAtributo.calcularAtributosCorpus(modelos,consulta,listaDocumentos)

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
                            if "atributos" in consultaClase:
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


    def rankingSVM(self, listaUrls, consulta, parametros):
        """ metodo para rankear una lista de urls mediante el algoritmo RSVM
            Entrada:
                listaUrls: lista de los urls para rankear
                consulta: consulta de busqueda en cadena de caracteres
                parametros: parametros
            Salida:
                lista de urls rankeados
        """

        self.preprocesamiento.lecturaSVMRanking(listaUrls, consulta)

        """ creacion de atributos para cada enlace"""
        listaUrls = self.setearAtributosRanking(listaUrls, consulta)

        """se obtiene los puntos para realizar el ranking"""
        puntos = self.getAtributosRanking(listaUrls, consulta.name)
        X = np.array(puntos['X'])

        svmNorelevante = joblib.load('Model/SVM/norelevante.pkl')
        svmRelevante = joblib.load('Model/SVM/relevante.pkl')
        svmMuyrelevante = joblib.load('Model/SVM/muyrelevante.pkl')

        prediccionesNoRelevante = svmNorelevante.predict(X)
        prediccionesRelevante = svmRelevante.predict(X)
        prediccionesMuyRelevante = svmMuyrelevante.predict(X)

        listaUrls = self.preprocesamiento.limpiarListaUrls(listaUrls, puntos['name'])
        ranking = []

        modeloLista = []
        for url in listaUrls:
            documento = self.mongodb.getDocumento(url)
            if documento:
                documentoPattern = self.preprocesamiento.getDocumentoPattern(documento['_id'])
                modeloLista.append(documentoPattern)

        unModelo = Model(modeloLista)

        """calculo del puntaje de ranking SVM"""
        for indice, doc in enumerate(unModelo):
            url = doc.name
            documento = {}
            documento['url'] = url
            documento['score'] = (1-self.obtenerVectorSpaceModel(doc,consulta)) + (prediccionesNoRelevante[indice] + prediccionesRelevante[indice] * parametros[1] + prediccionesMuyRelevante[indice] * parametros[2])
            ranking.append(documento)

        listaNueva = sorted(ranking, key=lambda k: k['score'], reverse=True)
        return listaNueva

    def obtenerVectorSpaceModel(self, url,consulta):
        docBD = self.mongodb.getDocumento(url.name)
        documento = self.preprocesamiento.getDocumentoPattern(docBD['_id'])
        consulta = self.preprocesamiento.crearDocumentoPattern(consulta,consulta)
        if docBD and documento:
            return self.calcularVectorSpaceModel(documento,consulta)
        return 1

    def calcularVectorSpaceModel(self, doc1, doc2):
        return distance(doc1.vector,doc2.vector,method=COSINE)