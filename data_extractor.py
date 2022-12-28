import os
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torchaudio
import tqdm
from speechbrain.pretrained import EncoderClassifier

from My_PCA import My_PCA
from utils import get_label, extract_feature, get_first_letters


class AudioExtractor:
    """A class that is used to featurize audio clips, and provide
    them to the machine learning algorithms for training and testing"""

    def __init__(self, audio_config=None, verbose=1, features_folder_name="features",
                 classification=True,
                 emotions=['sad', 'neutral', 'happy'], balance=True):
        """
        Params:
            audio_config (dict): the dictionary that indicates what features to extract from the audio file,
                default is {'mfcc': True, 'chroma': True, 'mel': True, 'contrast': False, 'tonnetz': False}
                (i.e mfcc, chroma and mel)
            verbose (bool/int): verbosity level, 0 for silence, 1 for info, default is 1
            features_folder_name (str): the folder to store output features extracted, default is "features".
            classification (bool): whether it is a classification or regression, default is True (i.e classification)
            emotions (list): list of emotions to be extracted, default is ['sad', 'neutral', 'happy']
            balance (bool): whether to balance dataset (both training and testing), default is True
        """
        self.audio_config = audio_config if audio_config else {'mfcc': True, 'chroma': True, 'mel': True,
                                                               'contrast': False, 'tonnetz': False}
        self.verbose = verbose
        self.features_folder_name = features_folder_name
        self.classification = classification
        self.emotions = emotions
        self.balance = balance
        # input dimension
        self.input_dimension = None

        # self.featureCol_list = []
        # for i in range(0, 180): self.featureCol_list.append(f"Feature {i + 1}")
        # self.xVectorCol_list = []
        # for i in range(0, 512): self.xVectorCol_list.append(f"Feature {i + 1}")
        # self.combineCol_list = []
        # for i in range(0, 692): self.combineCol_list.append(f"Feature {i + 1}")
        # self.featuresDf = pd.DataFrame(columns=self.featureCol_list)
        # self.xVectorDf = pd.DataFrame(columns=self.xVectorCol_list)
        # self.combineDf = pd.DataFrame(columns=self.combineCol_list)

    def _load_data(self, desc_files, partition, shuffle):
        self.load_metadata_from_desc_file(desc_files, partition)
        # balancing the datasets ( both training or testing )
        if partition == "train" and self.balance:
            self.balance_training_data()
        elif partition == "test" and self.balance:
            self.balance_testing_data()
        else:
            if self.balance:
                raise TypeError("Invalid partition, must be either train/test")
        if shuffle:
            self.shuffle_data_by_partition(partition)

    def load_train_data(self, desc_files=["train_speech.csv"], shuffle=False):
        """Loads training data from the metadata files `desc_files`"""
        self._load_data(desc_files, "train", shuffle)

    def load_test_data(self, desc_files=["test_speech.csv"], shuffle=False):
        """Loads testing data from the metadata files `desc_files`"""
        self._load_data(desc_files, "test", shuffle)

    def shuffle_data_by_partition(self, partition):
        if partition == "train":
            self.train_audio_paths, self.train_emotions, self.train_features = shuffle_data(self.train_audio_paths,
                                                                                            self.train_emotions,
                                                                                            self.train_features)
        elif partition == "test":
            self.test_audio_paths, self.test_emotions, self.test_features = shuffle_data(self.test_audio_paths,
                                                                                         self.test_emotions,
                                                                                         self.test_features)
        else:
            raise TypeError("Invalid partition, must be either train/test")

    def load_metadata_from_desc_file(self, desc_files, partition):
        """Read metadata from a CSV file & Extract and loads features of audio files
        Params:
            desc_files (list): list of description files (csv files) to read from
            partition (str): whether is "train" or "test"
        """
        # empty dataframe
        df = pd.DataFrame({'path': [], 'emotion': []})
        for desc_file in desc_files:
            # concat dataframes
            df = pd.concat((df, pd.read_csv(desc_file)), sort=False)
        if self.verbose:
            print("[*] Loading audio file paths and its corresponding labels...")
        # get columns
        audio_paths, emotions = list(df['path']), list(df['emotion'])
        # if not classification, convert emotions to numbers
        if not self.classification:
            # so naive and need to be implemented
            # in a better way
            if len(self.emotions) == 3:
                self.categories = {'sad': 1, 'neutral': 2, 'happy': 3}
            elif len(self.emotions) == 5:
                self.categories = {'angry': 1, 'sad': 2, 'neutral': 3, 'ps': 4, 'happy': 5}
            else:
                raise TypeError(
                    "Regression is only for either ['sad', 'neutral', 'happy'] or ['angry', 'sad', 'neutral', 'ps', 'happy']")
            emotions = [self.categories[e] for e in emotions]
        # make features folder if does not exist
        if not os.path.isdir(self.features_folder_name):
            os.mkdir(self.features_folder_name)
        # get label for features
        label = get_label(self.audio_config)
        # construct features file name
        n_samples = len(audio_paths)
        first_letters = get_first_letters(self.emotions)
        name = os.path.join(self.features_folder_name, f"{partition}_{label}_{first_letters}_{n_samples}.npy")
        if os.path.isfile(name):
            # if file already exists, just load then
            if self.verbose:
                print("[+] Feature file already exists, loading...")
            features = np.load(name)
        else:
            # file does not exist, extract those features and dump them into the file
            features = []
            append = features.append
            classifier = EncoderClassifier.from_hparams(source="speechbrain/spkrec-xvect-voxceleb",
                                                        savedir="pretrained_models/spkrec-xvect-voxceleb")
            path_counter = 0

            for audio_file in tqdm.tqdm(audio_paths, f"Extracting features for {partition}"):
                feature = extract_feature(audio_file, **self.audio_config)
                if self.input_dimension is None:
                    self.input_dimension = feature.shape[0]

                signal, fs = torchaudio.load(audio_paths[path_counter])
                path_counter = path_counter + 1
                embeddings = classifier.encode_batch(signal)
                embeddings = embeddings.detach().cpu().numpy()
                embedding = embeddings[0][0]
                # self.featuresDf.loc[len(self.featuresDf.index)] = (list(feature))
                # print(f"Features new rank: {self.featuresDf.shape}")
                # self.xVectorDf.loc[len(self.xVectorDf.index)] = (list(embedding))
                # print(f"xVector new rank: {self.xVectorDf.shape}")
                # print(f"the df is:\n {testdf}")
                # print(f"The Xvect is {len(embedding)}:\n {embedding}")
                # print(f"({len(feature)}) features before adding x: {feature}")
                feature = np.concatenate((feature, embedding))
                # self.combineDf.loc[len(self.combineDf.index)] = (list(feature))
                # print(f"Combined new rank: {self.combineDf.shape}")
                # print(f"({len(feature)}) features after adding x: {feature}")
                append(feature)
            # self.combineDf.to_csv("Combine.csv")
            # self.xVectorDf.to_csv("xVector.csv")
            # self.featuresDf.to_csv("features.csv")
            # testdf.to_csv("Test_DF.csv")
            # traindf.to_csv("Train_DF.csv")
            # convert to numpy array
            features = np.array(features)
            # save it
            np.save(name, features)
        if partition == "train":
            try:
                self.train_audio_paths
            except AttributeError:
                self.train_audio_paths = audio_paths
                self.train_emotions = emotions
                self.train_features = features
                print(f"Trainnnnnnn : {self.train_features.shape}")
                print(f"Trainnnnnnn : {self.train_features}")
            else:
                if self.verbose:
                    print("[*] Adding additional training samples")
                self.train_audio_paths += audio_paths
                self.train_emotions += emotions
                self.train_features = np.vstack((self.train_features, features))
                print(f"train features: {self.train_features}")
        elif partition == "test":
            try:
                self.test_audio_paths
            except AttributeError:
                self.test_audio_paths = audio_paths
                self.test_emotions = emotions
                self.test_features = features
            else:
                if self.verbose:
                    print("[*] Adding additional testing samples")
                self.test_audio_paths += audio_paths
                self.test_emotions += emotions
                self.test_features = np.vstack((self.test_features, features))
        else:
            raise TypeError("Invalid partition, must be either train/test")

    def plotPCA(self):
        featurePCA = My_PCA(self.featuresDf, 180)
        xVectorPCA = My_PCA(self.xVectorDf, 512)
        combinePCA = My_PCA(self.combineDf, 692)
        featurePCA.normalize_data(self.featureCol_list)
        xVectorPCA.normalize_data(self.xVectorCol_list)
        combinePCA.normalize_data(self.combineCol_list)
        print("Finished normalizing data")
        (featureX, featureY) = featurePCA.decide_args(1)
        (xVectorX, xVectorY) = xVectorPCA.decide_args(1)
        (combineX, combineY) = combinePCA.decide_args(1)
        plt.plot(featureX, featureY, label="Features")
        plt.plot(xVectorX, xVectorY, label="xVector")
        plt.plot(combineX, combineY, label="Combined")
        plt.xlabel('Features Number')
        plt.ylabel('Variance Conservation %')
        plt.legend()
        plt.show()

    def _balance_data(self, partition):
        if partition == "train":
            emotions = self.train_emotions
            features = self.train_features
            audio_paths = self.train_audio_paths
        elif partition == "test":
            emotions = self.test_emotions
            features = self.test_features
            audio_paths = self.test_audio_paths
        else:
            raise TypeError("Invalid partition, must be either train/test")

        count = []
        if self.classification:
            for emotion in self.emotions:
                count.append(len([e for e in emotions if e == emotion]))
        else:
            # regression, take actual numbers, not label emotion
            for emotion in self.categories.values():
                count.append(len([e for e in emotions if e == emotion]))
        # get the minimum data samples to balance to
        minimum = min(count)
        if minimum == 0:
            # won't balance, otherwise 0 samples will be loaded
            print("[!] One class has 0 samples, setting balance to False")
            self.balance = False
            return
        if self.verbose:
            print("[*] Balancing the dataset to the minimum value:", minimum)
        d = defaultdict(list)
        if self.classification:
            counter = {e: 0 for e in self.emotions}
        else:
            counter = {e: 0 for e in self.categories.values()}
        for emotion, feature, audio_path in zip(emotions, features, audio_paths):
            if counter[emotion] >= minimum:
                # minimum value exceeded
                continue
            counter[emotion] += 1
            d[emotion].append((feature, audio_path))

        emotions, features, audio_paths = [], [], []
        for emotion, features_audio_paths in d.items():
            for feature, audio_path in features_audio_paths:
                emotions.append(emotion)
                features.append(feature)
                audio_paths.append(audio_path)

        if partition == "train":
            self.train_emotions = emotions
            self.train_features = features
            self.train_audio_paths = audio_paths
        elif partition == "test":
            self.test_emotions = emotions
            self.test_features = features
            self.test_audio_paths = audio_paths
        else:
            raise TypeError("Invalid partition, must be either train/test")

    def balance_training_data(self):
        self._balance_data("train")

    def balance_testing_data(self):
        self._balance_data("test")


def shuffle_data(audio_paths, emotions, features):
    """ Shuffle the data (called after making a complete pass through 
        training or validation data during the training process)
    Params:
        audio_paths (list): Paths to audio clips
        emotions (list): Emotions in each audio clip
        features (list): features audio clips
    """
    p = np.random.permutation(len(audio_paths))
    audio_paths = [audio_paths[i] for i in p]
    emotions = [emotions[i] for i in p]
    features = [features[i] for i in p]
    return audio_paths, emotions, features


def executePCA(trainX, testX):
    pca = My_PCA(trainX, testX)
    pca.executePCA()
    return pca.df1, pca.df2


def load_data(train_desc_files, test_desc_files, audio_config=None, classification=True,
              shuffle=True,
              balance=True, emotions=['sad', 'neutral', 'happy']):
    # instantiate the class
    audiogen = AudioExtractor(audio_config=audio_config,
                              classification=classification, emotions=emotions,
                              balance=balance, verbose=0)
    # Loads training data
    audiogen.load_train_data(train_desc_files, shuffle=shuffle)
    # Loads testing data
    audiogen.load_test_data(test_desc_files, shuffle=shuffle)
    # audiogen.plotPCA()
    # X_train, X_test, y_train, y_test
    x_train, x_test = executePCA(audiogen.train_features, audiogen.test_features)
    return {
        "X_train": x_train,
        "X_test": x_test,
        "y_train": np.array(audiogen.train_emotions),
        "y_test": np.array(audiogen.test_emotions),
        "train_audio_paths": audiogen.train_audio_paths,
        "test_audio_paths": audiogen.test_audio_paths,
        "balance": audiogen.balance,
    }
