import pandas as pd
import scipy as scipy

def read_raw_data(csv_file, columns):
    return pd.read_csv(csv_file, usecols=columns)

def thresholding_on_key(df, lambda_fn_checkers, key):
    for k, v in lambda_fn_checkers.items():
        df[k] = df[key].apply(v)
    return df

def extract_metrics(df, date_time_col):
    metrics = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    by_day_cgm_manual = df.groupby(pd.Grouper(key=date_time_col, freq='D'))

    time_ranges = [
        ("00:00:00", "06:00:00"),
        ("06:00:00", "23:59:59"),
        ("00:00:00", "23:59:59")
    ]

    cgm_ranges = [
        "hyperglycemia",
        "hyperglycemia_critical",
        "in_range",
        "in_range_secondary",
        "hypoglycemia_1",
        "hypoglycemia_2"
        ]

    i=0
    #iterating from night, daytime, then whole day for result format
    for (start_time, end_time) in time_ranges:
        start_time = pd.to_datetime(start_time).time()
        end_time = pd.to_datetime(end_time).time()
        for k in cgm_ranges:
            metrics[i] = round((by_day_cgm_manual.apply(lambda x: x[(x['Time']>=start_time)&(x['Time']<=end_time)][k].sum(), include_groups=False)/288).mean().item()*100, 4)
            i+=1
    return metrics


def main():
    cgm_data = read_raw_data('CGMData.csv', ['Date', 'Time', 'Sensor Glucose (mg/dL)'])
    insulin_data = read_raw_data('InsulinData.csv', ['Date', 'Time', 'Alarm'])


    # Data manipulation to convert Date and Time columns into Date_Time column
    cgm_data['Date_Time'] = pd.to_datetime(cgm_data['Date']+" "+cgm_data['Time'])
    cgm_data.drop(columns=['Date', 'Time'], inplace=True)

    insulin_data['Date_Time'] = pd.to_datetime(insulin_data['Date']+" "+insulin_data['Time'])
    insulin_data.drop(columns=['Date', 'Time'], inplace=True)

    # Time column for day segmentation into overnight and daytime
    time = cgm_data['Date_Time'].dt.time
    cgm_data['Time'] = time

    # Drop na values
    cgm_data.dropna()
    
    # Addition of conditional count columns (values 1 or 0) to indicate cgm range
    cgm_ranges_lamda_fns = {
        "hyperglycemia": lambda x: 1 if x>180 else 0,
        "hyperglycemia_critical": lambda x: 1 if x>250 else 0,
        "in_range": lambda x: 1 if 70<=x<=180 else 0,
        "in_range_secondary": lambda x: 1 if 70<=x<=150 else 0,
        "hypoglycemia_1": lambda x: 1 if x<70 else 0,
        "hypoglycemia_2": lambda x: 1 if x<54 else 0
        }
    
    cgm_data = thresholding_on_key(cgm_data, cgm_ranges_lamda_fns, 'Sensor Glucose (mg/dL)')
    
    # Extraction of earliest date where switch to AUTO MODE ACTIVE PLGM OFF occurs
    insulin_data = insulin_data[insulin_data['Alarm'] == "AUTO MODE ACTIVE PLGM OFF"]
    auto_switch_date = insulin_data['Date_Time'].min()

    # Dividing cgm dataset into two based on switch date
    cgm_manual = cgm_data[cgm_data['Date_Time']<auto_switch_date].copy()
    cgm_auto = cgm_data[cgm_data['Date_Time']>=auto_switch_date].copy()

    # Metric extraction (% time in 1-0 format instead of 100-0)
    cgm_manual_metrics = extract_metrics(cgm_manual, 'Date_Time')
    cgm_auto_metrics = extract_metrics(cgm_auto, 'Date_Time')

    # final output
    results_df = pd.DataFrame(
        [cgm_manual_metrics, cgm_auto_metrics], index=['Manual mode', 'Auto mode']
    )
    result_vals = results_df.values

    # Output the results to a CSV file
    pd.DataFrame(result_vals).to_csv("Result.csv", index=False, header=False)


if __name__ == '__main__':
    main()










