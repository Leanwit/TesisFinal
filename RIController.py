from SupportVectorMachine.SVM import *
from preprocesamientoController import *
import numpy as np
from sklearn.externals import joblib

class RIController:
    preprocesamiento = preprocesamientoController()
    svm = SVM()

    def __init__(self):
        pass

    def initSVM(self,path,load = False, valorRelevancia = 2):

        self.preprocesamiento.lecturaSVM(path)
        self.svm.setearAtributos()

        '''Diccionario con X e Y'''

        puntos = self.svm.obtenerAtributos(valorRelevancia)
        conjuntos = self.svm.dividirConjuntoTesting(puntos,.8,.2)

        X = conjuntos['xEntrenamiento']
        Y = conjuntos['yEntrenamiento']

        if os.path.exists("Model/SVM/filename.pkl") and load:
            self.predecirListaUrls(conjuntos)
        else:

            inicio = 0.01
            fin = 10
            incremento = 1

            rangoC = np.arange(inicio, fin, incremento)
            rangoGamma = np.arange(inicio, fin, incremento)
            kernels = ['rbf','poly',"linear"]

            mejorCombinacion = {}
            mejorCombinacion['precision'] = 0
            mejorCombinacion['C'] = inicio
            mejorCombinacion['gamma'] = inicio
            mejorCombinacion['kernel'] = kernels[0]


            for kernel in kernels:
                for gamma in rangoGamma:
                    for C in rangoC:
                        self.svm.ajustarParametros(C, kernel, .7,.3, X, Y, gamma=gamma)
                        self.svm.training()
                        precision = self.svm.testing()
                        if precision > mejorCombinacion['precision']:
                            mejorCombinacion['precision'] = precision
                            mejorCombinacion['C'] = C
                            mejorCombinacion['gamma'] = gamma
                            mejorCombinacion['kernel'] = kernel
                            print mejorCombinacion
                            print " ---------- "
                print "fin kernel " + kernel




            X = conjuntos['xTest']
            Y = conjuntos['yTest']
            predicciones = self.svm.predecir(X)

            print Y
            print "Inicio Prediccion"
            total = len(Y)
            aciertos = 0
            for prediccion, y in zip(predicciones,Y):
                print prediccion, y
                if prediccion == y:
                    aciertos += 1

            print float(aciertos)/float(total)


            joblib.dump(self.svm.instanciaSVM, 'Model/SVM/filename.pkl')

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