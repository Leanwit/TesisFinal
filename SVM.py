from Model.mongodb import *
from pattern.vector import Document,Model

class SVM:

    mongodb = MongoDb()

    def __init__(self):
        pass


    def setearAtributos(self,consulta):
        documentos = self.mongodb.getDocumentosConsulta(consulta)
        for documento in documentos:
            self.crearAtributos(documento,consulta)


    def crearAtributos(self,documento,consulta):
        unDocumentoPattern = Document.load("DocumentoPattern/"+str(documento['_id']))
        html = unDocumentoPattern.vector

        titulo = ""
        if "titulo" in documento:
            titulo = documento['titulo']

        body = ""
        if "body" in documento:
            body = documento['body']

        urlValues = ""
        if "urlValues" in documento:
            urlValues = documento['urlValues']



    '''def crearAtributos(self,documento,consulta):
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