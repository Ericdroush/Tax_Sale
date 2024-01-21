# -*- coding: utf-8 -*-
"""
Created on Wed Jan 3 2024

Reads csv file with property details and bid amounts to try to predict bid prices

@author: ericd
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.metrics import mean_absolute_percentage_error
from sklearn.ensemble import RandomForestRegressor
from time import perf_counter


def get_type():
    type_dict = {
        'item': int,
        'taxmap': str,
        'account': str,
        'owner': str,
        'address': str,
        'subdiv': str,
        'tax_dist': str,
        'bldgs': float,
        'acres': float,
        'land_use': int,
        'bldg_type': str,
        'bedrooms': float,
        'sq_ft': float,
        'dpsf': float,
        'yr_built': str,
        'appraised_land': float,
        'appraised_bldg': float,
        'appraised_total': float,
        'bldg_ratio': float,
        'sale_price': float,
        'sale_date': str,
        'lake%': float,
        'bbox': str,
        'lat': float,
        'long': float,
        'dist1': str,
        'dist2': str,
        'dist3': str,
        'withdrawn': str,
        'county_link': str,
        'map_link': str,
        'amount_due': float,
        'comments': str,
        'rating': float,
        'bid': float,
        'max_int': float,
        'Actual': str,
        'Column1': float,
        'Column2': float,
        'Column3': float,
        'Bought': str,
    }
    return type_dict


def get_and_clean_data(verbose, flag='full'):
    props = pd.read_csv('gvl_temp.csv', dtype=get_type())
    if verbose:
        print('Number of properties read in:', len(props))

    # Remove the text values from Actual column - pandas will always treat mixed numbers and str as str
    props = props.loc[~props['Actual'].isin(['W', 'FLC'])]

    # Convert remaining values to numbers
    props['Actual'] = pd.to_numeric(props['Actual'])

    # Screen out properties without bids
    props = props.loc[props['Actual'] > 0]
    if verbose:
        print('Number of properties with recorded bids:', len(props), '\n')

    # Remove non-numeric columns
    if verbose:
        print('Column types filter - all "object" columns will be removed.')
        s = props.dtypes
        print(s[s == 'object'].index.tolist(), '\n')
    props = props.select_dtypes(exclude='object')

    # Remove columns that are *ALL* NaN
    if verbose:
        print('Columns with all NaN are True - will be removed')
        s = props.isnull().all()
        print(s[s == True].index.tolist(), '\n')  # to see which columns are going to be removed
    props.dropna(axis=1, how='all', inplace=True)

    # Remove columns that are *ANY* NaN
    if verbose:
        print('Columns with any NaN are True - will be removed')
        s = props.isnull().any()
        print(s[s == True].index.tolist(), '\n')  # to see which columns are going to be removed
    props.dropna(axis=1, how='any', inplace=True)

    # Manually remove columns
    to_remove = ['lat', 'long', 'bid', 'max_int', 'Column1', 'Column2', 'Column3']
    # to_remove.append('item')  # There could be some trend throughout the day
    # to_remove.append('sale_price')  # Should be a correlation, but the input is sketchy - lots of $10 properties
    # to_remove.append('amount_due')
    props.drop(columns=to_remove, inplace=True)
    if verbose:
        print('Manually removed columns')
        print(to_remove, '\n')

    if flag == 'land':
        props = props.loc[props['bldgs'] == 0]
        if verbose:
            print('Number of land only properties:', len(props), '\n')
    elif flag == 'houses':
        props = props.loc[props['bldgs'] > 0]
        if verbose:
            print('Number of house properties:', len(props), '\n')

    fit_cols = props.columns.tolist()
    if verbose:
        print('Remaining columns')
        print(fit_cols, '\n')

    return props, fit_cols


def runXGB(train_X, val_X, train_y, val_y, n_estimators=100, early_stopping_rounds=5, learning_rate=0.1, n_jobs=4, save=False):
    #t0 = perf_counter()

    model = XGBRegressor(n_estimators=n_estimators, learning_rate=learning_rate, n_jobs=n_jobs)
    model.fit(train_X, train_y) #, early_stopping_rounds=early_stopping_rounds, eval_set=[(val_X, val_y)], verbose=False)

    predictions = model.predict(val_X)

    if save:
        model.save_model('bid_predict_xgboost_model.txt')
    # Better optimization would be to try across multiple settings of the random_state parameter - maybe average the results? - started this in really_optimize
    #print(perf_counter() - t0)
    # return mean_absolute_percentage_error(predictions, val_y)
    return mean_absolute_error(predictions, val_y)


def XGBpredict(x_vals):
    model = XGBRegressor()
    model.load_model('bid_predict_xgboost_model.txt')
    return model.predict(x_vals)


def runRF(train_X, val_X, train_y, val_y, n_est=85, max_depth=14, max_leaf_nodes=340):
    model = RandomForestRegressor(n_estimators=n_est, max_depth=max_depth, max_leaf_nodes=max_leaf_nodes,
                                  random_state=1)
    model.fit(train_X, train_y)
    predictions = model.predict(val_X)
    return mean_absolute_error(predictions, val_y)


def optimize_rf(mae, train_X, val_X, train_y, val_y):
    n_est = 85
    max_depth = 14
    max_leaf_nodes = 340

    improvement = 2
    while improvement > 1:
        # Find optimal n_est
        val_range = range(30, 50)
        mae_vals = {n_est: runRF(train_X, val_X, train_y, val_y, n_est, max_depth, max_leaf_nodes) for n_est in val_range}
        opt_val = min(mae_vals, key=mae_vals.get)
        print('n_est', opt_val, mae_vals[opt_val])
        n_est = opt_val

        # Find optimal max_depth
        val_range = range(2, 15)
        mae_vals = {max_depth: runRF(train_X, val_X, train_y, val_y, n_est, max_depth, max_leaf_nodes) for max_depth in val_range}
        opt_val = min(mae_vals, key=mae_vals.get)
        print('max_depth', opt_val, mae_vals[opt_val])
        max_depth = opt_val

        # Find optimal max_leaf_nodes
        val_range = range(20, 100, 10)
        mae_vals = {max_leaf_nodes: runRF(train_X, val_X, train_y, val_y, n_est, max_depth, max_leaf_nodes) for max_leaf_nodes in val_range}
        opt_val = min(mae_vals, key=mae_vals.get)
        print('max_leaf_nodes', opt_val, mae_vals[opt_val])
        max_leaf_nodes = opt_val

        improvement = mae - mae_vals[opt_val]
        mae = mae_vals[opt_val]
        print('improvement', improvement, mae, '\n')


def optimize_xgb(train_X, val_X, train_y, val_y):
    n_estimators = 100
    learning_rate = 0.1

    mae = runXGB(train_X, val_X, train_y, val_y)

    improvement = 2
    #while improvement > 1:
    for i in range(4):
        # Find optimal n_estimators
        val_range = range(10, 100, 1)
        mae_vals = {n_estimators: runXGB(train_X, val_X, train_y, val_y, n_estimators=n_estimators,
                                         learning_rate=learning_rate) for n_estimators in val_range}
        opt_val = min(mae_vals, key=mae_vals.get)
        print('n_estimators', opt_val, mae_vals[opt_val])
        n_estimators = opt_val

        # Find optimal learning_rate
        val_range = [x/100 for x in range(1, 20)]
        mae_vals = {learning_rate: runXGB(train_X, val_X, train_y, val_y, n_estimators=n_estimators,
                                          learning_rate=learning_rate) for learning_rate in val_range}
        opt_val = min(mae_vals, key=mae_vals.get)
        print('learning_rate', opt_val, mae_vals[opt_val])
        learning_rate = opt_val

        improvement = mae - mae_vals[opt_val]
        mae = mae_vals[opt_val]
        print('improvement', improvement, mae, '\n')

    print(mae,n_estimators, learning_rate)
    return mae, n_estimators, learning_rate


def really_optimize_xgb():
    n_est_array = np.zeros(10)
    learn_array = np.zeros(10)
    mae_array = np.zeros(10)
    for i in range(10):
        train_X, val_X, train_y, val_y = train_test_split(props, y, random_state=i+1)
        print(i)
        mae_array[i], n_est_array[i], learn_array[i] = optimize_xgb(train_X, val_X, train_y, val_y)

    print('n_est', n_est_array, np.average(n_est_array))
    print('learn', learn_array, np.average(learn_array))
    print('mae', mae_array, np.average(mae_array))
    return


def predict_new(fit_cols):
    props_new = pd.read_csv('gvl_temp.csv', dtype=get_type())

    props_fit = props_new.copy()
    props_fit = props_fit[props_fit.columns.intersection(fit_cols)]
    props_fit.drop(columns='Actual', inplace=True)

    predict = XGBpredict(props_fit)
    props_new['Bid_predict'] = predict
    props_new.to_csv('gvl_temp_w_bid.csv', index=False, na_rep='NaN')
    return

props, fit_cols = get_and_clean_data(True, 'land')

y = props['Actual']
props.drop(columns='Actual', inplace=True)

train_X, val_X, train_y, val_y = train_test_split(props, y, random_state=1)

rf_mae = runRF(train_X, val_X, train_y, val_y)
print('Random Forest MAE:', rf_mae)

xgb_mae = runXGB(train_X, val_X, train_y, val_y, n_estimators=225, learning_rate=0.1)
print('XGBoost MAE:', xgb_mae)



# optimize_rf(rf_mae, train_X, val_X, train_y, val_y)
# mae, n_estimators, learning_rate = optimize_xgb(train_X, val_X, train_y, val_y)
# xgb_mae = runXGB(train_X, val_X, train_y, val_y, n_estimators=n_estimators, learning_rate=learning_rate, save=True)
# print('XGBoost MAE:', xgb_mae)
#
# predict_new(fit_cols)

#really_optimize_xgb()
