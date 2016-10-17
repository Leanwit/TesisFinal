from Model.mongodb import *
from pattern.vector import Document, PORTER
from pattern.web import URL, plaintext, extension
import urllib2
import os
import commands


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
            self.insertarDocumento(url,contenido)


    def descargarContenido(self,url):
        try:
            unaUrl = URL(url)
            if "pdf" in extension(unaUrl.page):
                return self.descargarPDF(unaUrl)
            else:
                return plaintext(unaUrl.download())
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
        unDocumento = Document(contenido, name=url,stopwords=False, stemming=PORTER)
        result = self.mongoDb.crearDocumento(unDocumento)
        if result:
            unDocumento.save("DocumentoPattern/" + str(result.inserted_id))
        return unDocumento

    def lecturaSVM(self,path,consulta):
        archivo = open(path, 'r').read()
        for unaLinea in archivo.split("\n"):
            if unaLinea:

                campos = unaLinea.split(" , ")
                url = self.limpiarUrl(campos[0])
                clase = campos[1]

                self.crearDocumento(url)

                relevancia = {}
                relevancia['consulta'] = consulta
                relevancia['clase'] = clase



