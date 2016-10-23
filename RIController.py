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

        parametros['inicio'] = 0.01
        parametros['fin'] = 100
        parametros['incremento'] = 0.5

        parametros['rangoC'] = np.arange(parametros['inicio'], parametros['fin'], parametros['incremento'])
        parametros['rangoGamma'] = np.arange(parametros['inicio'], parametros['fin'], parametros['incremento'])
        parametros['kernels'] = ['rbf', 'poly', "linear"]

        return parametros

    def inicializarMejorCombinacion(self, parametros,name):

        mejorCombinacion = {}
        mejorCombinacion['precision'] = 0
        mejorCombinacion['C'] = parametros['inicio']
        mejorCombinacion['gamma'] = parametros['inicio']
        mejorCombinacion['kernel'] = parametros['kernels'][0]
        mejorCombinacion['name'] = name
        return mejorCombinacion

    def entrenarSVM(self, svm, parametros, X, Y,name):

        mejorCombinacion = self.inicializarMejorCombinacion(parametros,name)
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
        self.mongodb.escribirParametrosSVM(mejorCombinacion)

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

        self.entrenarSVM(svm,parametros, X, Y,name)

        X = conjuntos['xTest']
        Y = conjuntos['yTest']
        self.predecir(svm,X, Y)

        joblib.dump(svm.instanciaSVM, 'Model/SVM/'+name+'.pkl')
        pass

    def rankingSVM(self, path,consulta):
        listaUrls = self.preprocesamiento.leerArchivoUrl(path)
        self.preprocesamiento.lecturaSVMRanking(listaUrls,consulta)
        listaUrls = self.svmRelevante.setearAtributosRanking(listaUrls,consulta)
        puntos = self.svmRelevante.getAtributosRanking(listaUrls,consulta)
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
            documento['url'] = url
            documento['score'] = (1-self.preprocesamiento.obtenerVectorSpaceModel(url,consulta)) * (prediccionesNoRelevante[indice] + prediccionesRelevante[indice] * 2 + prediccionesMuyRelevante[indice] * 3)
            ranking.append(documento)
            #print url['url'], prediccionNoRelevante, prediccionRelevante, prediccionesMuyRelevante


        listaNueva = sorted(ranking, key=lambda k: k['score'], reverse=True)
        self.escribirRanking("Salida/svm.txt",listaNueva)
        self.metricasEvaluacion(listaNueva,"RankingSVM")

        return listaNueva


    def limpiarListaUrls(self, listaUrls, urlsX):
        """limpiar lista de urls que no lograron descargarse"""
        nuevaLista = []
        for url in listaUrls:
            if url in urlsX:
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

    def metricasEvaluacion(self, listaNueva,metodoRanking):
        print metodoRanking
        listaRelevancia = []
        for doc in listaNueva:
            documento = self.mongodb.getDocumentosRelevancia(doc['url'])
            if documento:
                documentoAux = {}
                documentoAux['url'] = documento['url']
                documentoAux['relevancia'] = documento['relevancia']
                listaRelevancia.append(documentoAux)



        cantidadRelevantes = self.calcularCantidadDocumentosRelevantes(listaRelevancia)
        precisionRecall = []
        listaFmeasure = []
        listaMap = []
        listaPrecision = []
        listaRecall = []
        for top in range(1,len(listaRelevancia)):
            precision = self.precision(top,listaRelevancia)
            recall = self.recall(top,listaRelevancia,cantidadRelevantes)
            fmeasure = self.fmeasure(recall,precision)
            precisionPromedio = self.precisionPromedio(top,listaRelevancia)

            listaPrecision.append(precision)
            listaRecall.append(recall)
            listaFmeasure.append(fmeasure)
            listaMap.append(precisionPromedio)
            precisionRecall.append([precision,recall])
        interpolacion = self.interpolarPrecisionRecall(precisionRecall)

        top5 = self.promedioTop(listaRelevancia, 5)
        top10 = self.promedioTop(listaRelevancia, 10)

        print "PrecisionRecall ",interpolacion
        print "Precision ",listaPrecision
        print "Recall ", listaRecall
        print "Fmeasure ",listaFmeasure
        print "MAP ",listaMap
        print "Top5", top5
        print "Top10", top10
        print


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

        listaRankeada = self.crank.calcularPuntajeFinal(listaUrls,consulta)
        self.escribirRanking("Salida/sc.txt", listaRankeada)
        self.metricasEvaluacion(listaRankeada,"RankingContribucion")

        return listaRankeada

    def iniciarRanking(self,consulta):
        #Entrenar SVM
        #self.initSVM('Entrada/svmEntrenamiento.txt')

        #Crear lista de documentos con relevancia
        self.crearListaConRelevancia('Entrada/listaRelevancia.txt')

        #Ranking SVM
        listaSvm = self.rankingSVM('Entrada/urls.txt',consulta)

        #Ranking Contribucion
        listaContribucion = self.initCrank("EP",consulta)


        listaFinal = self.rankingFinal(listaSvm,listaContribucion)
        print "Score Final"
        self.escribirRanking("Salida/final.txt", listaFinal)
        self.metricasEvaluacion(listaFinal,"Ranking Final")

    def rankingFinal(self, listaSvm, listaContribucion):
        listaFinal = []
        for indice, url in enumerate(listaSvm):
            documento = {}
            documento['url'] = url['url']
            documento['score'] = float(1) / float(indice + 1)
            listaFinal.append(documento)

        for indice, url in enumerate(listaContribucion):
            for auxUrl in listaFinal:
                if auxUrl['url'] == url['url']:
                    auxUrl['score'] += float(1) / float(indice + 1)

        listaFinal = sorted(listaFinal, key=lambda k: k['score'], reverse=True)
        return listaFinal

    def interpolarPrecisionRecall(self, precisionRecall):
        recall = [0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1]
        precision = []
        indice = 0
        for parPR in precisionRecall:
            if indice < len(recall):
                if float(parPR[1]) > (recall[indice]):
                    precision.append(parPR[0])
                    indice +=1
        return precision

    def metodosAlternativos(self,consulta):
        listaUrls = self.preprocesamiento.leerArchivoUrl("Entrada/urls.txt")
        consulta = self.preprocesamiento.crearDocumentoPattern(consulta, "consulta")

        self.rankingVectorSpaceModel(listaUrls,consulta)
        self.enfoquePonderado(listaUrls,consulta)
        self.calcularCrankOriginal(listaUrls,consulta)


    def rankingVectorSpaceModel(self, listaUrls, consulta):
        listaUrlsRankeados = []
        for url in listaUrls:
            documento = self.mongodb.getDocumento(url)
            if documento:
                documentoPattern = self.preprocesamiento.getDocumentoPattern(documento['_id'])
                score = self.preprocesamiento.calcularVectorSpaceModel(consulta,documentoPattern)
                listaUrlsRankeados.append(self.crearJsonRanking(url,score))

        listaFinal = sorted(listaUrlsRankeados, key=lambda k: k['score'], reverse=True)
        self.metricasEvaluacion(listaFinal,"Vector Space Model")
        self.escribirRanking("Salida/vectorSpaceModel.txt", listaFinal)


    def enfoquePonderado(self, listaUrls, consulta,tema = "Tea"):
        listaUrlsRankeados = []
        diccionario = self.crank.getDiccionarioDominio(tema)
        for url in listaUrls:
            documento = self.mongodb.getDocumento(url)
            if documento:
                documentoPattern = self.preprocesamiento.getDocumentoPattern(documento['_id'])
                score = self.crank.calcularEnfoquePonderado(documentoPattern,consulta,diccionario)
                listaUrlsRankeados.append(self.crearJsonRanking(url,score))

        listaFinal = sorted(listaUrlsRankeados, key=lambda k: k['score'], reverse=True)
        self.metricasEvaluacion(listaFinal,"Enfoque Ponderado")
        self.escribirRanking("Salida/enfoqueponderado.txt", listaFinal)


    def crearJsonRanking(self,url,score):
        documento = {}
        documento['url'] = url
        documento['score'] = score
        return documento

    def calcularCrankOriginal(self, listaUrls, consulta):
        listaUrlsRankeados = []
        self.crank.calcularRelevanciaCrank(consulta)
        for url in listaUrls:
            documento = self.mongodb.getDocumento(url)
            if documento:
                documentoPattern = self.preprocesamiento.getDocumentoPattern(documento['_id'])
                score = documento['relevanciaCrank']
                listaUrlsRankeados.append(self.crearJsonRanking(url,score))

        listaFinal = sorted(listaUrlsRankeados, key=lambda k: k['score'], reverse=True)
        self.metricasEvaluacion(listaFinal, "Crank")
        self.escribirRanking("Salida/crankOriginal.txt", listaFinal)

    def promedioTop(self, listaRelevancia,top):
        contador = 0
        for url in listaRelevancia[:top]:
            contador += int(url['relevancia'])
        return float(contador)/float(top)