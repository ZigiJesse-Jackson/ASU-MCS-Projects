import pandas as pd
import numpy as np
import random
import sys
from collections import deque
import math

class DBSCAN_Point:
    def __init__(self, point, type, pos):
        self.point = point
        # types are:
        # 'c' for core point
        # 'b' for border point
        # 'n' for noise point
        self.type = type
        self.pos = pos

def read_and_transform_data(csv_file, columns):
    data = pd.read_csv(csv_file, low_memory='False', usecols=columns)
    data['Datetime'] = pd.to_datetime(data['Date']+" "+data['Time'])
    data = data.drop(columns=['Date', 'Time'])
    data = data.sort_values('Datetime')
    data = data.reset_index(drop=True)
    return data

def get_meal_times_from_insulin(insulin_df):
    insulin_meal_times = insulin_df.dropna()
    insulin_meal_times = insulin_meal_times.drop(insulin_df[insulin_df['BWZ Carb Input (grams)']==0].index)

    time_diffs = insulin_meal_times['Datetime'].diff()

    # Define the time threshold (2 hours)
    t_2h = pd.Timedelta(hours=2)
    # t_30m = pd.Timedelta(minutes=30)

    # Filter and include rows where the time difference from the next row is greater than 2 hours
    meal_times = insulin_meal_times[
        (time_diffs > t_2h) | (time_diffs.isna() & (insulin_meal_times['Datetime'].diff(periods=-1) > t_2h))
    ]

    return meal_times

def create_bins(insulin_meal_times):
    max_carb = insulin_meal_times['BWZ Carb Input (grams)'].max()
    min_carb = insulin_meal_times['BWZ Carb Input (grams)'].min()
    bins = []
    last_bin = min_carb
    while(last_bin<max_carb):
        bins.append(last_bin+20)
        last_bin +=20
    return bins

def find_bin(data_point, bins):
    l = 0
    r = len(bins)-1
    mid = l + ((r-l)//2)
    while(l<=r):
        if(bins[mid] == data_point): return mid
        if(bins[mid]<data_point):
            l = mid+1
            mid = l + ((r-l)//2)
        else:
            r = mid-1
            mid = l+ ((r-l)//2)
    return l

def extract_data(meal_times, cgm_data, insulin_data, bins):
    meal_matrix = []
    bin_matrix = []
    for meal_time in meal_times['Datetime']:
        # cgm data closest to insulin mealtime 
        meal_time_index = cgm_data[cgm_data['Datetime']>=meal_time].idxmin().values[1]
        # extracting preceding 30min (6 rows) and succeeding 2hr (24 rows)
        meal_row = cgm_data.iloc[meal_time_index-6: meal_time_index+24]['Sensor Glucose (mg/dL)']
        #if nan count > 6 we skip else we perform cubic interpolation
        if meal_row.count()<24:
            continue
        meal_row = meal_row.interpolate(method='cubic')
        # edge case of nan values at beginning or end of meal_row
        meal_row = meal_row.dropna()
        if(len(meal_row)<30):
            continue
        meal_row = meal_row.to_list()
        meal_row = [round(x) for x in meal_row]
        carb_intake = insulin_data[insulin_data['Datetime']==meal_time]['BWZ Carb Input (grams)'].values[0]
        bin_matrix.append(find_bin(carb_intake, bins))
        meal_matrix.append(meal_row)
    return meal_matrix, bin_matrix


def get_index(start, end, data, max=True):
    ix = start
    curr_x = data[start]
    for i in range(start + 1, end):
        if max:
            if curr_x <= data[i]:
                curr_x = data[i]
                ix = i
        else:
            if curr_x >= data[i]:
                curr_x = data[i]
                ix = i
    return ix

def extract_features(training_matrix):
    features = []
    for data in training_matrix:
        data_features = []
        t = get_index(0, 8, data, False)
        trough = data[t]
        p = get_index(t, 30, data)
        peak = data[p]
        
        # f1, difference between start of meal and peak cgm level post start of meal
        data_features.append((p-t)*5)
        # # f2, difference between cgm level at start of meal and  " "
        data_features.append(peak-trough)
        # #f3, normalized f2 by start of meal
        data_features.append((peak-trough)/trough)
        # f4, variance of meal cgm levels
        data_features.append(np.var(data))
        #f5, mean of cgm values
        data_features.append(np.mean(data))

        features.append(data_features)
    return features


# Calculate euclidean distance between two points
def calcDist(point1, point2):
    sqr_dist = 0
    for i in range(0, len(point1)):
        sqr_dist+= (point1[i]-point2[i])**2
    return (sqr_dist)**0.5

# Calculate the k-means SSE-loss
def kMeansError(kMeans: list, data: list )->float:
    err = 0
    for d in data:
        d = list(d)
        min_error = sys.maxsize
        for mean in kMeans:
            min_error = min(calcDist(d, mean)**2, min_error)
        err+=min_error
    return err

# Classify data into clusters
def findClusters(kMeans: list, data: list )->float:
    clusters = dict()
    for k in kMeans:
        clusters[k] = []
    for d in data:
        dist = sys.maxsize
        closest = ()
        for mu in kMeans:
            dist_to_mu = calcDist(d, mu)
            if dist>dist_to_mu:
                dist = dist_to_mu
                closest = mu
        clusters[closest].append(d)
    return clusters

# Calculate centermost point in a cluster for each cluster
def findCentroids(clusters: dict)->list:
    centroids = []
    for key in clusters.keys():
#         calculate average point in cluster
        if(len(clusters[key])==0):
            centroids.append(tuple(key))
            continue
        centroid = np.mean(clusters[key], axis=0)
        centroids.append(tuple(centroid))
    return centroids

# Find most means in data using k-means algorithm
def kMeansCalc(newMeans: list, data: list)->list:
    oldMeans = []
    while set(oldMeans)!=set(newMeans):
        clusters = findClusters(newMeans, data)
        oldMeans = newMeans
        newMeans = findCentroids(clusters)
    return newMeans

# Initialize means with K-Means++ approach
def initializeRandomMeans(data: list, k:int)->list:
    means = [data[random.randrange(len(data))]]
    
    i=1
    while i<k:
        avg_max = ()
        max_avg_dist = 0
        for d in data:
            if d in means:
                continue
            dist = 0
            for mean in means:
                dist += calcDist(d, mean)
            avg_dist = dist/len(means)
            if max_avg_dist< avg_dist:
                max_avg_dist = avg_dist
                avg_max = d
        means.append(avg_max)
        i+=1
    return means
                
# Find furthest point from a given a point, given list of points 
def findFurthest(point: tuple, data: list):
    longest = 0
    p = ()
    for d in data:
        dist = calcDist(d, point)
        if dist>longest:
            longest = dist
            p = d
    return p

# Parameters for DBSCAN
# developed by finding elbow of graph of distance to a stated k neighbours
# current parameters tuned already
# use 
eps = 50
min_pts = 10

# You can use the code below to plot such a graph
# import heapq
# import seaborn as sns
# def find_eps(data_points, k):
#     k_nearest_list = []
#     for i in range(len(data_points)):
#         point_a = data_points[i]
#         distances = []
#         for j in range(len(data_points)):
#             if i == j: continue
#             point_b = data_points[j]
#             distances.append(calcDist(point_a, point_b))
#         heapq.heapify(distances)
#         k_dist = heapq.nsmallest(k, distances)
#         k_nearest_list.append((k_dist[-1], point_a))
#     return k_nearest_list

# k_nearest_dist = find_eps(meal_features, 4)
# k_nearest_dist.sort(key=lambda a: a[0])
# y = [x[0] for x in k_nearest_dist]
# x = [i for i in range(len(k_nearest_dist))]
# sns.lineplot(x=x, y=y)


# labeling points as core, border or noise points
def label_data(data, eps, min_pts):
    data = [DBSCAN_Point(data[i], 'n', i) for i in range(len(data))]
    for i in range(len(data)):
        data_a = data[i]
        points_in_range_indices = []
        for j in range(len(data)):
            if i == j: continue
            data_b = data[j]
            dist = calcDist(data_a.point, data_b.point)
            if dist<=eps: points_in_range_indices.append(j)
        if len(points_in_range_indices)+1>=min_pts:
            data[i].type = 'c'
            for j in points_in_range_indices:
                if data[j].type == 'n':
                    data[j].type == 'b'
    return data


def assign_border_points(clusters, clusters_indices, eps, noiseless_data:list[DBSCAN_Point]):
    for i in range(len(noiseless_data)):
        if noiseless_data[i].type!='b': continue
        data_a = noiseless_data[i]
        min = sys.maxsize
        min_i = -1
        # check which cluster border point is closest to
        for j in range(len(noiseless_data)):
            if i==j or noiseless_data[j].type!='c': continue
            data_b = noiseless_data[j]
            dist = calcDist(data_a.point, data_b.point)
            if(dist<=eps and dist < min):
                min = dist
                min_i = j
        if min_i >-1:
            # noiseless_data[i].type = 'c'
            # assign border point to closest cluster
            for x in range(len(clusters)):
                if min_i in clusters_indices[x]:
                    clusters_indices[x].add(i)
                    clusters[x].append(data_a.point)
                    break
    return clusters

def cluster_DBSCAN_labeled_points(data: list[DBSCAN_Point], eps):
    noiseless_data = [x for x in data if x.type!='n']
    visited = set()
    clusters = []
    clusters_indices = []

    for i in range(len(noiseless_data)):
        if i in visited: continue
        q = deque()
        q.append(i)
        cluster = [noiseless_data[i].point]
        cluster_indices = {i}
        # performing bfs to find clusters
        while(len(q)!=0):
            curr_i = q.popleft()
            curr_data = noiseless_data[curr_i]
            for j in range(len(noiseless_data)):
                if j == i or j in visited: continue
                next_data = noiseless_data[j]
                dist = calcDist(curr_data.point, next_data.point)
                if dist<=eps and next_data.type == 'c': 
                    visited.add(j)
                    cluster.append(next_data.point)
                    cluster_indices.add(j)
                    q.append(j)
                    
        clusters.append(cluster)
        clusters_indices.append(cluster_indices)

    clusters = assign_border_points(clusters, clusters_indices, eps, noiseless_data)
    return clusters

def calc_SSE_Clusters(clusters):
    total_sse = 0
    for cluster in clusters:
        total_sse+=calc_SSE(cluster)
    return total_sse

def calc_SSE(cluster):
    sse = 0
    c_mu = np.mean(cluster, axis=0)
    for i in range(len(cluster)):
        sse+= calcDist(c_mu, cluster[i])**2
    return sse
    
def bisecting_k_means(k, clusters):
    ordered_clusters_SSE = [(calc_SSE(cluster), cluster) for cluster in clusters]
    ordered_clusters_SSE.sort(key=lambda x: x[0])
    while(len(ordered_clusters_SSE)<k):
        curr_cluster = ordered_clusters_SSE[-1][1]
        ordered_clusters_SSE = ordered_clusters_SSE[:-1]
        means = initializeRandomMeans( curr_cluster, 2)
        means = [tuple(x) for x in means]
        curr_cluster = [tuple(x) for x in curr_cluster]
        new_clusters = [*findClusters(kMeansCalc(means, curr_cluster), curr_cluster).values()]
        cluster1 = new_clusters[0]
        cluster2 = new_clusters[1]
        ordered_clusters_SSE.append((calc_SSE(cluster1), cluster1))
        ordered_clusters_SSE.append((calc_SSE(cluster2), cluster2))
        ordered_clusters_SSE.sort(key=lambda x: x[0])
    return [x[1] for x in ordered_clusters_SSE]
        
def fill_cluster_classes(clusters, len_bins, bin_matrix, original_data):
    clusters_x_bins_matrix = []
    for i in range(len(clusters)):
        cluster_classes = [0]*len_bins
        for j in range(len(clusters[i])):
            b_i = bin_matrix[original_data.index(clusters[i][j])]
            cluster_classes[b_i]+=1
        clusters_x_bins_matrix.append(cluster_classes)

    return clusters_x_bins_matrix

def entropy(list):
    res = 0
    sum_1 = sum(list)
    for i in list:
        if(i==0): continue
        entropy_i = (i/sum_1)*math.log2(i/sum_1)
        res += (entropy_i)*-1
    return round(res, 2)

def purity(list):
    res = 0
    sum_1 = sum(list)
    for i in list:
        res = max(res, i/sum_1)
    return round(res,2)

def calc_total_cluster_measure(cluster_x_bin_matrix, func):
    total_entropy = []
    total_sum = 0
    for cluster in cluster_x_bin_matrix:
        sum_c = sum(cluster)
        total_entropy.append(func(cluster)*sum_c)
        total_sum+=sum_c
    total_entropy = [x/total_sum for x in total_entropy]
    return sum(total_entropy)


def main():
    cgm_data = read_and_transform_data('CGMData.csv', columns=['Date', 'Time', 'Sensor Glucose (mg/dL)'])
    insulin_data = read_and_transform_data('InsulinData.csv', columns=['Date', 'Time', 'BWZ Carb Input (grams)'])
    
    insulin_data_meal_times = get_meal_times_from_insulin(insulin_data)
    bins = create_bins(insulin_data_meal_times)

    meals_data, bin_matrix = extract_data(insulin_data_meal_times, cgm_data, insulin_data, bins)
    meal_features = extract_features(meals_data)

    means = initializeRandomMeans( meal_features, len(bins))
    means = [tuple(x) for x in means]
    meal_features = [tuple(x) for x in meal_features]
    clusters_kmeans = [*findClusters(kMeansCalc(means, meal_features), meal_features).values()]

    data_db = label_data(meal_features, eps, min_pts)
    clusters_dbscan = cluster_DBSCAN_labeled_points(data_db, eps)
    clusters_dbscan = bisecting_k_means(len(clusters_kmeans), clusters_dbscan)

    clusters_x_bins_matrix_k_means = fill_cluster_classes(clusters_kmeans, 7, bin_matrix, meal_features)
    clusters_x_bins_matrix_dbscan = fill_cluster_classes(clusters_dbscan, 7, bin_matrix, meal_features)

    kmeans_sse = calc_SSE_Clusters(clusters_kmeans)
    dbscan_sse = calc_SSE_Clusters(clusters_dbscan)
    k_means_entropy = calc_total_cluster_measure(clusters_x_bins_matrix_k_means, entropy)
    k_means_purity = calc_total_cluster_measure(clusters_x_bins_matrix_k_means, purity)
    dbscan_entropy = calc_total_cluster_measure(clusters_x_bins_matrix_dbscan, entropy)
    dbscan_purity = calc_total_cluster_measure(clusters_x_bins_matrix_dbscan, entropy)

    results_df = pd.DataFrame(
        [[kmeans_sse, dbscan_sse, k_means_entropy, dbscan_entropy, k_means_purity, dbscan_purity]]
    )
    result_vals = results_df.values

        # Output the results to a CSV file
    pd.DataFrame(result_vals).to_csv("Result.csv", index=False, header=False)




if __name__ == "__main__":
    main()