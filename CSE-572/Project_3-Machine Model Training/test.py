import pandas as pd
from train import extract_features
import pickle

def read_test_data(test_file):
    test_data = pd.read_csv(test_file, header=None)
    test_data = test_data.transpose()
    extracted_test_data = []
    for series_name, series in test_data.items():
        extracted_test_data.append(series.to_list())
    return extracted_test_data



def main():

    test_data = read_test_data('test.csv')
    test_data = extract_features(test_data)

    model = pickle.load(open('model_file.sav', 'rb'))
   
    results = model.predict(test_data).tolist()

    pd.DataFrame(results).to_csv("Result.csv", index=False, header=False)

    

if __name__ == '__main__':
    main()