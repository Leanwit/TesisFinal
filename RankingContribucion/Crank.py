from preprocesamientoController import *
from Model.mongodb import *
import copy
class RC:
    preprocesamiento = preprocesamientoController()
    mongodb = MongoDb()
    def __init__(self):
        pass

    def lecturaArchivoCrank(self,path):
        file = open(path, 'rb')
        listaUrls = []
        for unaLinea in file.readlines():
            if unaLinea:
                unaLinea = unaLinea.split("\n")[0]
                if unaLinea:
                    lineaLimpia = self.limpiarLineaCrank(unaLinea)
                    if lineaLimpia['source']:
                        listaUrls.append(self.limpiarLineaCrank(unaLinea))
        return listaUrls

    def limpiarLineaCrank(self,linea):
        '''Metodo que limpia las lineas del archivo generado por el crawler'''
        unaLinea = linea.split("INFO:root:;")[1].split(";From;")
        if len(unaLinea) == 2:
            json = {}
            json['source'] = unaLinea[1]
            json['target'] = unaLinea[0]
            return json

    def calcularRelevancia(self, consulta, tema="Tea", listaUrls=[], parametrosCrank=[]):
        '''Metodo para calcular la relevancia'''
        diccionario = self.getDiccionarioDominio(tema)
        consultaPattern = self.preprocesamiento.crearDocumentoPattern(consulta, "Consulta")

        listaDocumentos = self.getAllInlinks(listaUrls)
        while listaDocumentos != listaUrls:
            listaUrls = copy.copy(listaDocumentos)
            listaDocumentos = self.getAllInlinks(listaUrls)

        listaModelo = []
        for unDoc in listaDocumentos:
            docBD = self.mongodb.getDocumento(unDoc)
            if docBD:
                unDocumento = self.preprocesamiento.getDocumentoPattern(docBD['_id'])
                listaModelo.append(unDocumento)

        unModelo = Model(listaModelo, weight=TFIDF)

        for unDocumento in unModelo:
            puntajeFinal = self.calcularEnfoquePonderado(unDocumento, consultaPattern, diccionario,parametrosCrank)
            self.mongodb.setearRelevanciaEnfoquePonderado(unDocumento.name, puntajeFinal)


    def getDiccionarioDominio(self, diccionario):
        '''Metodo para obotener el diccionario de dominio segun el tema y transformarlo en un documento pattern'''
        archivo = open("RankingContribucion/dd"+diccionario+".txt","r")
        return self.preprocesamiento.crearDocumentoPattern(archivo.read(),"diccionarioDominio")

    def calcularEnfoquePonderado(self,documento,consulta,diccionario, parametrosCrank = []):
        '''Calculo del enfoque ponderado'''
        aciertoClave = 0
        aciertoPositivo = 0
        aciertoNegativo = 0

        for doc in documento.vector:
            frecuencia = documento.vector[doc]
            if doc in consulta.words and doc in diccionario.words:
                aciertoClave += frecuencia
            else:
                if doc in diccionario.words:
                    aciertoPositivo += frecuencia
                else:
                    aciertoNegativo += frecuencia


        if aciertoClave + aciertoPositivo + aciertoNegativo:
            puntajeFinal = float(aciertoClave * float(parametrosCrank['AC']) + aciertoPositivo * float(parametrosCrank['AP']) + aciertoNegativo * float(parametrosCrank['AN'])) / float(aciertoClave + aciertoPositivo + aciertoNegativo)
        else:
            puntajeFinal = 0
        return puntajeFinal

    def calcularRelevanciaCrank(self,consulta,listaUrls, tema = ""):
        '''Metodo para calcular la relevancia del Crank'''
        consultaDocumento = self.preprocesamiento.crearDocumentoPattern(consulta,"consulta")

        listaDocumentos = self.getAllInlinks(listaUrls)
        while listaDocumentos != listaUrls:
            listaUrls = copy.copy(listaDocumentos)
            listaDocumentos = self.getAllInlinks(listaDocumentos)

        listaDocumentosPattern = []
        for doc in listaDocumentos:
            doc = self.mongodb.getDocumento(doc)
            if doc:
                documentoPattern = self.preprocesamiento.getDocumentoPattern(doc['_id'])
                listaDocumentosPattern.append(documentoPattern)

        modelo = self.preprocesamiento.crearModelo(listaDocumentosPattern)

        for doc in modelo:
            #doc = self.preprocesamiento.getDocumentoPattern(doc['_id'])
            scoreRelevance = 0
            var_coord = self.coord(doc, consultaDocumento)
            for unTermino in consultaDocumento:
                scoreRelevance += doc.tfidf(unTermino) * self.norm(doc, unTermino) * var_coord

            scoreDicc = 0
            if tema != "":
                diccionario = self.getDiccionarioDominio(tema)
                var_coord = self.coord(doc,diccionario)
                for unTermino in diccionario:
                    scoreDicc += doc.tfidf(unTermino) * self.norm(doc,unTermino) * var_coord

            scoreRelevance = scoreRelevance + (scoreDicc * 0.5)
            self.mongodb.setearRelevanciaEnfoquePonderado(doc.name, scoreRelevance)

    def coord(self, documento, consulta):
        '''Puntaje coord utilizando en el crank para el calculo de relevancia'''
        contador = 0
        for word in consulta:
            if word in documento.words:
                contador += 1
        return (float(contador) / float(len(consulta)))

    def norm(self, documento, un_termino):
        '''Puntaje norm utilizando en el crank para el calculo de relevancia'''
        valor = 0
        if un_termino in documento.words:
            valor = documento.tf(un_termino)
        return valor

    def calcularScoreContribucion(self,listaUrls, atributo = "relevanciaEnfoquePonderado",parametrosCrank = []):
        '''Calculo del puntaje de contribucion'''
        listaDocumentos = self.getAllInlinks(listaUrls)
        while listaDocumentos != listaUrls:
            listaUrls = copy.copy(listaDocumentos)
            listaDocumentos = self.getAllInlinks(listaUrls)

        analizados = []
        for unDocumento in listaDocumentos:
            unDocumento = self.mongodb.getDocumento(unDocumento)
            if unDocumento:
                unDocumento['scoreContribucion'] = self.calcularScoreContribucionRecursividad(unDocumento,0,analizados,atributo,nivelAEvaluar = int(parametrosCrank['niveles']))
                self.mongodb.setearRelevanciaContribucion(unDocumento['url'],unDocumento['scoreContribucion'])

    def calcularScoreContribucionRecursividad(self, doc, nivel, analizados, atributo = "relevanciaEnfoquePonderado",nivelAEvaluar = 3):
        '''Metodo recursivo para ir calculando los puntajes del grafo hasta 3 niveles'''
        score = 0
        if nivel < nivelAEvaluar:
            if not doc in analizados:
                analizados.append(doc)
                if 'inlinks' in doc:
                    for inlink in doc['inlinks']:
                        inlink = self.mongodb.getDocumento(inlink)
                        score += self.calcularScoreContribucionRecursividad(inlink, nivel + 1, analizados,atributo)
                        if "inlinks" in inlink:
                            score_inlink = 0
                            for aux_inlink in inlink['inlinks']:
                                aux_inlink = self.mongodb.getDocumento(aux_inlink)
                                score_inlink += aux_inlink[atributo]
                            if inlink[atributo] != 0:
                                score += (doc[atributo] / (inlink[atributo] + score_inlink)) * inlink[atributo]

        return score

    def calcularPuntajeFinal(self,listaUrls,atributo = "relevanciaEnfoquePonderado",parametro=""):
        if parametro == "":
            parametro = 0.20

        listaUrlsPonderados = []
        for unaUrl in listaUrls:
            documento = self.mongodb.getDocumento(unaUrl)
            if documento:
                scoreRelevance = documento[atributo]
                scoreContribucion = documento['relevanciaContribucion']
                scoreFinal = ((1-float(parametro['factorContribucion'])) * scoreRelevance) + (float(parametro['factorContribucion']) * scoreContribucion)

                urlPonderado = {}
                urlPonderado['url'] = unaUrl
                urlPonderado['score'] = scoreFinal
                listaUrlsPonderados.append(urlPonderado)

        listaNueva = sorted(listaUrlsPonderados, key=lambda k: k['score'], reverse=True)
        return listaNueva

    def getAllInlinks(self, listaUrls):
        '''metodo para obtener todos los enlaces entrantes de un documento web'''
        listaCalculo = []
        for url in listaUrls:
            if url not in listaCalculo:
                listaCalculo.append(url)
            documento = self.mongodb.getDocumento(url)
            if documento:
                if "inlinks" in documento:
                    for inlink in documento['inlinks']:
                        if not inlink in listaCalculo:
                            listaCalculo.append(inlink)
        return listaCalculo




