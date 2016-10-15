import sys
from pymongo import MongoClient
from pattern.vector import Document
from pattern.web import URL, plaintext


class MongoDb:
    client = MongoClient()
    db = client.Documento

    def __init__(self):
        reload(sys)
        sys.setdefaultencoding('utf-8')



    def crearDocumento(self,url):
        cursor = self.db.documento.find({"url": url})
        if not cursor.count():

            contenido = self.descargarContenido(url)
            self.insertarDocumento(url,contenido)
        else:
            for documento in cursor:
                try:
                    archivo = open("DocumentoPattern/"+str(documento['_id']))
                except:
                    self.db.documento.delete_many({"url": url})
                    contenido = self.descargarContenido(url)
                    self.insertarDocumento(url, contenido)
                break

    def descargarContenido(self,url):
        unaUrl = URL(url).download()
        return plaintext(unaUrl)

    def insertarDocumento(self,url,contenido):
        """ Crea registro en mongodb y un archivo Pattern Document"""
        unDocumento = Document(contenido, name=url)
        result = self.db.documento.insert_one(
            {
                "id": unDocumento.id,
                "url": url,
                "contenido": unDocumento.vector,

            }
        )
        unDocumento.save("DocumentoPattern/" + str(result.inserted_id))