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
        errores = 0
        prediccion = self.predecir(self.xTest)
        cantidadTotal = len(self.xTest)
        for unaClase,unaPrediccion in zip(self.yTest,prediccion):
            if unaClase != unaPrediccion:
                errores +=1
        aciertos = cantidadTotal - errores
        return round((aciertos*100)/cantidadTotal,3)

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

        '''self.crearAtributosGrupales(listaAtributos,consulta)'''

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


    def crearAtributosGrupales(self,listaAtributos,consulta):
        listaDocumentosHtml, listaDocumentosBody, listaDocumentosUrlValues, listaDocumentosTitle, listaDocumentosID = ([] for i in range(5))
        for unAtributo in listaAtributos:
            listaDocumentosHtml.append(unAtributo.html)
            listaDocumentosBody.append(unAtributo.body)
            listaDocumentosUrlValues.append(unAtributo.urlValues)
            listaDocumentosTitle.append(unAtributo.titulo)

        modelos = {}
        modelos['documento'] = self.preprocesamiento.crearModelo(listaDocumentosHtml)
        modelos['body'] = self.preprocesamiento.crearModelo(listaDocumentosBody)
        modelos['urlValues'] = self.preprocesamiento.crearModelo(listaDocumentosUrlValues)
        modelos['title'] = self.preprocesamiento.crearModelo(listaDocumentosTitle)

        listaDocumentos = self.mongodb.getDocumentosConsulta(consulta)
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

    def obtenerAtributos(self,consulta):
        listaDocumentos = self.mongodb.getDocumentosConsulta(consulta)
        puntos = {}
        X = []
        Y = []
        for doc in listaDocumentos:
            aux = []
            for atributo in doc['atributosConsulta']['atributos']:
                aux.append(doc['atributosConsulta']['atributos'][atributo])
            X.append(aux)
            Y.append(doc['relevancia']['clase'])

        puntos['X'] = X
        puntos['Y'] = Y
        return puntos