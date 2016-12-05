from SupportVectorMachine.RSVM import *
from RankingContribucion.RC import *
from preprocesamientoController import *
import numpy as np
from sklearn.externals import joblib
from Model.mongodb import *
from pattern.vector import Model , distance, COSINE

class RIController:

    preprocesamiento = preprocesamientoController()

    isRelevante = 2
    mongodb = MongoDb()
    rc = RC()

    def __init__(self):
        self.svm = SVM()
        self.svmNoRelevante = SVM()
        self.svmRelevante = SVM()
        self.svmMuyRelevante = SVM()

    def recall(self,top = 10, listaDocumentos = [],cantidadDocRelevantes = 0):
        """Metodo para calcular el recall de una lista de documentos
        Entrada: Top a anlizar, lista de documentos con su relevancia, y la cantidad de documentos relevantes existentes para el top a analizar
        Salida: valor del recall"""
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
        """Metodo para obtener la precision de una lista de documentos
        Entrada: Top a anlizar, lista de documentos con su relevancia, y la cantidad de documentos relevantes existentes para el top a analizar
        Salida: valor de precision"""
        cantRelevantes = 0
        for unDocumento in listaDocumentos[:top]:
            if int(unDocumento['relevancia']) > self.isRelevante:
                cantRelevantes += 1
        precision = float(cantRelevantes)/float(top)
        return precision

    def fmeasure(self,recall,precision):
        """metodo para obtener la medida-F.
        Entrada: Recall y precision"""
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
        """Metodo para calcular MAP
        Entrada: Top y la lista de documentos.
        Salida: Valor MAP"""
        total,cant = [0,0]
        listaAux = listaDocumentos
        for indice , unDocumento in enumerate(listaAux[:top]):
            if int(unDocumento['relevancia']) > self.isRelevante:
                total += self.precision(indice + 1,listaDocumentos)
                cant += 1
        if cant == 0:
            return 0
        return str(total/cant)



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

        """ Calculo de Precision, Recall, Medida-F y MAP"""
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

        """F-Medida y MAP para determinados tops"""
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

        ruido10 = self.getRuido(listaRelevancia,10)
        ruido20 = self.getRuido(listaRelevancia,20)
        ruido50 = self.getRuido(listaRelevancia,50)


        ultimoDocumentoRecuperado = self.getUltimoRecuperado(listaRelevancia)
        urlsUltimosDocumentos = self.getUltimosUrlsRecuperados(listaRelevancia)

        """diccionario con los valores de la metrica"""
        metrica = {}
        metrica['interpolacion'] =interpolacion
        metrica['FMedida'] =listaNuevaFmeasure
        metrica['map'] =listaNuevaMap
        metrica['top5'] =top5
        metrica['top10'] =top10
        metrica['top15'] =top15
        metrica['top20'] =top20
        metrica['ruido'] = [ruido10,ruido20,ruido50]
        metrica['ultimoRecuperado'] = ultimoDocumentoRecuperado

        return metrica

    def getUltimoRecuperado(self,listaRelevancia):
        pos = []
        for indice,unaUrl in enumerate(listaRelevancia):
            if int(unaUrl['relevancia']) > self.isRelevante:
                pos.append(indice)
        return pos

    def getUltimosUrlsRecuperados(self, listaRelevancia):
        urls = []
        for indice, unaUrl in enumerate(listaRelevancia):
            if int(unaUrl['relevancia']) > self.isRelevante:
                if indice > 200:
                    urls.append(unaUrl['url'])
        return urls

    def getRuido(self,listaRelevancia,top):
        cantidadNoRelevante = 0
        for unDocumento in listaRelevancia[:top]:
            if int(unDocumento['relevancia']) < (self.isRelevante+1):
                cantidadNoRelevante +=1
        return float(cantidadNoRelevante)/float(top)

    def crearRelacionesCRank(self,path):
        """Creacion de las relaciones de enlaces entrantes y salientes de los documentos Web"""
        listaUrls = self.rc.lecturaArchivoCrank(path)
        for parUrls in listaUrls:
            self.crearDocumentosCrank(parUrls['source'],parUrls['target'])
            self.mongodb.crearRelaciones(parUrls['source'],parUrls['target'])

    def crearDocumentosCrank(self, source, target):
        """Creacion de documentos C-rank en la base de datos"""
        documento = self.mongodb.getDocumento(source)
        if not documento:
            self.preprocesamiento.crearDocumento(source)
        documento = self.mongodb.getDocumento(target)
        if not documento:
            self.preprocesamiento.crearDocumento(target)


    def initCrank(self,metodo="EP",consulta="",listaUrls="", parametrosCrank=[],tema = ""):
        """Inicializacion del metodo Crank
           Entrada: Consulta de busqueda, lista de urls a rankear, parametros de configuracion y el escenario a evaluar
               Metodo = EP -> para utilizar enfoque ponderado como calculo de relevancia
               Metodo = CRank -> para utilizar el rc como calculo de relevancia
           Salida: Lista de urls rankeados """

        #self.crearRelacionesCRank("Entrada/rc.txt")
        if metodo == "EP":
            self.rc.calcularRelevancia(consulta,tema,listaUrls,parametrosCrank)
        elif metodo == "Crank":
            self.rc.calcularRelevanciaCrank(consulta,listaUrls,tema)

        self.rc.calcularScoreContribucion(listaUrls,parametrosCrank = parametrosCrank)

        listaRankeada = self.rc.calcularPuntajeFinal(listaUrls,parametro=parametrosCrank)
        return listaRankeada


    def getConsultasTema(self,tema,claseConsulta = ""):
        """Metodo con las consultas de busquedas definidas"""
        if not claseConsulta == "secundario":
            consultasTree = ["Trees AND inserts AND avl AND create AND Balanced", "Trees AND search AND balanced AND trim","B+ Tree AND remove AND pruning AND Balanced AND papers","trees AND recursive AND balanced AND nodes AND insert AND data structure AND patents OR paper OR cite","trees AND root AND node AND recursive AND optimization AND search AND b++ AND avl"]
            consultasValueAdded = ["Tea AND alternative AND new AND Value added AND patents OR paper OR cite","sell OR buy AND Tea AND value added AND products AND alimentation","Tea AND products AND medicine AND health AND patents OR paper OR cite","Tea AND innovations AND competitive AND marketing AND strategies AND Value added AND patents OR paper OR cite","tea AND food AND black AND green AND exports AND value added AND patents OR paper OR cite"]
            consultasTechnology = ["buy AND Tea AND Machinery AND Production", "Tea AND machinery AND process AND harvest","buy AND Tea AND plantation AND Technology AND Machinery","tea AND system AND irrigation AND harvest AND production AND manufacturers AND technology AND patents OR paper OR cite","buy AND tea AND lower cost AND technology AND machinery AND harvest"]
            consultasBGP = ["bgp AND isp AND connection AND dual-homed AND patents OR paper OR cite","bgp AND isp AND keepalive AND messages","bgp AND Configurations AND Environments AND single isp AND multihoming","bgp AND routing AND wan AND configuration AND one isp AND two links AND patents OR paper OR cite.","bgp AND Dual Internet AND route AND connections AND patents OR paper OR cite"]
        else:
            consultasTree = ["trees balanced AND trim balanced trees AND create balanced trees AND delete balance trees AND pruning balanced trees AND algorithms AND methods AND techniques"]
            consultasValueAdded = ["tea added value AND tea products for health AND tea products for alimentation AND new products with tea AND tea product differentiation "]
            consultasTechnology = ["technology for tea production AND machinery for plantation of tea AND tea processing machinery AND tea harvest machinery"]
            consultasBGP = ["border gateway protocol AND bgp dual homed connection to one isp AND bgp multihoming with single isp AND bgp two link to one isp AND bgp dual-homed connection to one isp AND configurations AND service provider internet"]

        if tema == "Value":
            return consultasValueAdded
        elif tema == "Tech":
            return consultasTechnology
        elif tema == "Tree":
            return consultasTree
        elif tema == "BGP":
            return consultasBGP


    def iniciarRanking(self,parametros,parametrosCrank,tema):
        """Metodo para realizar el ranking unificado
        Entrada: Parametros del SVM y Crank, escenario a evaluar"""
        consultas = self.getConsultasTema(tema)

        #Entrenar SVM
        #self.initSVM('Entrada/svmEntrenamiento.txt')

        #Crear lista de documentos con relevancia
        self.preprocesamiento.crearListaConRelevancia('Entrada/listaRelevancia'+tema+'.txt')

        listaSVMs = []
        listasContribucion = []
        listaUrls = self.preprocesamiento.leerArchivoUrl("Entrada/urls"+tema+".txt")

        """ranking por cada consulta definida"""
        for indice,consulta in enumerate(consultas):

            consulta = self.preprocesamiento.crearDocumentoPattern(consulta,consulta)
            """ranking svm"""

            listaSvm = self.svm.rankingSVM(listaUrls,consulta,parametros)
            listaSVMs.append(listaSvm)
            """ranking contribucion"""

            listaContribucion = self.initCrank("EP",consulta.name,listaUrls,parametrosCrank,tema)
            listasContribucion.append(listaContribucion)

        """ranking final utilizado los dos rankings anteriores"""
        listaFinal = self.rankingFinal(listaSVMs,listasContribucion)

        """evaluacion del rendimiento de los algoritmos"""
        self.evaluarMetodos(listaSVMs, "svm")
        self.evaluarMetodos(listasContribucion, "Contribucion")
        self.evaluarMetodos(listaFinal,"Ranking Final")

        #self.imprimirListaTop10(listaSVMs, "RSVM")
        #self.imprimirListaTop10(listasContribucion, "Contribucion")
        #self.imprimirListaTop10(listaFinal,"Ranking Final")


    def rankingFinal(self, listaSvm, listaContribucion):
        """Metodo del ranking reciproco para crear el ranking final
        Entrada: La lista del RSVM ordenado, la lista del RC ordenado"""
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
        """Set puntaje reciproco"""
        for documento in listaFinal:
            if documento['url'] == url['url']:
                documento['score'] += float(1) / float(indice)

    def interpolarPrecisionRecall(self, precisionRecall):
        """metodo para obtener los valores de preicision y recall interpolados"""
        recall = [0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1]
        precision = []
        indice = 0
        for parPR in precisionRecall:
            if indice < len(recall):
                if float(parPR[1]) >= (recall[indice]):
                    precision.append(parPR[0])
                    indice +=1

        """Si no alcanza el 100% de la precision"""
        if len(precision) == 10:
            precision.append(precisionRecall[-1][0])
        return precision

    def metodosAlternativos(self,tema,parametrosCrank):
        """Metodo para rankear con los algoritmo EP, C-Rank y VSM"""
        consultas = self.getConsultasTema(tema)

        # Crear lista de documentos con relevancia
        self.preprocesamiento.crearListaConRelevancia('Entrada/listaRelevancia'+tema+'.txt')
        listaUrls = self.preprocesamiento.leerArchivoUrl("Entrada/urls"+tema+".txt")

        VSM = []
        EP = []
        CRANK = []

        for indice,consulta in enumerate(consultas):
            consulta = self.preprocesamiento.crearDocumentoPattern(consulta, consulta)
            VSM.append(self.rankingVectorSpaceModel(listaUrls,consulta))
            EP.append(self.enfoquePonderado(listaUrls,consulta,tema))
            CRANK.append(self.calcularCrankOriginal(listaUrls,consulta,parametrosCrank))


        self.evaluarMetodos(VSM,"VSM")
        self.evaluarMetodos(EP,"EnfoquePonderado")
        self.evaluarMetodos(CRANK,"Crank")

        #self.imprimirListaTop10(VSM,"VSM")
        #self.imprimirListaTop10(EP,"EnfoquePonderado")
        #self.imprimirListaTop10(CRANK,"Crank")

    def ndcg(self,listas,name):
        """Metodo para obtener la normalizacion del descuento de la ganancia acumulada"""
        tops = [5, 10, 20, 30, 50]
        resultados = [0,0,0,0,0]

        for unaLista in listas:
            relevancia = []
            for indice, documento in enumerate(unaLista):
                unaRelevancia = self.mongodb.getDocumentosRelevancia(documento['url'])
                relevancia.append(unaRelevancia['relevancia'])
            for indice,top in enumerate(tops):
                resultados[indice] += self.ndcg_at_k(relevancia,top)

        for indice,aux in enumerate(resultados):
            resultados[indice] = float(aux)/float(len(listas))

        return resultados

    def dcg_at_k(self,r, k, method=0):
        """Obtenido de https://gist.github.com/bwhite/3726239#file-rank_metrics-py-L152"""
        r = np.asfarray(r)[:k]
        if r.size:
            if method == 0:
                return r[0] + np.sum(r[1:] / np.log2(np.arange(2, r.size + 1)))
            elif method == 1:
                return np.sum(r / np.log2(np.arange(2, r.size + 2)))
            else:
                raise ValueError('method must be 0 or 1.')
        return 0.


    def ndcg_at_k(self,r, k, method=0):
        """Obtenido de https://gist.github.com/bwhite/3726239#file-rank_metrics-py-L195"""
        dcg_max = self.dcg_at_k(sorted(r, reverse=True), k, method)
        if not dcg_max:
            return 0.
        return self.dcg_at_k(r, k, method) / dcg_max

    def obtenerPromedioTop(self,listaurls,metrica):
        aux = 0
        for valor in listaurls:
            aux += valor[metrica]
        return float(aux)/float(5)

    def rankingVectorSpaceModel(self, listaUrls, consulta):
        """metodo para el ranking mediante VSM
        Entrada: Consulta de busqueda en string, y lista de urls
        Salida: lista final rankeado"""
        listaUrlsRankeados = []
        listaModel = []
        for url in listaUrls:
            documento = self.mongodb.getDocumento(url)
            if documento:
                documentoPattern = self.preprocesamiento.getDocumentoPattern(documento['_id'])
                listaModel.append(documentoPattern)

        unModelo = Model(listaModel,weight=TFIDF)
        for unDocumento in unModelo:
            score = self.svm.calcularVectorSpaceModel(consulta,unDocumento)
            listaUrlsRankeados.append(self.crearJsonRanking(unDocumento.name,score))

        listaFinal = sorted(listaUrlsRankeados, key=lambda k: k['score'], reverse=False)

        return listaFinal



    def enfoquePonderado(self, listaUrls, consulta, tema = "ISP"):
        """Metodo para el ranking del enfoque ponderado
        Entrada: Lista de urls y consulta en cadena de caracteres"""
        listaUrlsRankeados = []
        diccionario = self.rc.getDiccionarioDominio(tema)
        for url in listaUrls:
            documento = self.mongodb.getDocumento(url)
            if documento:
                documentoPattern = self.preprocesamiento.getDocumentoPattern(documento['_id'])
                score = self.rc.calcularEnfoquePonderado(documentoPattern,consulta,diccionario, {"AN":0.5,"AP":0.75,"AC":1})
                listaUrlsRankeados.append(self.crearJsonRanking(url,score))

        listaFinal = sorted(listaUrlsRankeados, key=lambda k: k['score'], reverse=True)
        return listaFinal


    def crearJsonRanking(self,url,score):
        documento = {}
        documento['url'] = url
        documento['score'] = score
        return documento

    def calcularCrankOriginal(self, listaUrls, consulta,parametrosCrank):
        """
        Metodo para calcular el ranking Crank mediante el calculo de relevanciao original
        Entrada: Lista de urls y consulta en cadena de caracteres.
        Salida: Lista de urls rankeados
        """
        listaUrlsRankeados = []
        self.rc.calcularRelevanciaCrank(consulta,listaUrls)
        self.rc.calcularScoreContribucion(listaUrls,"relevanciaCrank",parametrosCrank={"niveles":3,"factorContribucion":0.2})
        self.rc.calcularPuntajeFinal(listaUrls,parametro={"niveles":3,"factorContribucion":0.2})

        for url in listaUrls:
            documento = self.mongodb.getDocumento(url)
            if documento:
                score = documento['relevanciaCrank']
                listaUrlsRankeados.append(self.crearJsonRanking(url,score))

        listaFinal = sorted(listaUrlsRankeados, key=lambda k: k['score'], reverse=True)
        return listaFinal

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
        if len(valores) == 5:
            for m1, m2, m3, m4, m5 in zip(valores[0], valores[1], valores[2], valores[3], valores[4]):
                suma = float(m1) + float(m2) + float(m3) + float(m4) + float(m5)
                valoresFinales.append(suma / float(5))
        else:
            return valores
        return valoresFinales


    def evaluarMetodos(self, rankings, metodo):
        """Metodo para evaluar el rendimiento de los algoritmos
         Entrada: lista de urls y algoritmo evaluado
         """
        metrica = []
        for ranking in rankings:
            metrica.append(self.metricasEvaluacion(ranking,metodo))


        print metodo
        metricas = {}
        metricas['interpolacion'] = self.obtenerMetrica(metrica, "interpolacion")
        metricas['FMedida'] = self.obtenerMetrica(metrica, "FMedida")
        metricas['MAP'] = self.obtenerMetrica(metrica, "map")
        metricas['ndcg'] = self.ndcg(rankings, metodo)
        metricas['ruido'] = self.obtenerMetrica(metrica,"ruido")
        metricas['ultimoRecuperado'] = self.obtenerMetrica(metrica,"ultimoRecuperado")
        self.escribirTxt(metricas,metodo)

    def escribirTxt(self,metricas,metodo):
        f = open("Salida/resultados","a")
        self.escribirMetrica(f,metodo,metricas)
        f.close()


    def escribirMetrica(self,f,nombre,lista):
        string = "\n"+nombre+"\n"
        for metrica in lista:
                string += metrica + "-"
                for unValor in lista[metrica]:
                    string += str(unValor)+","
                string+= "\n"
        f.write(string)

    def imprimirListaTop10(self,lista,nombre):
        """metodo para imprimir los primeros 10 documentos de una lista rankeada"""
        print "INICIO ", nombre
        for listaDocumentos in lista:
            for documento in listaDocumentos[:10]:
                relevancia = self.mongodb.getDocumentosRelevancia(documento['url'])
                print documento['url'],";",documento['score'],";",relevancia['relevancia']
            print


    def imprimirLista(self,lista,nombre):
        print "INICIO ", nombre
        for documento in lista:
            relevancia = self.mongodb.getDocumentosRelevancia(documento['url'])
            print documento['url'],";",documento['score'],";",relevancia['relevancia']
        print

    def metodoSecundario(self, tema):
        consultas = self.getConsultasTema(tema,"secundario")

        # Crear lista de documentos con relevancia
        self.preprocesamiento.crearListaConRelevancia('Secundario/listaRelevancia' + tema + '.txt')
        listaUrls = self.preprocesamiento.leerArchivoUrl("Secundario/urls" + tema + ".txt")

        EP = []
        CRANK = []
        VSM = []

        for indice, consulta in enumerate(consultas):
            print "Procesando " + str(indice + 1) + " de " + str(len(consultas))
            consulta = self.preprocesamiento.crearDocumentoPattern(consulta, consulta)
            VSM.append(self.rankingVectorSpaceModel(listaUrls,consulta))
            EP.append(self.enfoquePonderado(listaUrls, consulta, tema))
            CRANK.append(self.calcularCrankOriginal(listaUrls, consulta))

        for unVsm in VSM:
            self.imprimirLista(unVsm[:10],"VSM")

        for unEP in EP:
            self.imprimirLista(unEP[:10],"EP")

        for unCrank in CRANK:
            self.imprimirLista(unCrank[:10],"CRank")

        self.evaluarMetodos(VSM,'vsm')

    def initSVM(self, path):
        """ Iniciar el ranking SVM"""
        listaUrls = self.preprocesamiento.lecturaSVM(path)
        self.iniciarSVM(self.svmNoRelevante, "norelevante", 1, listaUrls)
        self.iniciarSVM(self.svmRelevante, "relevante", 2, listaUrls)
        self.iniciarSVM(self.svmMuyRelevante, "muyrelevante", 4, listaUrls)


    def predecirListaUrls(self, puntos):
        """ Metodo para predicir la clase de cada url
            Entrada: Lista urls
        """
        svm = joblib.load('Model/SVM/filename.pkl')

        X = puntos['xEntrenamiento']
        Y = puntos['yEntrenamiento']

        predicciones = svm.predict(X)

        total = len(Y)
        aciertos = 0
        for prediccion, y in zip(predicciones, Y):
            print prediccion, y
            if prediccion == y:
                aciertos += 1

        porcentajeAcierto = float(aciertos) / float(total)


    def inicializarParametrosIteracion(self):
        """Parametros para el entrenamiento del SVM"""
        parametros = {}

        parametros['inicio'] = 0.001
        parametros['fin'] = 30
        parametros['incremento'] = 0.1

        # incremento gamma
        parametros['incrementoG'] = 1

        parametros['rangoC'] = np.arange(parametros['inicio'], parametros['fin'], parametros['incremento'])
        parametros['rangoGamma'] = np.arange(parametros['inicio'], parametros['fin'], parametros['incrementoG'])

        # parametros['kernels'] = ['rbf', 'linear', 'poly',]
        parametros['kernels'] = ['rbf']

        return parametros

    def inicializarMejorCombinacion(self, parametros, name):

        mejorCombinacion = {}
        mejorCombinacion['precision'] = 0
        mejorCombinacion['C'] = parametros['rangoC'][0]
        mejorCombinacion['gamma'] = parametros['rangoGamma'][0]
        mejorCombinacion['kernel'] = parametros['kernels'][0]
        mejorCombinacion['name'] = name
        return mejorCombinacion



    def entrenarSVM(self, svm, parametros, X, Y, name):
        """
            Metodo para entrenar el SVM
            Parametros de entrada:
                svm: instancia de la clase SVM
                parametros: conjunto de valores de c y gamma
                X: lista de atributos
                Y: lista de clases
                name: nombre de la instancia del svm"""
        mejorCombinacion = self.inicializarMejorCombinacion(parametros, name)
        for kernel in parametros['kernels']:
            for gamma in parametros['rangoGamma']:
                for C in parametros['rangoC']:
                    print C, kernel, gamma
                    svm.ajustarParametros(C, kernel, .8, .2, X, Y, gamma=gamma)
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
        self.mongodb.escribirParametrosSVM(mejorCombinacion).inserted_id


    def predecir(self, svm, X, Y):
        """Metodo para predecir la clase dado una lista de atributos
           Salida: porcentaje de aciertos"""
        predicciones = svm.predecir(X)
        total = len(Y)
        aciertos = 0
        for prediccion, y in zip(predicciones, Y):
            if prediccion == y:
                aciertos += 1
        print float(aciertos) / float(total)


    def iniciarSVM(self, svm, name, limite, listaUrls):

        puntos = svm.obtenerAtributos(limite, listaUrls)
        conjuntos = svm.dividirConjuntoTesting(puntos, .8, .2)

        X = conjuntos['xEntrenamiento']
        Y = conjuntos['yEntrenamiento']

        parametros = self.inicializarParametrosIteracion()
        self.entrenarSVM(svm, parametros, X, Y, name)

        X = conjuntos['xTest']
        Y = conjuntos['yTest']
        self.predecir(svm, X, Y)

        joblib.dump(svm.instanciaSVM, 'Model/SVM/' + name + '.pkl')



