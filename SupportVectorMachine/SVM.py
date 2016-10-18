from Model.mongodb import *
from preprocesamientoController import *
from pattern.vector import Document,Model
from Atributos import *
import re

class SVM:
    mongodb = MongoDb()
    preprocesamiento = preprocesamientoController()

    def __init__(self):
        pass


    def setearAtributos(self,consulta):
        documentos = self.mongodb.getDocumentosConsulta(consulta)
        listaAtributos = []
        for documento in documentos:
            atributo = self.crearAtributosSingulares(documento,consulta)

            atributosConsulta = {}
            atributosConsulta['consulta'] = consulta
            atributosConsulta['atributos'] = atributo.atributos

            self.mongodb.agregarDatosAtributos(documento, atributosConsulta)
            listaAtributos.append(atributo)

        self.crearAtributosGrupales(listaAtributos,consulta)

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

'''
    def crearAtributos(self,documento,consulta):
        html = Document(unDocumento.html)
        titulo = Document(unDocumento.titulo)
        body = Document(unDocumento.body)
        urlValues = Document(unDocumento.urlValues)

        unAtributo = Atributo(documento=unDocumento)
        unAtributo.setQueryTermNumber(unDocumento, unaQuery.words, html.words, titulo.words, body.words,urlValues.words)
        unAtributo.setQueryTermRatio(unDocumento, unaQuery.vector, html.vector, titulo.vector, body.vector,urlValues.vector)
        unAtributo.setQuerySumTermFrequency(unDocumento, unaQuery, html, titulo, body, urlValues)
        unAtributo.setQueryMinTermFrequency(unDocumento, unaQuery, html, titulo, body, urlValues)
        unAtributo.setQueryMaxTermFrequency(unDocumento, unaQuery, html, titulo, body, urlValues)
        unAtributo.setQueryVarianceTermFrequency(unDocumento, unaQuery, html, titulo, body, urlValues)
        unAtributo.setQueryVectorSpaceModel(unDocumento, unaQuery.vector, html.vector, titulo.vector, body.vector,urlValues.vector)

        return unAtributo'''