from preprocesamientoController import *
from Model.mongodb import *

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

    def calcularRelevancia(self, consulta, tema = "Tea"):
        diccionario = self.getDiccionarioDominio(tema)
        consultaPattern = self.preprocesamiento.crearDocumentoPattern(consulta,"Consulta")
        listaDocumentos = self.mongodb.getDocumentos()
        for unDocumento in listaDocumentos:
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

    def calcularRelevanciaCrank(self,consulta):
        consultaDocumento = self.preprocesamiento.crearDocumentoPattern(consulta,"consulta")
        listaDocumentos = self.mongodb.getDocumentos()
        listaDocumentosPattern = []
        for doc in listaDocumentos:
            documentoPattern = self.preprocesamiento.getDocumentoPattern(doc['_id'])
            listaDocumentosPattern.append(documentoPattern)
        modelo = self.preprocesamiento.crearModelo(listaDocumentosPattern)

        listaDocumentos = self.mongodb.getDocumentos()
        for doc in listaDocumentos:
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