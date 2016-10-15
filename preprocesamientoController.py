from Model.mongodb import *
from pattern.vector import Document, PORTER
from pattern.web import URL, plaintext

class preprocesamientoController:

    listaUrls = []
    mongoDb = MongoDb()

    def __init__(self,nombreArchivo):
            self.leerArchivo(nombreArchivo)



    def leerArchivo(self,nombreArchivo):
        """ retorna una lista de urls limpios leidos de un archivo"""
        archivo = open(nombreArchivo,'rb')
        for unaLinea in archivo.readlines():
            url = self.limpiarUrl(unaLinea.split("\n")[0])

            self.crearDocumento(url)
            self.listaUrls.append(url)


    def limpiarUrl(self,url):
        """ Metodo para limpiar la barra final de la url """
        if url[-1:] == "/":
            return url[:-1]
        return url

    def crearDocumento(self,url):
        contenido = self.descargarContenido(url)
        self.insertarDocumento(url,contenido)


    def descargarContenido(self,url):
        unaUrl = URL(url).download()
        return plaintext(unaUrl)

    def insertarDocumento(self,url,contenido):
        """ Crea registro en mongodb y un archivo Pattern Document"""
        unDocumento = Document(contenido, name=url,stopwords=False, stemming=PORTER)
        result = self.mongoDb.crearDocumento(unDocumento)
        if result:
            unDocumento.save("DocumentoPattern/" + str(result.inserted_id))
        return unDocumento