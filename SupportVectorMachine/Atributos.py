from pattern.vector import distance,COSINE
from Model.mongodb import *
mongodb = MongoDb()

class Atributos:

    html = ""
    titulo = ""
    urlValues = ""
    body = ""
    url = ""
    consulta = ""
    atributos = {}

    def __init__(self,html="",url="",titulo="",urlValues="",body="",consulta=""):
        self.html = html
        self.url = url
        self.titulo = titulo
        self.urlValues = urlValues
        self.body = body
        self.consulta = consulta

    def calcularAtributos(self):
        self.setQueryTermNumber()
        self.setQueryTermRatio()
        self.setQuerySumTermFrequency()
        self.setQueryMinTermFrequency()
        self.setQueryMaxTermFrequency()
        self.setQueryVarianceTermFrequency()
        self.setQueryVectorSpaceModel()

    def setQueryTermNumber(self):
        self.atributos['queryTermNumberDocumento'] = self.contarNumeroAparicion(self.html.vector, self.consulta)
        self.atributos['queryTermNumberUrl'] = self.contarNumeroAparicion(self.url, self.consulta)
        self.atributos['queryTermNumberTitle'] = self.contarNumeroAparicion(self.titulo, self.consulta)
        self.atributos['queryTermNumberUrlValues'] = self.contarNumeroAparicion(self.urlValues, self.consulta)
        self.atributos['queryTermNumberBody'] = self.contarNumeroAparicion(self.body, self.consulta)

    def setQueryTermRatio(self):
        self.atributos['queryTermRatioDocumento'] = self.contarFrecuenciaAparicion(self.html.vector, self.consulta)
        self.atributos['queryTermRatioTitle'] = self.contarFrecuenciaAparicion(self.titulo, self.consulta)
        self.atributos['queryTermRatioUrlValues'] = self.contarFrecuenciaAparicion(self.urlValues, self.consulta)
        self.atributos['queryTermRatioBody'] = self.contarFrecuenciaAparicion(self.body, self.consulta)

    def setIDF(self):
        self.atributos['queryIDFDocumento'] = self.calcularIDF(self.html, self.consulta)
        self.atributos['queryIDFTitle'] = self.calcularIDF(self.titulo, self.consulta)
        self.atributos['queryIDFUrlValues'] = self.calcularIDF(self.urlValues, self.consulta)
        self.atributos['queryIDFBody'] = self.calcularIDF(self.body, self.consulta)

    def setQuerySumTermFrequency(self):
        self.atributos['querySumTermFrequencyDocumento'] = self.calcularSumTermFrequency(self.html, self.consulta)
        self.atributos['querySumTermFrequencyTitle'] = self.calcularSumTermFrequency(self.titulo, self.consulta)
        self.atributos['querySumTermFrequencyUrlValues'] = self.calcularSumTermFrequency(self.urlValues, self.consulta)
        self.atributos['querySumTermFrequencyBody'] = self.calcularSumTermFrequency(self.body, self.consulta)

    def setQueryMinTermFrequency(self):
        self.atributos['queryMinTermFrequencyDocumento'] = self.calcularMinTermFrequency(self.html, self.consulta)
        self.atributos['queryMinTermFrequencyTitle'] = self.calcularMinTermFrequency(self.titulo, self.consulta)
        self.atributos['queryMinTermFrequencyUrlValues'] = self.calcularMinTermFrequency(self.urlValues, self.consulta)
        self.atributos['queryMinTermFrequencyBody'] = self.calcularMinTermFrequency(self.body, self.consulta)

    def setQueryMaxTermFrequency(self):
        self.atributos['queryMaxTermFrequencyDocumento'] = self.calcularMaxTermFrequency(self.html, self.consulta)
        self.atributos['queryMaxTermFrequencyTitle'] = self.calcularMaxTermFrequency(self.titulo, self.consulta)
        self.atributos['queryMaxTermFrequencyUrlValues'] = self.calcularMaxTermFrequency(self.urlValues, self.consulta)
        self.atributos['queryMaxTermFrequencyBody'] = self.calcularMaxTermFrequency(self.body, self.consulta)

    def setQueryVarianceTermFrequency(self):
        self.atributos['queryVarianceTermFrequencyDocumento'] = self.calcularVarianceTermFrequency(self.html, self.consulta)
        self.atributos['queryVarianceTermFrequencyTitle'] = self.calcularVarianceTermFrequency(self.titulo, self.consulta)
        self.atributos['queryVarianceTermFrequencyUrlValues'] = self.calcularVarianceTermFrequency(self.urlValues,self.consulta)
        self.atributos['queryVarianceTermFrequencyBody'] = self.calcularVarianceTermFrequency(self.body, self.consulta)

    def setQueryVectorSpaceModel(self):
        self.atributos['queryVectorSpaceModelDocumento'] = self.calcularVectorSpaceModel(self.html, self.consulta)
        self.atributos['queryVectorSpaceModelTitle'] = self.calcularVectorSpaceModel(self.titulo, self.consulta)
        self.atributos['queryVectorSpaceModelUrlValues'] = self.calcularVectorSpaceModel(self.urlValues, self.consulta)
        self.atributos['queryVectorSpaceModelBody ']= self.calcularVectorSpaceModel(self.body,self.consulta)

    def contarNumeroAparicion(self, string, unaQuery):
        contador = 0
        for unTermino in unaQuery:
            if unTermino in string:
                contador += 1
        return contador

    def contarFrecuenciaAparicion(self,string,unaQuery):
        contador = 0
        for unTermino in unaQuery:
            try:
                contador += string.vector[unTermino]
            except:
                pass
        contador = contador / len(unaQuery)
        return contador

    def calcularIDF(self,string,unaQuery):
        contador = 0
        for unTermino in unaQuery:
            if unTermino in string:
                 contador += string.tfidf(unTermino)
        return contador

    def calcularSumTermFrequency(self,string,unaQuery):
        contador = 0
        for unTermino in unaQuery:
            if unTermino in string:
                 contador += string.tf(unTermino)
        return contador

    def calcularMinTermFrequency(self,string,unaQuery):
        contador = 1.1
        for unTermino in unaQuery:
            if unTermino in string:
                 if contador > string.tf(unTermino):
                    contador = string.tf(unTermino)
        if contador == 1.1:
            contador = 0
        return contador

    def calcularMaxTermFrequency(self,string,unaQuery):
        contador = 0
        for unTermino in unaQuery:
            if unTermino in string:
                 if contador < string.tf(unTermino):
                    contador = string.tf(unTermino)
        return contador

    def calcularVarianceTermFrequency(self,string,unaQuery):
        contador = 0
        for unTermino in unaQuery:
            if unTermino in string:
                contador += string.tf(unTermino)
        promedio = contador / len(unaQuery)
        contador = 0
        for unTermino in unaQuery:
            if unTermino in string:
                contador += (string.tf(unTermino)- promedio)**2
        contador = contador / len(unaQuery)
        return contador

    def calcularVectorSpaceModel(self,string,unaQuery):
        if string:
            return distance(string.vector, unaQuery.vector, method=COSINE)
        else:
            return 0

    def calcularAtributosCorpus(self,modelos, unaConsulta,listaDocumentos):

        for unModelo in modelos:
            self.calcularAtributosCorpusSum(modelos[unModelo], unModelo, unaConsulta,listaDocumentos)
            self.calcularAtributosCorpusMin(modelos[unModelo], unModelo, unaConsulta,listaDocumentos)
            self.calcularAtributosCorpusMax(modelos[unModelo], unModelo, unaConsulta,listaDocumentos)
            self.calcularAtributosCorpusProm(modelos[unModelo], unModelo, unaConsulta,listaDocumentos)




    def calcularAtributosCorpusSum(self,modelo, atributo, consulta,listaDocumentos):
        contador = 0
        for indice, unDocumento in enumerate(modelo):
            for unaConsulta in consulta:
                contador += unDocumento.tfidf(unaConsulta)

            mongodb.setDocumentoAtributo(consulta,listaDocumentos[indice],'querySumTfidf'+self.getNameAtributo(atributo),contador)
            #print 'querySumTfidf'+self.getNameAtributo(atributo) , " - " ,contador

    def calcularAtributosCorpusMax(self, modelo, atributo, consulta, listaDocumentos):
        for indice, unDocumento in enumerate(modelo):
            contador = 0
            for unaConsulta in consulta:
                contadorAux = unDocumento.tfidf(unaConsulta)
                if contador < contadorAux:
                    contador = contadorAux
            mongodb.setDocumentoAtributo(consulta,listaDocumentos[indice],'queryMaxTfidf'+self.getNameAtributo(atributo),contador)
            #print 'queryMaxTfidf'+self.getNameAtributo(atributo) , " - " ,contador

    def calcularAtributosCorpusMin(self, modelo, atributo, consulta, listaDocumentos):
        for indice, unDocumento in enumerate(modelo):
            contador = 100
            for unaConsulta in consulta:
                contadorAux = unDocumento.tfidf(unaConsulta)
                if contador > contadorAux:
                    contador = contadorAux
            mongodb.setDocumentoAtributo(consulta,listaDocumentos[indice],'queryMinTfidf'+self.getNameAtributo(atributo),contador)
            #print 'queryMinTfidf'+self.getNameAtributo(atributo) , " - " ,contador

    def calcularAtributosCorpusProm(self, modelo, atributo, consulta, listaDocumentos):
        for indice, unDocumento in enumerate(modelo):
            contador = 0
            for unaConsulta in consulta:
                contador += unDocumento.tfidf(unaConsulta)
            contador = contador / len(consulta)
            mongodb.setDocumentoAtributo(consulta,listaDocumentos[indice],'queryPromTfidf'+self.getNameAtributo(atributo),contador)
            #print 'queryPromTfidf' + self.getNameAtributo(atributo), " - ", contador

    def getNameAtributo(self,unAtributo):
        if "documento" in unAtributo:
            return "Documento"
        elif "body" in unAtributo:
            return "Body"
        elif "url" in unAtributo:
            return "UrlValues"
        elif "title" in unAtributo:
            return "Title"
