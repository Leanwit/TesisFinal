from SupportVectorMachine.SVM import *
from RankingContribucion.Crank import *
from preprocesamientoController import *
import numpy as np
from sklearn.externals import joblib
from Model.mongodb import *

class RIController:
    preprocesamiento = preprocesamientoController()
    svmNoRelevante = SVM()
    svmRelevante = SVM()
    svmMuyRelevante = SVM()
    isRelevante = 2
    mongodb = MongoDb()
    crank = Crank()

    def __init__(self):
        pass

    def clasificarSVM(self):
        if os.path.exists("Model/SVM/filename.pkl") and load:
            self.predecirListaUrls(conjuntos)

    def initSVM(self,path):
        self.preprocesamiento.lecturaSVM(path)
        self.iniciarSVM(self.svmNoRelevante,"norelevante",1)
        self.iniciarSVM(self.svmRelevante,"relevante",2)
        self.iniciarSVM(self.svmMuyRelevante,"muyrelevante",4)

    def predecirListaUrls(self,puntos):
        svm = joblib.load('Model/SVM/filename.pkl')

        X = puntos['xEntrenamiento']
        Y = puntos['yEntrenamiento']

        predicciones = svm.predict(X)

        print Y
        print "Inicio Prediccion"
        total = len(Y)
        aciertos = 0
        for prediccion, y in zip(predicciones, Y):
            print prediccion, y
            if prediccion == y:
                aciertos += 1

        print float(aciertos) / float(total)
        pass

    def inicializarParametrosIteracion(self):
        parametros = {}

        parametros['inicio'] = 1
        parametros['fin'] = 10
        parametros['incremento'] = 1

        parametros['rangoC'] = np.arange(parametros['inicio'], parametros['fin'], parametros['incremento'])
        parametros['rangoGamma'] = np.arange(parametros['inicio'], parametros['fin'], parametros['incremento'])
        parametros['kernels'] = ['rbf', 'poly', "linear"]

        return parametros

    def inicializarMejorCombinacion(self, parametros):

        mejorCombinacion = {}
        mejorCombinacion['precision'] = 0
        mejorCombinacion['C'] = parametros['inicio']
        mejorCombinacion['gamma'] = parametros['inicio']
        mejorCombinacion['kernel'] = parametros['kernels'][0]
        return mejorCombinacion

    def entrenarSVM(self, svm, parametros, X, Y):

        mejorCombinacion = self.inicializarMejorCombinacion(parametros)
        for kernel in parametros['kernels']:
            for gamma in parametros['rangoGamma']:
                for C in parametros['rangoC']:
                    svm.ajustarParametros(C, kernel, .8,.2, X, Y, gamma=gamma)
                    svm.training()
                    precision = svm.testing()
                    if precision > mejorCombinacion['precision']:
                        mejorCombinacion['precision'] = precision
                        mejorCombinacion['C'] = C
                        mejorCombinacion['gamma'] = gamma
                        mejorCombinacion['kernel'] = kernel
                        print mejorCombinacion
                        print " ---------- "
            print "fin kernel " + kernel

    def predecir(self, svm, X, Y):
        predicciones = svm.predecir(X)
        print "Inicio Prediccion"
        total = len(Y)
        aciertos = 0
        for prediccion, y in zip(predicciones, Y):
            if prediccion == y:
                aciertos += 1
        print float(aciertos) / float(total)

    def iniciarSVM(self,svm,name,limite):
        svm.setearAtributos()

        puntos = svm.obtenerAtributos(limite)
        conjuntos = svm.dividirConjuntoTesting(puntos, .8, .2)

        X = conjuntos['xEntrenamiento']
        Y = conjuntos['yEntrenamiento']

        parametros = self.inicializarParametrosIteracion()

        self.entrenarSVM(svm,parametros, X, Y)

        X = conjuntos['xTest']
        Y = conjuntos['yTest']
        self.predecir(svm,X, Y)

        joblib.dump(svm.instanciaSVM, 'Model/SVM/'+name+'.pkl')
        pass

    def rankingSVM(self, path):
        listaUrls = self.preprocesamiento.leerArchivoUrls(path)
        self.preprocesamiento.lecturaSVM(path,'ranking')
        self.svmRelevante.setearAtributosRanking(listaUrls)
        puntos = self.svmRelevante.getAtributosRanking(listaUrls)
        X = np.array(puntos['X'])

        svmNorelevante = joblib.load('Model/SVM/norelevante.pkl')
        svmRelevante = joblib.load('Model/SVM/relevante.pkl')
        svmMuyrelevante = joblib.load('Model/SVM/muyrelevante.pkl')

        prediccionesNoRelevante = svmNorelevante.predict(X)
        prediccionesRelevante = svmRelevante.predict(X)
        prediccionesMuyRelevante = svmMuyrelevante.predict(X)

        #print len(puntos['X']) , len(prediccionesNoRelevante),len(prediccionesRelevante),len(prediccionesMuyRelevante)

        listaUrls = self.limpiarListaUrls(listaUrls,puntos['name'])
        ranking = []
        for indice , url in enumerate(listaUrls):
            documento = {}
            documento['url'] = url['url']
            documento['score'] = (1-self.preprocesamiento.obtenerVectorSpaceModel(url)) * (prediccionesNoRelevante[indice] + prediccionesRelevante[indice] * 2 + prediccionesMuyRelevante[indice] * 3)
            ranking.append(documento)
            #print url['url'], prediccionNoRelevante, prediccionRelevante, prediccionesMuyRelevante


        listaNueva = sorted(ranking, key=lambda k: k['score'], reverse=True)
        self.escribirRanking("Salida/svm.txt",listaNueva)
        self.metricasEvaluacion(listaNueva)



    def limpiarListaUrls(self, listaUrls, urlsX):
        """limpiar lista de urls que no lograron descargarse"""
        nuevaLista = []
        for url in listaUrls:
            if url['url'] in urlsX:
                nuevaLista.append(url)
        return nuevaLista


    def recall(self,top = 10, listaDocumentos = [],cantidadDocRelevantes = 0):
        relevante = 0
        for unDocumento in listaDocumentos[:top]:
            if int(unDocumento['relevancia']) > self.isRelevante:
                relevante += 1
        if cantidadDocRelevantes != 0:
            recall = str(float(relevante)/float(cantidadDocRelevantes))
        else:
            recall = 0
        return recall

    def precision(self, top=10, listaDocumentos = []):
        cantRelevantes = 0
        for unDocumento in listaDocumentos[:top]:
            if int(unDocumento['relevancia']) > self.isRelevante:
                cantRelevantes += 1
        precision = float(cantRelevantes)/float(top)
        return precision

    def fmeasure(self,recall,precision):
        recall = float(recall)
        precision = float(precision)
        if recall + precision != 0:
            fmeasure = 2 * (float(recall * precision) / float(recall + precision))
        else:
            fmeasure = 0
        return fmeasure

    def calcularCantidadDocumentosRelevantes(self,listaDocumentos = []):
        cantidadDocRelevantes  = 0
        for unDocumento in listaDocumentos:
            if int(unDocumento['relevancia']) > self.isRelevante:
                cantidadDocRelevantes +=1
        return cantidadDocRelevantes

    def precisionPromedio(self,top = 10,listaDocumentos = []):
        total,cant = [0,0]
        listaAux = listaDocumentos
        for indice , unDocumento in enumerate(listaAux[:top]):
            if int(unDocumento['relevancia']) > self.isRelevante:
                total += self.precision(indice + 1,listaDocumentos)
                cant += 1
        if cant == 0:
            return 0
        return str(total/cant)

    def crearListaConRelevancia(self,path):
        archivo = open(path,"r")
        for unaLinea in archivo.readlines():
            if unaLinea:
                campos = unaLinea.split("	,	")
                url = self.preprocesamiento.limpiarUrl(campos[0])
                relevancia = campos[1].split("\n")[0]
                self.mongodb.crearDocumentoRelevancia(url,relevancia)

    def escribirRanking(self, path, lista):
        archivo = open(path, "wb")
        for doc in lista:
            archivo.write(doc['url'] + " , " + str(doc['score']) + "\n")
        archivo.close()
        pass

    def metricasEvaluacion(self, listaNueva):
        listaRelevancia = []
        for doc in listaNueva:
            documento = self.mongodb.getDocumentosRelevancia(doc['url'])
            if documento:
                documentoAux = {}
                documentoAux['url'] = documento['url']
                documentoAux['relevancia'] = documento['relevancia']
                listaRelevancia.append(documentoAux)

        cantidadRelevantes = self.calcularCantidadDocumentosRelevantes(listaRelevancia)
        print cantidadRelevantes
        for top in range(1,30):
            precision = self.precision(top,listaRelevancia)
            recall = self.recall(top,listaRelevancia,cantidadRelevantes)
            fmeasure = self.fmeasure(recall,precision)
            precisionPromedio = self.precisionPromedio(top,listaRelevancia)
            print precision,recall,fmeasure,precisionPromedio


    def crearRelacionesCRank(self,path):
        listaUrls = self.crank.lecturaArchivoCrank(path)
        for parUrls in listaUrls:
            self.crearDocumentosCrank(parUrls['source'],parUrls['target'])
            self.mongodb.crearRelaciones(parUrls['source'],parUrls['target'])

    def crearDocumentosCrank(self, source, target):
        documento = self.mongodb.getDocumento(source)
        if not documento:
            self.preprocesamiento.crearDocumento(source)
        documento = self.mongodb.getDocumento(target)
        if not documento:
            self.preprocesamiento.crearDocumento(target)

    def initCrank(self,metodo="EP",consulta=""):
        self.crearRelacionesCRank("Entrada/crank.txt")
        listaUrls = self.preprocesamiento.leerArchivoUrl("Entrada/urls.txt")
        if metodo == "EP":
            self.crank.calcularRelevancia(consulta)
        elif metodo == "Crank":
            self.crank.calcularRelevanciaCrank(consulta)

        self.crank.calcularScoreContribucion()


