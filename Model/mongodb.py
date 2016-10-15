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


