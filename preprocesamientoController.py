from Model.mongodb import *
from pattern.vector import Document, PORTER, TFIDF, Model, distance, COSINE
from pattern.web import URL, plaintext, extension,Element
import urllib2
import os
import commands
from pyPdf import PdfFileWriter, PdfFileReader

from pattern.en import Sentence,parse
class preprocesamientoController:

    listaUrls = []


    def __init__(self,nombreArchivo =""):
            self.mongodb = MongoDb()
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
        """Metodo para obtener diferentes partes del documento"""
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

                self.mongodb.setInformacionDocumento(html,url,titulo,urlValues,body)
            else:
                html = self.verificarContenidoVacio(contenido)
                body = ""
                urlValues = ""
                titulo = ""
                self.mongodb.setInformacionDocumento(html,url,titulo,urlValues,body)
        except Exception as e:
            print str(e)

    def getBody(self,unElemento):
        """ Metodo para obtener el cuerpo del documento web. """
        body = ""
        for unBody in unElemento.by_tag('body'):
            body += unBody.source
        return body

    def getUrlValues(self,unElemento):
        """Metodo para obtener todas las urls dentro del documento web"""
        urlValues = ""
        for unValueUrl in unElemento('a:first-child'):
            urlValues += plaintext(unValueUrl.content) + " - "
        return urlValues

    def getTitulo(self,unElemento):
        """Metodo para obtener el titulo del documento web"""
        titulo = ""
        if unElemento.by_tag('title'):
            titulo = unElemento.by_tag('title')[0].content
        return titulo

    def descargarContenido(self,url):
        """Metodo para descargar el contenido de los documentos webs siendo url o pdf"""
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
        """Metodo para descargar contenido de un pdf.
        Se descarga el archivo, se utilza la libreria pdf2txt para transformar el pdf en texto plano"""
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
        '''Metodo para descargar archivo mediante urllib2'''
        response = urllib2.urlopen(url)
        html = response.read()
        return html

    def insertarDocumento(self,url,contenido):
        """ Crea registro en mongodb y un archivo Pattern Document"""
        unDocumento = Document(contenido, name=url,stopwords=True, stemming=PORTER,weigth=TFIDF)
        result = self.mongodb.crearDocumento(unDocumento)
        if result:
            unDocumento.save("DocumentoPattern/" + str(result.inserted_id))
        return unDocumento

    def lecturaSVM(self,path):
        '''Lectura del archivo SVM para el entrenamiento'''
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
                        documento = self.mongodb.getDocumento(url)
                        if not documento:
                            documentoPattern = self.crearDocumentoSVM(url)
                        else:
                            documentoPattern = self.getDocumentoPattern(documento['_id'])
                        if documentoPattern and consulta:
                            consultaClase = {}
                            consultaClase['consulta'] = consulta
                            consultaClase['clase'] = clase
                            if documentoPattern:
                                self.mongodb.setearRelevancia(documentoPattern.name,consultaClase)
                                listaUrls.append([url,consulta])
        self.mongodb.eliminarDocumentosSinContenido()
        return listaUrls

    def lecturaSVMRanking(self,listaUrls,consulta):
        bandera = True
        for url in listaUrls:
            doc = self.mongodb.getDocumento(url)
            if doc:
                if "consultasClase" in doc:
                    for unaConsulta in doc['consultasClase']:
                        if unaConsulta['consulta'] == consulta:
                            bandera = False
                if bandera:
                    documentoPattern = self.getDocumentoPattern(doc['_id'])
                    consultaClase = {}
                    consultaClase['consulta'] = consulta.name
                    self.mongodb.setearRelevancia(documentoPattern.name, consultaClase)

        self.mongodb.eliminarDocumentosSinContenido()

    def crearDocumentoPattern(self,contenido,name = ""):
        '''Creacion de documentos eliminando stopwords, aplicando stemming y peso de frecuencias TFIDF'''
        return Document(contenido,name=name,stemmer=PORTER,stopwords=True,weigth=TFIDF)

    def crearModelo(self,listaDocumentos):
        '''Crear modelo de listas de documentos utilizando calculo de frencuencias TFIDF'''
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



    def leerArchivoUrl(self,path):
        listaUrls = []
        archivo = open(path, 'r').read()
        for unaLinea in archivo.split("\n"):
            if unaLinea:
                listaUrls.append(self.limpiarUrl(unaLinea))
        return listaUrls



    def crearListaConRelevancia(self,path):
        self.mongodb.eliminarBdRelevancia()
        archivo = open(path,"r")
        for unaLinea in archivo.readlines():
            if unaLinea:
                campos = unaLinea.split("	,	")
                url = self.limpiarUrl(campos[0])
                relevancia = campos[1].split("\n")[0]

                self.mongodb.crearDocumentoRelevancia(url,relevancia)

    def limpiarListaUrls(self, listaUrls, urls):
        """limpiar lista de urls que no lograron descargarse"""
        nuevaLista = []
        for url in listaUrls:
            if url in urls:
                nuevaLista.append(url)
        return nuevaLista