from Model.mongodb import *


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
            self.mongoDb.crearDocumento(url)
            self.listaUrls.append(url)


    def limpiarUrl(self,url):
        """ Metodo para limpiar la barra final de la url """
        if url[-1:] == "/":
            return url[:-1]
        return url