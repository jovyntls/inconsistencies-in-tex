from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from sklearn import datasets
import pandas as pd

data_raw = pd.read_csv('../logs/20240205_200640_imgcompare.csv')
data_raw = data_raw.set_index('identifier')

KEYWORD = 'xelua'

# split the data accordingly
filtered_data = pd.DataFrame()
for colname in data_raw.columns:
    if KEYWORD not in colname: continue
    filtered_data[colname.replace(f'{KEYWORD}_', '')] = data_raw[colname]

# set and clean the input data
X = filtered_data.dropna()
# add new data
X['mean'] = X.mean(axis=1)
X['stdev'] = X.std(axis=1)
X['cw-ssim'] = X['CWSSIM'] - X['SSIM']
print(X.head())

#KMeans
km = KMeans(n_clusters=2)
km.fit(X)
km.predict(X)
labels = km.labels_
#Plotting
fig = plt.figure()
ax = fig.add_subplot(projection='3d')
# ax = Axes3D(fig, rect=[0, 0, 1, 1])

ax.scatter(X.loc[:, 'mean'], X.loc[:, 'stdev'], X.loc[:, 'cw-ssim'],
          c = labels, edgecolor="k", s=50)
ax.set_xlabel('mean')
ax.set_ylabel('stdev')
ax.set_zlabel('cw-ssim')
plt.title("K Means", fontsize=14)
plt.show()
