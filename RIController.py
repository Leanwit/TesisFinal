from SupportVectorMachine.SVM import *
from preprocesamientoController import *
import numpy as np
from sklearn.externals import joblib

class RIController:
    preprocesamiento = preprocesamientoController()
    svmNoRelevante = SVM()
    svmRelevante = SVM()
    svmMuyRelevante = SVM()
    def __init__(self):
        pass

    def clasificarSVM(self):
        if os.path.exists("Model/SVM/filename.pkl") and load:
            self.predecirListaUrls(conjuntos)

    def initSVM(self,path):

        self.preprocesamiento.lecturaSVM(path)
        self.iniciarSVM(self.svmNoRelevante,"norelevante",1)
        self.iniciarSVM(self.svmRelevante,"relevante",2)
        self.iniciarSVM(self.svmMuyRelevante,"muyrelevante",4)

    def predecirListaUrls(self,puntos):
        svm = joblib.load('Model/SVM/filename.pkl')

        X = puntos['xEntrenamiento']
        Y = puntos['yEntrenamiento']

        predicciones = svm.predict(X)

        print Y
        print "Inicio Prediccion"
        total = len(Y)
        aciertos = 0
        for prediccion, y in zip(predicciones, Y):
            print prediccion, y
            if prediccion == y:
                aciertos += 1

        print float(aciertos) / float(total)
        pass

    def inicializarParametrosIteracion(self):
        parametros = {}

        parametros['inicio'] = 1
        parametros['fin'] = 10
        parametros['incremento'] = 1

        parametros['rangoC'] = np.arange(parametros['inicio'], parametros['fin'], parametros['incremento'])
        parametros['rangoGamma'] = np.arange(parametros['inicio'], parametros['fin'], parametros['incremento'])
        parametros['kernels'] = ['rbf', 'poly', "linear"]

        return parametros

    def inicializarMejorCombinacion(self, parametros):

        mejorCombinacion = {}
        mejorCombinacion['precision'] = 0
        mejorCombinacion['C'] = parametros['inicio']
        mejorCombinacion['gamma'] = parametros['inicio']
        mejorCombinacion['kernel'] = parametros['kernels'][0]
        return mejorCombinacion

    def entrenarSVM(self, svm, parametros, X, Y):

        mejorCombinacion = self.inicializarMejorCombinacion(parametros)
        for kernel in parametros['kernels']:
            for gamma in parametros['rangoGamma']:
                for C in parametros['rangoC']:
                    svm.ajustarParametros(C, kernel, .8,.2, X, Y, gamma=gamma)
                    svm.training()
                    precision = svm.testing()
                    if precision > mejorCombinacion['precision']:
                        mejorCombinacion['precision'] = precision
                        mejorCombinacion['C'] = C
                        mejorCombinacion['gamma'] = gamma
                        mejorCombinacion['kernel'] = kernel
                        print mejorCombinacion
                        print " ---------- "
            print "fin kernel " + kernel

    def predecir(self, svm, X, Y):
        predicciones = svm.predecir(X)
        print "Inicio Prediccion"
        total = len(Y)
        aciertos = 0
        for prediccion, y in zip(predicciones, Y):
            if prediccion == y:
                aciertos += 1
        print float(aciertos) / float(total)

    def iniciarSVM(self,svm,name,limite):
        svm.setearAtributos()

        puntos = svm.obtenerAtributos(limite)
        conjuntos = svm.dividirConjuntoTesting(puntos, .8, .2)

        X = conjuntos['xEntrenamiento']
        Y = conjuntos['yEntrenamiento']

        parametros = self.inicializarParametrosIteracion()

        self.entrenarSVM(svm,parametros, X, Y)

        X = conjuntos['xTest']
        Y = conjuntos['yTest']
        self.predecir(svm,X, Y)

        joblib.dump(svm.instanciaSVM, 'Model/SVM/'+name+'.pkl')
        pass

    def rankingSVM(self, path):
        pass


