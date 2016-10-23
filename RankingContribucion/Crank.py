from preprocesamientoController import *
from Model.mongodb import *
import copy
class Crank:
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
        unaLinea = linea.split("INFO:root:;")[1].split(";From;")
        if len(unaLinea) == 2:
            json = {}
            json['source'] = unaLinea[1]
            json['target'] = unaLinea[0]
            return json

    def calcularRelevancia(self, consulta, tema = "Tea",listaUrls = []):
        diccionario = self.getDiccionarioDominio(tema)
        consultaPattern = self.preprocesamiento.crearDocumentoPattern(consulta,"Consulta")

        listaDocumentos = self.getAllInlinks(listaUrls)
        while listaDocumentos != listaUrls:
            listaUrls = copy.copy(listaDocumentos)
            listaDocumentos = self.getAllInlinks(listaUrls)

        for unDocumento in listaDocumentos:
            unDocumento = self.mongodb.getDocumento(unDocumento)
            if unDocumento:
                documentoPattern = self.preprocesamiento.getDocumentoPattern(unDocumento['_id'])
                puntajeFinal = self.calcularEnfoquePonderado(documentoPattern,consultaPattern,diccionario)
                self.mongodb.setearRelevanciaEnfoquePonderado(unDocumento['url'],puntajeFinal)


    def getDiccionarioDominio(self, diccionario):
        archivo = open("RankingContribucion/dd"+diccionario+".txt","r")
        return self.preprocesamiento.crearDocumentoPattern(archivo.read(),"diccionarioDominio")

    def calcularEnfoquePonderado(self,documento,consulta,diccionario):
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
            puntajeFinal = float(aciertoClave + aciertoPositivo * 0.75 + aciertoNegativo * 0.50) / float(
                aciertoClave + aciertoPositivo + aciertoNegativo)
        else:
            puntajeFinal = 0
        return puntajeFinal

    def calcularRelevanciaCrank(self,consulta,listaUrls):
        consultaDocumento = self.preprocesamiento.crearDocumentoPattern(consulta,"consulta")

        listaDocumentos = self.getAllInlinks(listaUrls)
        while listaDocumentos != listaUrls:
            listaUrls = copy.copy(listaDocumentos)
            listaDocumentos = self.getAllInlinks(listaUrls)

        listaDocumentosPattern = []
        for doc in listaDocumentos:
            doc = self.mongodb.getDocumento(doc)
            if doc:
                documentoPattern = self.preprocesamiento.getDocumentoPattern(doc['_id'])
                listaDocumentosPattern.append(documentoPattern)
        modelo = self.preprocesamiento.crearModelo(listaDocumentosPattern)

        for doc in listaDocumentos:
            doc = self.mongodb.getDocumento(doc)
            if doc:
                doc = self.preprocesamiento.getDocumentoPattern(doc['_id'])
                scoreRelevance = 0
                var_coord = self.coord(doc, consultaDocumento)
                for unTermino in consultaDocumento:
                    scoreRelevance += doc.tfidf(unTermino) * self.norm(doc, unTermino) * var_coord
                self.mongodb.setearRelevanciaCrank(doc.name,scoreRelevance)

    def coord(self, documento, consulta):
        contador = 0
        for word in consulta:
            if word in documento.words:
                contador += 1
        return (float(contador) / float(len(consulta)))

    def norm(self, documento, un_termino):
        valor = 0
        if un_termino in documento.words:
            valor = documento.tf(un_termino)
        return valor

    def calcularScoreContribucion(self,listaUrls):
        listaDocumentos = self.getAllInlinks(listaUrls)
        while listaDocumentos != listaUrls:
            listaUrls = copy.copy(listaDocumentos)
            listaDocumentos = self.getAllInlinks(listaUrls)

        analizados = []
        for unDocumento in listaDocumentos:
            unDocumento = self.mongodb.getDocumento(unDocumento)
            if unDocumento:
                unDocumento['scoreContribucion'] = self.calcularScoreContribucionRecursividad(unDocumento,0,analizados)
                self.mongodb.setearRelevanciaContribucion(unDocumento['url'],unDocumento['scoreContribucion'])

    def calcularScoreContribucionRecursividad(self, doc, nivel, analizados, atributo = "relevanciaEnfoquePonderado"):
        score = 0
        if nivel < 4:
            if not doc in analizados:
                analizados.append(doc)
                if 'inlinks' in doc:
                    for inlink in doc['inlinks']:
                        inlink = self.mongodb.getDocumento(inlink)
                        score += self.calcularScoreContribucionRecursividad(inlink, nivel + 1, analizados)
                        if "inlinks" in inlink:
                            score_inlink = 0
                            for aux_inlink in inlink['inlinks']:
                                aux_inlink = self.mongodb.getDocumento(aux_inlink)
                                score_inlink += aux_inlink[atributo]
                            if inlink[atributo] != 0:
                                score += (doc[atributo] / (inlink[atributo] + score_inlink)) * inlink[atributo]

        return score

    def calcularPuntajeFinal(self,listaUrls,consulta,atributo = "relevanciaEnfoquePonderado"):
        listaUrlsPonderados = []
        for unaUrl in listaUrls:
            documento = self.mongodb.getDocumento(unaUrl)
            if documento:
                scoreRelevance = documento[atributo]
                scoreContribucion = documento['relevanciaContribucion']
                scoreFinal = 0.80 * scoreRelevance + 0.20 * scoreContribucion

                urlPonderado = {}
                urlPonderado['url'] = unaUrl
                urlPonderado['score'] = scoreFinal
                listaUrlsPonderados.append(urlPonderado)

        listaNueva = sorted(listaUrlsPonderados, key=lambda k: k['score'], reverse=True)
        return listaNueva

    def getAllInlinks(self, listaUrls):
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




