from Model.mongodb import *
from pattern.vector import Document, PORTER, TFIDF, Model, distance, COSINE
from pattern.web import URL, plaintext, extension,Element
import urllib2
import os
import commands
from pyPdf import PdfFileWriter, PdfFileReader


class preprocesamientoController:

    listaUrls = []
    mongoDb = MongoDb()

    def __init__(self,nombreArchivo =""):
            if nombreArchivo:
                self.leerArchivo(nombreArchivo)
                self.eliminarDuplicados()

    def leerArchivo(self,nombreArchivo):
        """ retorna una lista de urls limpios leidos de un archivo"""
        archivo = open(nombreArchivo,'rb')
        for unaLinea in archivo.readlines():
            url = self.limpiarUrl(unaLinea.split("\n")[0])
            self.crearDocumento(url)
            self.listaUrls.append(url)




    def eliminarDuplicados(self):
        """ Eliminacion de urls duplicados """
        listaUrlsAux = []
        for url in self.listaUrls:
            if url not in listaUrlsAux:
                listaUrlsAux.append(url)
        self.listaUrls = listaUrlsAux

    def limpiarUrl(self,url):
        """ Metodo para limpiar la barra final de la url """
        if url[-1:] == "/":
            return url[:-1]
        return url

    def crearDocumento(self,url):
        contenido = self.descargarContenido(url)
        if contenido:
            documento = self.insertarDocumento(url,contenido)
            self.agregarInformacionDocumento(url, contenido)
            print "Creado " , url
            return documento

    def crearDocumentoSVM(self,url):
        ''' Se obtiene valores del html para los atributos del svm. La descarga entra en cache'''

        contenido = self.descargarContenido(url)
        if contenido:
            documento = self.insertarDocumento(url, contenido)
            self.agregarInformacionDocumento(url, contenido)
            return documento

    def agregarInformacionDocumento(self,url,contenido):
        try:
            unaUrl = URL(url)
            if not 'pdf' in extension(unaUrl.page):
                html = contenido
                unElemento = Element(self.descargarContenidoHtml(url))
                body = self.getBody(unElemento)
                urlValues = self.getUrlValues(unElemento)
                titulo = self.getTitulo(unElemento)

                html = self.verificarContenidoVacio(html)
                body = self.verificarContenidoVacio(body)
                urlValues = self.verificarContenidoVacio(urlValues)
                titulo = self.verificarContenidoVacio(titulo)
                self.mongoDb.setInformacionDocumento(html,url,titulo,urlValues,body)
            else:
                html = self.verificarContenidoVacio(contenido)
                body = ""
                urlValues = ""
                titulo = ""
                self.mongoDb.setInformacionDocumento(html,url,titulo,urlValues,body)
        except Exception as e:
            print str(e)

    def getBody(self,unElemento):
        body = ""
        for unBody in unElemento.by_tag('body'):
            body += unBody.source
        return body

    def getUrlValues(self,unElemento):
        urlValues = ""
        for unValueUrl in unElemento('a:first-child'):
            urlValues += plaintext(unValueUrl.content) + " - "
        return urlValues

    def getTitulo(self,unElemento):
        titulo = ""
        if unElemento.by_tag('title'):
            titulo = unElemento.by_tag('title')[0].content
        return titulo

    def descargarContenido(self,url):
        try:
            unaUrl = URL(url)
            if "pdf" in extension(unaUrl.page):
                return self.descargarPDF(unaUrl)
            else:
                return plaintext(unaUrl.download())
        except Exception as e:
            try:
                return plaintext(self.urlLibDescarga(url))
            except Exception as e:
                print "except " + str(e)
                print url

    def descargarContenidoHtml(self,url):
        try:
            unaUrl = URL(url)
            if "pdf" in extension(unaUrl.page):
                return self.descargarPDF(unaUrl)
            else:
                return unaUrl.download()
        except Exception as e:
            try:
                return self.urlLibDescarga(url)
            except Exception as e:
                print "except " + str(e)
                print url

    def descargarPDF(self,url):
        document = open(os.path.dirname(os.path.abspath(__file__)) + '/temp.pdf', 'w')
        document.close()
        download = url.download()
        document = open(os.path.dirname(os.path.abspath(__file__)) + '/temp.pdf', 'a')
        document.write(download)
        document.close()
        txtContent = commands.getoutput('pdf2txt.py ' + os.path.dirname(os.path.abspath(__file__)) + '/temp.pdf')
        os.remove(os.path.dirname(os.path.abspath(__file__)) + '/temp.pdf')
        return txtContent

    def urlLibDescarga(self,url):
        response = urllib2.urlopen(url)
        html = response.read()
        return html

    def insertarDocumento(self,url,contenido):
        """ Crea registro en mongodb y un archivo Pattern Document"""
        unDocumento = Document(contenido, name=url,stopwords=True, stemming=PORTER,weigth=TFIDF)
        result = self.mongoDb.crearDocumento(unDocumento)
        if result:
            unDocumento.save("DocumentoPattern/" + str(result.inserted_id))
        return unDocumento

    def lecturaSVM(self,path):
        listaUrls = []
        archivo = open(path, 'r').read()
        for unaLinea in archivo.split("\n"):
            if unaLinea:
                campos = unaLinea.split(" , ")
                consulta = campos[0]
                url = self.limpiarUrl(campos[1])
                if len(campos) > 2:
                    clase = campos[2]
                    if clase and url:
                        documento = self.mongoDb.getDocumento(url)
                        if not documento:
                            documentoPattern = self.crearDocumentoSVM(url)
                        else:
                            documentoPattern = self.getDocumentoPattern(documento['_id'])
                        if documentoPattern and consulta:
                            consultaClase = {}
                            consultaClase['consulta'] = consulta
                            consultaClase['clase'] = clase
                            if documentoPattern:
                                self.mongoDb.setearRelevancia(documentoPattern.name,consultaClase)
                                listaUrls.append(url)
        self.mongoDb.eliminarDocumentosSinContenido()
        return listaUrls

    def lecturaSVMRanking(self,listaUrls,consulta):
        for url in listaUrls:
            doc = self.mongoDb.getDocumentoParam({"url": url, "consultasClases.consulta": consulta})
            if not doc:
                documentoPattern = self.crearDocumentoSVM(url)
                consultaClase = {}
                consultaClase['consulta'] = consulta
                if documentoPattern:
                    self.mongoDb.setearRelevancia(documentoPattern.name, consultaClase)
        self.mongoDb.eliminarDocumentosSinContenido()

    def crearDocumentoPattern(self,contenido,name = ""):
        return Document(contenido,name=name,stemmer=PORTER,stopwords=True,weigth=TFIDF)

    def crearModelo(self,listaDocumentos):
        return Model(listaDocumentos, weight=TFIDF)

    def verificarContenidoVacio(self, param):
        if not param:
            param = ""
        return param

    def leerArchivoUrls(self, path):
        listaUrls = []
        archivo = open(path, 'r').read()
        for unaLinea in archivo.split("\n"):
            if unaLinea:
                unaUrl = {}
                campos = unaLinea.split(" , ")
                unaUrl['consulta'] = campos[0]
                unaUrl['url'] = self.limpiarUrl(campos[1])
                if len(campos) > 2:
                    unaUrl['relevancia'] = campos[2]
                listaUrls.append(unaUrl)
        return listaUrls

    def isPDF(self, param):
        url = URL(param)
        if "pdf" in extension(url.page):
            return 1
        else:
            return 0

    def getDocumentoPattern(self, id):
        return Document.load("DocumentoPattern/" + str(id))

    def obtenerVectorSpaceModel(self, url,consulta):
        documento = self.mongoDb.getDocumento(url)
        if documento:
            for consultasClase in documento['consultasClase']:
                if consultasClase['consulta'] == consulta:
                    return consultasClase['atributos']['queryVectorSpaceModelDocumento']
        return 1

    def leerArchivoUrl(self,path):
        listaUrls = []
        archivo = open(path, 'r').read()
        for unaLinea in archivo.split("\n"):
            if unaLinea:
                listaUrls.append(self.limpiarUrl(unaLinea))
        return listaUrls

    def calcularVectorSpaceModel(self, doc1, doc2):
        return distance(doc1.vector,doc2.vector,method=COSINE)

