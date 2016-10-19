from SupportVectorMachine.SVM import *
from preprocesamientoController import *
import numpy as np


class RIController:
    preprocesamiento = preprocesamientoController()
    svm = SVM()

    def __init__(self):
        pass

    def initSVM(self,path):

        self.preprocesamiento.lecturaSVM(path)
        #self.svm.setearAtributos(consulta)

        '''Diccionario con X e Y'''

        '''puntos = self.svm.obtenerAtributos(consulta)
        X = puntos['X']
        Y = puntos['Y']

        inicio = 1
        fin = 50
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
                    self.svm.ajustarParametros(C, kernel, .7, .3, X, Y, gamma=gamma)
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

        precisionAnt = 0
        for gamma in rangoGamma:
            for C in rangoC:

                print precision

                if precision > mejorCombinacion['precision']:
                    mejorCombinacion['precision'] = precision
                    mejorCombinacion['C'] = C
                    mejorCombinacion['gamma'] = gamma

                    print mejorCombinacion
                    print " ---------- "

                precisionAnt = precision


        lecturaArchivo('RankingSVM/data/prediccion.csv', 'predecir')
        X = getDocumentosAtributos('predecir')

        prediccion = unSVM.predecir(X)
        generarSalidaPrediccion(prediccion)'''