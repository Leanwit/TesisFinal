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

    def initSVM(self,path):
        print "Inicio Lectura Archivo"
        listaUrls = self.preprocesamiento.lecturaSVM(path)
        print "Fin Lectura Archivo"

        self.iniciarSVM(self.svmNoRelevante,"norelevante",1,listaUrls)
        self.iniciarSVM(self.svmRelevante,"relevante",2,listaUrls)
        self.iniciarSVM(self.svmMuyRelevante,"muyrelevante",4,listaUrls)

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

        parametros['inicio'] = 0.001
        parametros['fin'] = 30
        parametros['incremento'] = 0.1

        #incremento gamma
        parametros['incrementoG'] = 1

        parametros['rangoC'] = np.arange(parametros['inicio'], parametros['fin'], parametros['incremento'])
        parametros['rangoGamma'] = np.arange(parametros['inicio'], parametros['fin'], parametros['incrementoG'])


        #parametros['kernels'] = ['rbf', 'linear', 'poly',]
        parametros['kernels'] = ['rbf']

        return parametros

    def inicializarMejorCombinacion(self, parametros,name):

        mejorCombinacion = {}
        mejorCombinacion['precision'] = 0
        mejorCombinacion['C'] = parametros['rangoC'][0]
        mejorCombinacion['gamma'] = parametros['rangoGamma'][0]
        mejorCombinacion['kernel'] = parametros['kernels'][0]
        mejorCombinacion['name'] = name
        return mejorCombinacion

    def entrenarSVM(self, svm, parametros, X, Y,name):

        mejorCombinacion = self.inicializarMejorCombinacion(parametros,name)
        for kernel in parametros['kernels']:
            for gamma in parametros['rangoGamma']:
                for C in parametros['rangoC']:
                    print C,kernel,gamma
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
        print self.mongodb.escribirParametrosSVM(mejorCombinacion).inserted_id

    def predecir(self, svm, X, Y):
        predicciones = svm.predecir(X)
        print "Inicio Prediccion"
        total = len(Y)
        aciertos = 0
        for prediccion, y in zip(predicciones, Y):
            if prediccion == y:
                aciertos += 1
        print float(aciertos) / float(total)

    def iniciarSVM(self,svm,name,limite,listaUrls):
        #listaUrls = svm.desordenarLista(listaUrls)
        #svm.setearAtributos(listaUrls)

        puntos = svm.obtenerAtributos(limite,listaUrls)

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

    def rankingSVM(self, listaUrls,consulta):
        self.preprocesamiento.lecturaSVMRanking(listaUrls,consulta)
        print "Set Atributos"
        listaUrls = self.svmRelevante.setearAtributosRanking(listaUrls,consulta)
        print "Finis Set Atributos"
        puntos = self.svmRelevante.getAtributosRanking(listaUrls,consulta.name)
        X = np.array(puntos['X'])


        svmNorelevante = joblib.load('Model/SVM/norelevante.pkl')
        svmRelevante = joblib.load('Model/SVM/relevante.pkl')
        svmMuyrelevante = joblib.load('Model/SVM/muyrelevante.pkl')

        prediccionesNoRelevante = svmNorelevante.predict(X)
        prediccionesRelevante = svmRelevante.predict(X)
        prediccionesMuyRelevante = svmMuyrelevante.predict(X)

        #print prediccionesNoRelevante
        #print prediccionesRelevante
        #print prediccionesMuyRelevante
        #print len(puntos['X']) , len(prediccionesNoRelevante),len(prediccionesRelevante),len(prediccionesMuyRelevante)

        listaUrls = self.limpiarListaUrls(listaUrls,puntos['name'])
        ranking = []
        for indice , url in enumerate(listaUrls):
            documento = {}
            documento['url'] = url
            documento['score'] = (1-self.preprocesamiento.obtenerVectorSpaceModel(url,consulta.name)) * (prediccionesNoRelevante[indice] + prediccionesRelevante[indice] * 1.25 + prediccionesMuyRelevante[indice] * 1.5)

            print documento['url'],documento['score'],self.preprocesamiento.obtenerVectorSpaceModel(url,consulta.name),prediccionesNoRelevante[indice] , prediccionesRelevante[indice] * 2 , prediccionesMuyRelevante[indice] * 3
            ranking.append(documento)


        listaNueva = sorted(ranking, key=lambda k: k['score'], reverse=True)
        #self.escribirRanking("Salida/svm.txt",listaNueva)
        #self.metricasEvaluacion(listaNueva,"RankingSVM")

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
        self.mongodb.eliminarBdRelevancia()
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


        tops = [1,5,10,15,20,30,40,50]
        indiceTops = 0
        listaNuevaFmeasure = []
        for indice,fmeasure in enumerate(listaFmeasure[:50]):
            if (indice+1) == tops[indiceTops]:
                indiceTops +=1
                listaNuevaFmeasure.append(fmeasure)

        indiceTops = 0
        listaNuevaMap = []
        for indice, map in enumerate(listaMap[:50]):
            if (indice + 1) == tops[indiceTops]:
                indiceTops += 1
                listaNuevaMap.append(map)

        interpolacion = self.interpolarPrecisionRecall(precisionRecall)

        top5 = self.promedioTop(listaRelevancia, 5)
        top10 = self.promedioTop(listaRelevancia, 10)
        top15 = self.promedioTop(listaRelevancia, 15)
        top20 = self.promedioTop(listaRelevancia, 20)

        metrica = {}
        metrica['interpolacion'] =interpolacion
        metrica['f-medida'] =listaNuevaFmeasure
        metrica['map'] =listaNuevaMap
        metrica['top5'] =top5
        metrica['top10'] =top10
        metrica['top15'] =top15
        metrica['top20'] =top20
        return metrica

        '''print "PrecisionRecall:",interpolacion
        print "Precision:",listaPrecision
        print "Recall:", listaRecall
        print "Fmeasure:",listaFmeasure[:50]
        print "MAP:",listaMap[:50]
        print "Top5:", top5
        print "Top10:", top10
        print "Top15:", top15
        print "Top20:", top20
        print'''


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



    def initCrank(self,metodo="EP",consulta="",listaUrls=""):
        #self.crearRelacionesCRank("Entrada/crank.txt")
        if metodo == "EP":
            self.crank.calcularRelevancia(consulta,"ISP",listaUrls)
        elif metodo == "Crank":
            self.crank.calcularRelevanciaCrank(consulta)

        self.crank.calcularScoreContribucion(listaUrls)

        listaRankeada = self.crank.calcularPuntajeFinal(listaUrls,consulta)
        return listaRankeada

    def iniciarRanking(self,consultas):
        #Entrenar SVM
        #self.initSVM('Entrada/svmEntrenamiento.txt')

        #Crear lista de documentos con relevancia
        self.crearListaConRelevancia('Entrada/listaRelevancia.txt')

        listaSVMs = []
        listasContribucion = []
        listaUrls = self.preprocesamiento.leerArchivoUrl("Entrada/urls.txt")

        for indice,consulta in enumerate(consultas):
            print "Inicio consulta: " , indice+1 , "de", len(consultas), " ->",consulta
            consulta = self.preprocesamiento.crearDocumentoPattern(consulta,consulta)
            listaSvm = self.rankingSVM(listaUrls,consulta)
            listaSVMs.append(listaSvm)

            listaContribucion = self.initCrank("EP",consulta.name,listaUrls)
            listasContribucion.append(listaContribucion)

        self.evaluarMetodos(listaSVMs,"svm")
        self.evaluarMetodos(listasContribucion,"Contribucion")



        listaFinal = self.rankingFinal(listaSVMs,listasContribucion)
        print
        print "Score Final"
        #self.escribirRanking("Salida/final.txt", listaFinal)
        self.evaluarMetodos(listaFinal,"Ranking Final")

        self.imprimirListaTop10(listaSVMs, "RSVM")
        self.imprimirListaTop10(listasContribucion, "Contribucion")
        self.imprimirListaTop10(listaFinal,"Ranking Final")

    def rankingFinal(self, listaSvm, listaContribucion):
        listaFinal = []
        listaAux = []
        for urlSvm, urlContribucion in zip(listaSvm,listaContribucion):

            for indice, url in enumerate(urlSvm):
                if url not in listaAux:
                    documento = {}
                    documento['url'] = url['url']
                    documento['score'] = float(1) / float(indice + 1)
                    listaAux.append(documento)
                else:
                    self.setScore(listaAux,url,indice+1)

            for indice,url in enumerate(urlContribucion):
                self.setScore(listaAux,url,indice+1)

            listaAux = sorted(listaAux, key=lambda k: k['score'], reverse=True)
            listaFinal.append(listaAux)
            listaAux = []
        return listaFinal

    def setScore(self,listaFinal,url,indice):
        for documento in listaFinal:
            if documento['url'] == url['url']:
                documento['score'] += float(1) / float(indice)

    def interpolarPrecisionRecall(self, precisionRecall):
        recall = [0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1]
        precision = []
        indice = 0
        for parPR in precisionRecall:
            if indice < len(recall):
                if float(parPR[1]) >= (recall[indice]):
                    precision.append(parPR[0])
                    indice +=1

        '''Si no alcanza el 100% de la precision'''
        if len(precision) == 10:
            precision.append(precisionRecall[-1][0])
        return precision

    def metodosAlternativos(self,consultas):
        # Crear lista de documentos con relevancia
        self.crearListaConRelevancia('Entrada/listaRelevancia.txt')
        listaUrls = self.preprocesamiento.leerArchivoUrl("Entrada/urls.txt")

        VSM = []
        EP = []
        CRANK = []

        for indice,consulta in enumerate(consultas):
            print "Procesando " + str(indice+1) + " de " + str(len(consultas))
            consulta = self.preprocesamiento.crearDocumentoPattern(consulta, consulta)
            VSM.append(self.rankingVectorSpaceModel(listaUrls,consulta))
            EP.append(self.enfoquePonderado(listaUrls,consulta))
            CRANK.append(self.calcularCrankOriginal(listaUrls,consulta))

        print "VSM"
        self.evaluarMetodos(VSM,"VSM")

        print
        print "EnfoquePonderado"
        self.evaluarMetodos(EP,"EnfoquePonderado")

        print
        print "Crank"
        self.evaluarMetodos(CRANK,"Crank")

        self.imprimirListaTop10(VSM,"VSM")
        self.imprimirListaTop10(EP,"EnfoquePonderado")
        self.imprimirListaTop10(CRANK,"Crank")

    def obtenerPromedioTop(self,listaurls,metrica):
        aux = 0
        for valor in listaurls:
            aux += valor[metrica]
        return float(aux)/float(5)

    def rankingVectorSpaceModel(self, listaUrls, consulta):
        listaUrlsRankeados = []
        for url in listaUrls:
            documento = self.mongodb.getDocumento(url)
            if documento:
                documentoPattern = self.preprocesamiento.getDocumentoPattern(documento['_id'])
                score = self.preprocesamiento.calcularVectorSpaceModel(consulta,documentoPattern)
                listaUrlsRankeados.append(self.crearJsonRanking(url,score))

        listaFinal = sorted(listaUrlsRankeados, key=lambda k: k['score'], reverse=False)
        return listaFinal
        #self.metricasEvaluacion(listaFinal,"Vector Space Model")
        #self.escribirRanking("Salida/vectorSpaceModel.txt", listaFinal)


    def enfoquePonderado(self, listaUrls, consulta, tema = "ISP"):
        listaUrlsRankeados = []
        diccionario = self.crank.getDiccionarioDominio(tema)
        for url in listaUrls:
            documento = self.mongodb.getDocumento(url)
            if documento:
                documentoPattern = self.preprocesamiento.getDocumentoPattern(documento['_id'])
                score = self.crank.calcularEnfoquePonderado(documentoPattern,consulta,diccionario)
                listaUrlsRankeados.append(self.crearJsonRanking(url,score))

        listaFinal = sorted(listaUrlsRankeados, key=lambda k: k['score'], reverse=True)
        return listaFinal
        #self.metricasEvaluacion(listaFinal,"Enfoque Ponderado")
        #self.escribirRanking("Salida/enfoqueponderado.txt", listaFinal)

    def crearJsonRanking(self,url,score):
        documento = {}
        documento['url'] = url
        documento['score'] = score
        return documento

    def calcularCrankOriginal(self, listaUrls, consulta):
        listaUrlsRankeados = []
        self.crank.calcularRelevanciaCrank(consulta,listaUrls)
        for url in listaUrls:
            documento = self.mongodb.getDocumento(url)
            if documento:
                documentoPattern = self.preprocesamiento.getDocumentoPattern(documento['_id'])
                score = documento['relevanciaCrank']
                listaUrlsRankeados.append(self.crearJsonRanking(url,score))

        listaFinal = sorted(listaUrlsRankeados, key=lambda k: k['score'], reverse=True)
        return listaFinal
        #self.metricasEvaluacion(listaFinal, "Crank")
        #self.escribirRanking("Salida/crankOriginal.txt", listaFinal)

    def promedioTop(self, listaRelevancia,top):
        contador = 0
        for url in listaRelevancia[:top]:
            contador += int(url['relevancia'])
        return float(contador)/float(top)

    def obtenerMetrica(self, listaurls, metrica):
        valores = []
        for unaMetrica in listaurls:
            valores.append(unaMetrica[metrica])
        valoresFinales = []
        for m1, m2, m3, m4, m5 in zip(valores[0], valores[1], valores[2], valores[3], valores[4]):
            suma = float(m1) + float(m2) + float(m3) + float(m4) + float(m5)
            valoresFinales.append(suma / float(5))


        return valoresFinales

    def evaluarMetodos(self, rankings, metodo):
        metrica = []
        for ranking in rankings:
            metrica.append(self.metricasEvaluacion(ranking,metodo))

        print metodo
        print "Presicion/Recall", self.obtenerMetrica(metrica, "interpolacion")
        print "FMeasure", self.obtenerMetrica(metrica, "f-medida")
        print "Map", self.obtenerMetrica(metrica, "map")
        print "top", self.obtenerPromedioTop(metrica, "top5"),",",self.obtenerPromedioTop(metrica, "top10"),",",self.obtenerPromedioTop(metrica, "top15"),",", self.obtenerPromedioTop(metrica, "top20")
        print "\n\n"


    def imprimirListaTop10(self,lista,nombre):
        print "INICIO ", nombre
        for listaDocumentos in lista:
            for documento in listaDocumentos[:10]:
                relevancia = self.mongodb.getDocumentosRelevancia(documento['url'])
                print documento['url'],";",documento['score'],";",relevancia['relevancia']
            print