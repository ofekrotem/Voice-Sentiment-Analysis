import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from kneed import KneeLocator


class My_PCA:
    number_of_components = None
    loaded_data = None

    def __init__(self, df1, df2=None):
        self.pca = PCA()
        self.df1 = df1
        self.df2 = df2
        if My_PCA.loaded_data is None:
            if self.df2 is not None:
                My_PCA.loaded_data = (np.append(self.df1, self.df2, axis=0))
            else:
                My_PCA.loaded_data = self.df1
        if My_PCA.number_of_components is None:
            self.findElbow()

    def executePCA(self):
        if len(self.df1) == 1:
            self.PCAalgorithm(isRecording=True)
        else:
            self.PCAalgorithm(isRecording=False)

    def findElbow(self):
        pca = PCA()
        pca.fit(My_PCA.loaded_data)
        feat_lst = pca.explained_variance_ratio_
        x = []
        y = []
        counter = 0
        sum = 0
        for f in feat_lst:
            sum = sum + f
            counter = counter + 1
            x.append(counter)
            y.append(sum)

        kn = KneeLocator(x, y, curve='concave', direction='increasing', interp_method='polynomial')
        My_PCA.number_of_components = kn.elbow

        print(
            f"Elbow is: {My_PCA.number_of_components}, preserving {y[My_PCA.number_of_components] * 100}% of the variance")
        self.plot_data(x, y)

    def PCAalgorithm(self, isRecording: bool):
        if isRecording:
            extended = (np.append(My_PCA.loaded_data, self.df1, axis=0))
        else:
            extended = My_PCA.loaded_data

        pca = PCA(n_components=My_PCA.number_of_components)
        scaler = StandardScaler()
        scaler.fit(extended)
        scaled_data = scaler.transform(extended)
        result = pca.fit_transform(scaled_data)
        if isRecording:
            self.df1 = result[len(My_PCA.loaded_data):]
        else:
            self.df1 = result[:len(self.df1)]
            self.df2 = result[len(self.df1):]

    def plot_data(self, num, acc):
        plt.scatter(num, acc)
        plt.xlabel('Features Number')
        plt.ylabel('Accuracy %')
        plt.show()
