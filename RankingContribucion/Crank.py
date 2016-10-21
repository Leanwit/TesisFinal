class Crank:

    def __init__(self):
        pass

    def lecturaArchivoCrank(self,path):
        file = open(path, 'rb')
        listaUrls = []
        for unaLinea in file.readlines():
            if unaLinea:
                unaLinea = unaLinea.split("\n")[0]
                if unaLinea:
                    lineaLimpia = self.limpiarLineaCrank(unaLinea)
                    if lineaLimpia['source']:
                        listaUrls.append(self.limpiarLineaCrank(unaLinea))
        return listaUrls

    def limpiarLineaCrank(self,linea):
        unaLinea = linea.split("INFO:root:;")[1].split(";From;")
        if len(unaLinea) == 2:
            json = {}
            json['source'] = unaLinea[1]
            json['target'] = unaLinea[0]
            return json