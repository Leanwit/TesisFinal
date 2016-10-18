import sys
from pymongo import MongoClient



class MongoDb:
    client = MongoClient()
    db = client.Documento

    def __init__(self):
        reload(sys)
        sys.setdefaultencoding('utf-8')


    def getDocumento(self,url):
        cursor = self.db.documento.find({"url": url})
        for documento in cursor:
            return documento


    def crearDocumento(self,unDocumento):
        cursor = self.db.documento.find({"url": unDocumento.name})
        if not cursor.count():
            result = self.db.documento.insert_one(
                {
                    "id": unDocumento.id,
                    "url": unDocumento.name,
                    "contenido": unDocumento.vector,

                }
            )
            return result
        else:
            for documento in cursor:
                try:
                    archivo = open("DocumentoPattern/"+str(documento['_id']))
                except:
                    self.db.documento.delete_many({"url": unDocumento.name})
                    result = self.db.documento.insert_one(
                        {
                            "id": unDocumento.id,
                            "url": unDocumento.name,
                            "contenido": unDocumento.vector,

                        }
                    )
                    return result

    def setearRelevancia(self,url,relevancia):
        cursor = self.db.documento.find({"url": url})
        if cursor.count():
            for documento in cursor:
                result = self.db.documento.update_one(
                    {"url": documento['url']},
                    {
                        "$set": {
                            "relevancia": relevancia
                        },
                        "$currentDate": {"lastModified": True}
                    }
                )
        else:
            print "No existe url - setear relevancia"

    def getDocumentosConsulta(self,consulta):
        cursor = self.db.documento.find({"relevancia.consulta":consulta})
        return cursor

    def setInformacionDocumento(self,url,titulo,urlValues,body):
        cursor = self.db.documento.find({"url": url})
        if cursor.count():
            for documento in cursor:
                result = self.db.documento.update_one(
                    {"url": documento['url']},
                    {
                        "$set": {
                            "titulo": titulo,
                            "urlValues": urlValues,
                            "body":body
                        },
                        "$currentDate": {"lastModified": True}
                    }
                )
        else:
            print "No existe url - setInformacionDocumento"

    def agregarDatosAtributos(self,documento,atributo):
        cursor = self.db.documento.find({"url": documento['url']})
        if cursor.count():
            for documento in cursor:
                result = self.db.documento.update_one(
                    {"url": documento['url']},
                    {
                        "$set": {
                            "atributos": atributo.atributos
                        },
                        "$currentDate": {"lastModified": True}
                    }
                )
