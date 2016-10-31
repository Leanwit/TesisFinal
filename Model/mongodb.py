import sys
from pymongo import MongoClient
from random import randint


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
                    "rand": randint(1,100000),
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

    def setInformacionDocumento(self,html,url,titulo,urlValues,body):
        cursor = self.db.documento.find({"url": url})
        if cursor.count():
            for documento in cursor:
                result = self.db.documento.update_one(
                    {"url": documento['url']},
                    {
                        "$set": {
                            "html":html,
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
        cursor = self.db.documento.find({"url":atributo['url']})
        for doc in cursor:
            consultasClases = []
            for consultaClase in doc['consultasClase']:
                if consultaClase['consulta'] == consulta:
                    consultaClase['atributos'][variable] = valor
                consultasClases.append(consultaClase)
            self.db.documento.update_one(
                {"url": doc['url']},
                {
                    "$set": {
                        "consultasClase": consultasClases
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

    def getDocumentosConConsulta(self, orden = False):
        if not orden:
            cursor = self.db.documento.find({'consultasClase.clase':{'$exists': True}})
        else:
            cursor = self.db.documento.find({'consultasClase.clase':{'$exists': True}}).sort([("rand", 1)])
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
        listaDocumentos = self.getDocumentosConConsultaRanking()
        for doc in listaDocumentos:
            for consultaClase in doc['consultasClase']:
                if consultaClase['consulta'] == consulta:
                    atributos = {}
                    atributos['doc'] = doc['url']
                    atributos['atributo'] = consultaClase['atributos']
                    listaAtributos.append(atributos)
        return listaAtributos

    def getDocumentoParam(self, param):
        cursor = self.db.documento.find(param)
        for doc in cursor:
            return doc

    def eliminarDocumentosSinContenido(self):
        self.db.documento.delete_many({"html":{"$exists":False}})

    def getDocumentosConConsultaRanking(self):
        cursor = self.db.documento.find({'consultasClase': {'$exists': True}})
        return cursor

    def crearDocumentoRelevancia(self,url,relevancia):
        self.db.relevancia.insert_one(
            {
                "url":url,
                "relevancia":relevancia,
            }
        )

    def getDocumentosRelevancia(self, url):
        cursor = self.db.relevancia.find({"url":url})
        return cursor[0]

    def crearRelaciones(self, source, target):
        documentos = self.getDocumento(target)
        if documentos:
            if "inlinks" in documentos:
                if not source in documentos['inlinks']:
                    self.insertarRelacion(source,target)
            else:
                self.insertarRelacion(source,target)

    def insertarRelacion(self,source,target):
        self.db.documento.update_one(
            {"url": target},
            {
                "$push": {
                    "inlinks": source
                },
                "$currentDate": {"lastModified": True}
            }
        )

    def setearRelevanciaEnfoquePonderado(self, url, puntaje):
        self.db.documento.update_one(
            {"url": url},
            {
                "$set": {
                    "relevanciaEnfoquePonderado": puntaje
                },
                "$currentDate": {"lastModified": True}
            }
        )

    def setearRelevanciaCrank(self, url, puntaje):
        self.db.documento.update_one(
            {"url": url},
            {
                "$set": {
                    "relevanciaCrank": puntaje
                },
                "$currentDate": {"lastModified": True}
            }
        )

    def getDocumentos(self):
        return self.db.documento.find()

    def setearRelevanciaContribucion(self, url, puntaje):
        self.db.documento.update_one(
            {"url": url},
            {
                "$set": {
                    "relevanciaContribucion": puntaje
                },
                "$currentDate": {"lastModified": True}
            }
        )

    def escribirParametrosSVM(self, mejorCombinacion):
        return self.db.SVM.insert_one(
            {
                "instanciaSVM":mejorCombinacion
            }
        )

    def eliminarBdRelevancia(self):
        self.db.relevancia.delete_many({})
        print "Eliminado Relevancia"
