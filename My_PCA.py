import pprint

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from kneed import KneeLocator
from scipy import linalg


class My_PCA:
    number_of_components = 0

    def __init__(self, df1, df2=None):
        self.pca = PCA()
        self.df1 = df1
        self.df2 = df2
        self.combined = None

    def executePCA(self):
        if My_PCA.number_of_components == 0:
            self.findElbow()
        if len(self.df1) == 1:
            self.LUalgorithm()
        else:
            self.PCAalgorithm()

    def normalize_data(self):
        # Separating out the features
        # x = self.df.loc[:, features].values
        # Standardizing the features
        if len(self.df) > 1:
            x = StandardScaler().fit_transform(self.df)
            principalComponents = self.pca.fit_transform(x)
            self.df = pd.DataFrame(data=principalComponents)
        print(f"The dataset after Normalize is:\n {self.df}\n")

    def findElbow(self):
        self.combined = (np.append(self.df1, self.df2, axis=0))
        pca = PCA()
        pca.fit(self.combined)
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

        print(f"Elbow is: {My_PCA.number_of_components}")
        self.plot_data(x, y)
        # My_PCA.number_of_components = 692

    def LUalgorithm(self):
        # Compute the LU decomposition of the matrix
        P, L, U = linalg.lu(self.df1)
        print(f"P = {P.shape} , L = {L.shape} , U = {U.shape} , df = {self.df1.shape}")
        # Take the first four columns of U
        matrix_transformed = U[:, :My_PCA.number_of_components]
        print(matrix_transformed.shape)
        self.df1 = matrix_transformed

    def PCAalgorithm(self):
        if self.df2 is not None:
            extended = self.combined
        else:
            extended = self.df1
        pca = PCA(n_components=My_PCA.number_of_components)
        scaler = StandardScaler()
        scaler.fit(extended)
        scaled_data = scaler.transform(extended)
        result = pca.fit_transform(scaled_data)
        self.df1 = result[:len(self.df1)]
        self.df2 = result[len(self.df1):]

    def getMostSignificantFeatures(self):

        # self.covMat = np.cov(self.df)
        # print(f"cov = {type(self.covMat)}")
        # print("Finished calculating cov matrix")
        # eigenvalues, eigenvectors = np.linalg.eig(self.covMat)
        # self.eigen_pairs = [(eigenvalues[i], eigenvectors[:, i]) for i in range(len(eigenvalues))]
        # self.eigen_pairs.sort(key=lambda x: x[0], reverse=True)
        # print("Finished calculating eigen_pairs")
        # if self.number_of_components is None:
        #     self.findKnee()
        # col_list = []
        # for i in range(self.number_of_components): col_list.append(f"Feature {i + 1}")
        # result_df = pd.DataFrame(columns=col_list)
        # eigenvectors = []
        # for pair in self.eigen_pairs: eigenvectors.append(pair[1])
        # total_num_of_iterations = (len(self.df)) * self.number_of_components * len(eigenvectors)
        # counter = 0
        # for index, row in self.df.iterrows():
        #     new_row = []
        #     for column_index in range(self.number_of_components):
        #         sum = 0
        #         for eigenvectors_index in range(len(eigenvectors)):
        #             sum = sum + (float(row[column_index]) * float(eigenvectors[column_index][eigenvectors_index]))
        #             # print(
        #             # f"Iteration: {counter} / {total_num_of_iterations} = {(counter / total_num_of_iterations) * 100}%\tFeatures to take: {self.number_of_components} ")
        #             counter = counter + 1
        #         new_row.append(sum)
        #     result_df.loc[len(result_df)] = new_row
        # self.df = result_df
        print(f"after {self.df[0][:20]}")

    def decide_args(self, accuracy):
        print("Entered decide_args")
        self.covMat = np.cov(self.df)
        feat_lst = self.pca.explained_variance_ratio_
        eigenvalues, eigenvectors = np.linalg.eig(self.covMat)
        eigen_pairs = [(eigenvalues[i], eigenvectors[:, i]) for i in range(len(eigenvalues))]
        eigen_pairs.sort(key=lambda x: x[0], reverse=True)
        full_dict = {}
        for i in eigen_pairs:
            full_dict.update({i[0]: i[1]})
        pprint.pprint(f"The full dict: {full_dict}\n")
        print(f"Features priority list: {feat_lst}\n")
        x = []
        y = []
        counter = 0
        sum = 0
        for f in feat_lst:
            sum = sum + f
            counter = counter + 1
            x.append(counter)
            y.append(sum)
            if sum > accuracy:
                break;
        print(f"In order to get {accuracy * 100}%, you need {counter} features\n")
        return x, y

    def plot_data(self, num, acc):
        plt.scatter(num, acc)
        plt.xlabel('Features Number')
        plt.ylabel('Accuracy %')
        plt.show()
