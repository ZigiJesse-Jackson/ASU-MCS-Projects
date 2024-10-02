import pandas as pd
import numpy as np
import scipy.fft as fft
from sklearn import svm, model_selection, tree
import pickle

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
    ]['Datetime']

    return meal_times

def extract_meal_data(meal_times, cgm_data):
    meal_matrix = []
    for meal_time in meal_times:
        # cgm data closest to insulin mealtime 
        meal_time_index = cgm_data[cgm_data['Datetime']>=meal_time].idxmin().values[1]
        # extracting preceding 30min (6 rows) and succeeding 2hr (24 rows)
        meal_row = cgm_data.iloc[meal_time_index-5: meal_time_index+25]['Sensor Glucose (mg/dL)']
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
        meal_matrix.append(meal_row)
    return meal_matrix

def extract_no_meal_data(meal_times, cgm_data):
    # function to segment no meal gcm readings into 1x24 chunks
    def segment_no_meal_data(series):
        unsegmented_no_meal_data = series.to_list()
        num_records_to_ignore = len(unsegmented_no_meal_data)%24
        # ignore first 2 hour segment as it is meal data
        # ignore last record if it doesn't have 2 hours of data
        unsegmented_no_meal_data = unsegmented_no_meal_data[24:-num_records_to_ignore]
        segmented_no_meal_data = []
        for i in range(0,len(unsegmented_no_meal_data)-24,24):
            curr_segment = pd.Series(unsegmented_no_meal_data[i:i+24])
            # remove rows with more than 5 NaN values and perform linear interpolation
            # on rows with 5 or less NaN values
            if(curr_segment.count()<19):
                continue
            curr_segment = curr_segment.interpolate()
            # edge case of nan values at beginning or end of meal_row
            curr_segment = curr_segment.dropna()
            if(len(curr_segment)<24):
                continue 
            curr_segment = [round(x) for x in curr_segment]
            segmented_no_meal_data.append(curr_segment)

        return segmented_no_meal_data
    
    time_diffs = meal_times.diff()

    # Define the time threshold (4 hours)
    t_4h = pd.Timedelta(hours=4)

    # Filter and include rows where the time difference from the next row is greater than 4 hours
    meal_times = meal_times[
        (time_diffs >= t_4h) | (time_diffs.isna() & (meal_times.diff(periods=-1) >= t_4h))
    ]

    meal_times = meal_times.to_list()
    no_meal_matrix = []
    for i in range(len(meal_times)-1):
        # cgm data closest to insulin mealtimes 
        meal_time_index = cgm_data[cgm_data['Datetime']>=meal_times[i]].idxmin().values[1]
        next_meal_time_index = cgm_data[cgm_data['Datetime']>=meal_times[i+1]].idxmin().values[1]
        # cgm postprandrial data
        post_meal = cgm_data.iloc[meal_time_index:next_meal_time_index]['Sensor Glucose (mg/dL)']
        no_meal_data= segment_no_meal_data(post_meal)
        if(len(no_meal_data)!=0):
            no_meal_matrix +=no_meal_data
    
    return no_meal_matrix

def extract_fft_features(meal_data):
   fft_meal = fft.rfft(meal_data)
   fft_features = []
   # extract 2nd peak and its index from fft
   fft_features.append(max(fft_meal[1:]))
   fft_features.append(np.where(fft_meal==fft_features[0])[0][0])
   # extract 3rd peak and its index from fft
   fft_meal[fft_features[1]] = -np.inf
   fft_features.append(max(fft_meal[1:]))
   fft_features.append(np.where(fft_meal==fft_features[2])[0][0]) 
   fft_features[0] = round(fft_features[0].real, 2)
   fft_features[2] = round(fft_features[2].real, 2)

   return fft_features

def get_index(start, end, data, max=True):
    ix = start
    curr_x = data[start]
    for i in range(start, end):
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
        if(len(data)==30):
            t = get_index(3, 8, data, max=False)
            trough = data[t]
            p = get_index(t, 30, data)
            peak = data[p]
        else:
            t = get_index(0, 3, data) 
            trough = data[t]
            p = get_index(0, 24, data)
            peak = data[p]
        

        # f1-4 set, 2nd and 3rd peaks of FFT on meal data and their location/index
        data_features+=extract_fft_features(data)
        # f5, max 2nd differential of 
        data_features.append(max(np.diff(np.diff(data))))
        # f6, standard deviation of cgm values
        data_features.append(np.std(data))

        features.append(data_features)
    return features

def train_model(model_type_enumaration, training_data, training_labels, splits):
    model = None
    match model_type_enumaration:
        case 11:
            model = tree.DecisionTreeClassifier(criterion="entropy")
        case 12:
            model = tree.DecisionTreeClassifier(criterion="gini")
        case 21:
            model = svm.SVC(C=3)
        case 22: 
            model = svm.NuSVC()
        case _:
            model = svm.LinearSVC(C=100)

    kf = model_selection.KFold(n_splits=splits,shuffle=True,random_state=1)
    score_prediction = 0

    for i, (train_index, test_index) in enumerate(kf.split(training_data)):
        split_training_data = [training_data[i] for i in train_index]
        split_test_data = [training_data[i] for i in test_index]
        split_training_label = [training_labels[i] for i in train_index]
        split_test_label = [training_labels[i] for i in test_index]
        model.fit(split_training_data, split_training_label)
        score_prediction+=model.score(split_test_data, split_test_label)
    score_prediction/=(splits)
    return model, score_prediction

def main():
    cgm_data = read_and_transform_data('CGMData.csv', columns=['Date', 'Time', 'Sensor Glucose (mg/dL)'])
    insulin_data = read_and_transform_data('InsulinData.csv', columns=['Date', 'Time', 'BWZ Carb Input (grams)'])
    cgm_data2 = read_and_transform_data('CGM_patient2.csv', columns=['Date', 'Time', 'Sensor Glucose (mg/dL)'])
    insulin_data2 = read_and_transform_data('Insulin_patient2.csv', columns=['Date', 'Time', 'BWZ Carb Input (grams)'])

    insulin_data_meal_times = get_meal_times_from_insulin(insulin_data)
    insulin_data_meal_times2 = get_meal_times_from_insulin(insulin_data2)

    meal_training_data = extract_meal_data(insulin_data_meal_times, cgm_data)
    meal_training_data2 = extract_meal_data(insulin_data_meal_times2, cgm_data2)

    no_meal_training_data = extract_no_meal_data(insulin_data_meal_times, cgm_data)
    no_meal_training_data2 = extract_no_meal_data(insulin_data_meal_times2, cgm_data2)

    training_data_meal = extract_features(meal_training_data)
    training_data_meal2 = extract_features(meal_training_data2)
    training_data_no_meal = extract_features(no_meal_training_data)
    training_data_no_meal2 = extract_features(no_meal_training_data2)

    class_labels = [1 for x in range(len(training_data_meal)+len(training_data_meal2))]
    class_labels+= [0 for x in range(len(training_data_no_meal)+len(training_data_no_meal2))]
    training_data = training_data_meal+training_data_meal2+training_data_no_meal+training_data_no_meal2

    model, score = train_model(11, training_data, class_labels, 10)
    print(score)
    pickle.dump(model, open('model_file.sav', 'wb'))

if __name__ == '__main__':
    main()
