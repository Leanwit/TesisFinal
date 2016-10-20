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


    def setearAtributos(self):
        documentos = self.mongodb.getDocumentosConConsulta()
        listaAtributos = []
        for documento in documentos:
            for consultaClase in documento['consultasClase']:
                atributo = self.crearAtributosSingulares(documento,consultaClase['consulta'])
                self.mongodb.agregarDatosAtributos(documento,consultaClase['consulta'],atributo)
                listaAtributos.append(atributo)

        self.crearAtributosGrupales(listaAtributos)

    def crearAtributosSingulares(self,documento,consulta):
        unDocumentoPattern = Document.load("DocumentoPattern/"+str(documento['_id']))
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

        url = self.urlDocumento(unDocumentoPattern)

        consultaDocumento = self.preprocesamiento.crearDocumentoPattern(consulta, "consulta")
        unAtributo = Atributos(html,url,titulo,urlValues,body,consultaDocumento)
        unAtributo.calcularAtributos()
        return unAtributo


    def crearAtributosGrupales(self,listaAtributos):


        consultas = self.mongodb.obtenerTodasLasConsultas()
        for consulta in consultas:
            listaDocumentosHtml, listaDocumentosBody, listaDocumentosUrlValues, listaDocumentosTitle, listaDocumentosID = ([] for i in range(5))
            listaAtributos = self.mongodb.getAtributosPorConsulta(consulta)
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

    def obtenerAtributos(self, relevancia):
        listaDocumentos = self.mongodb.getDocumentosConConsulta()
        puntos = {}
        X = []
        Y = []
        for doc in listaDocumentos:
            for consultaClase in doc['consultasClase']:
                aux = []
                for atributo in consultaClase['atributos']:
                    aux.append(consultaClase['atributos'][atributo])
                X.append(aux)

                if int(consultaClase['clase']) > relevancia :
                    y = 1
                else:
                    y = 0
                print int(consultaClase['clase']),relevancia,y
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