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
                            "consultasClase":[]

                        }
                    )
                    return result

    def setearRelevancia(self,url,consultaClase):
        if not self.isExisteRelevancia(url,consultaClase):
            self.crearRelevancia(url,consultaClase)



    def isExisteRelevancia(self,url,consultaClase):
        cursor = self.db.documento.find({"url":url,"consultasClase.consulta":consultaClase['consulta']})
        if cursor.count():
            return True
        else:
            return False

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

    def agregarDatosAtributos(self,documento,consulta,atributo):
        cursor = self.db.documento.find({"url": documento['url']})
        if cursor.count():
            for doc in cursor:
                ''' preparacion de la variable para actualizar '''
                consultasClases = []
                for consultaClase in doc['consultasClase']:
                    if consultaClase['consulta'] == consulta:
                        consultaClase['atributos'] = atributo.atributos
                    consultasClases.append(consultaClase)

                '''actualizacion'''
                self.db.documento.update_one(
                    {"url": documento['url']},
                    {
                        "$set": {
                            "consultasClase": consultasClases
                        },
                        "$currentDate": {"lastModified": True}
                    }
                )



    def setDocumentoAtributo(self,consulta,atributo,variable,valor):
        result = self.db.documento.update_one(
            {"url": atributo['url'],"atributosConsulta.consulta":consulta.name},
            {
                "$set": {
                    "atributosConsulta.atributos."+variable: valor
                },
                "$currentDate": {"lastModified": True}
            }
        )

    def agregarRelevancia(self, url, consultaClase):
            self.db.documento.update_one(
                {"url": url},
                {
                    "$push": {
                        "consultasClase": consultaClase
                    },
                    "$currentDate": {"lastModified": True}
                }
            )

    def crearRelevancia(self, url, consultaClase):
        self.db.documento.update_one(
            {"url": url},
            {
                "$push": {
                    "consultasClase": consultaClase
                },
                "$currentDate": {"lastModified": True}
            }
        )

    def getDocumentosConConsulta(self):
        cursor = self.db.documento.find({'consultasClase':{'$exists': True}})
        return cursor

    def obtenerTodasLasConsultas(self):
        documentos = self.getDocumentosConConsulta()
        listaConsultas = []
        for doc in documentos:
            for consultaClase in doc['consultasClase']:
                consulta = consultaClase['consulta']
                if not consulta in listaConsultas:
                    listaConsultas.append(consulta)
        return listaConsultas

    def getAtributosPorConsulta(self, consulta):
        listaAtributos = []
        listaDocumentos = self.getDocumentosConConsulta()
        for doc in listaDocumentos:
            for consultaClase in doc['consultasClase']:
                if consultaClase['consulta'] == consulta:
                    listaAtributos.append(consultaClase['atributos'])
        return listaAtributos
