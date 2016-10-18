from SupportVectorMachine.SVM import *
from preprocesamientoController import *


class RIController:
    preprocesamiento = preprocesamientoController()
    svm = SVM()

    def __init__(self):
        pass

    def initSVM(self,path,consulta):

        self.preprocesamiento.lecturaSVM(path,consulta)

        self.svm.setearAtributos(consulta)

        '''X = getDocumentosAtributos('entrenamiento')
        Y = getDocumentosClase()

        inicio = 0.0001
        fin = 1
        incremento = 0.001

        rangoC = np.arange(inicio, fin, incremento)
        rangoGamma = np.arange(inicio, fin, incremento)

        mejorCombinacion = {}
        mejorCombinacion['precision'] = 0
        mejorCombinacion['C'] = inicio
        mejorCombinacion['gamma'] = inicio
        precisionAnt = 0
        for gamma in rangoGamma:
            for C in rangoC:
                unSVM = SVM(C, 'poly', .8, .2, X, Y, gamma=gamma)
                unSVM.training()

                precision = unSVM.testing()

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