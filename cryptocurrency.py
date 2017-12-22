import numpy as np
import pandas as pd
import pickle
import quandl
from datetime import datetime
import plotly.offline as py
import plotly.graph_objs as go
import time


'''--------------------------BITCOIN--------------------------'''
'''Download Bitcoin Price from Quandl'''
def get_quandl_data(quandl_id, start, end):
    cache_path = '{}.pkl'.format(quandl_id).replace('/','-')
    try:
        f = open(cache_path, 'rb')
        df = pickle.load(f)
        print('Loaded {} from cache'.format(quandl_id))
    except (OSError, IOError) as e:
        print('Downloading {} from Quandl'.format(quandl_id))
        df = quandl.get(quandl_id, start_date=start, end_date=end, returns="pandas")
        df.to_pickle(cache_path)
        print('Cached {} at {}'.format(quandl_id, cache_path))
    return df


'''Merge a single column of each dataframe into a new combined dataframe'''
'''Only Weighted Avg Price is Needed'''
def merge_dfs(dataframes, labels, col):
    series_dict={}
    for index in range(len(dataframes)):
        series_dict[labels[index]]=dataframes[index][col]
    return pd.DataFrame(series_dict)


'''Visualize The Pricing Series'''
'''Generate a scatter plot of the entire dataframe'''
def df_scatter(df, title, seperate_y_axis=False, y_axis_label='', scale='linear', initial_hide=False):
    label_arr = list(df)
    series_arr = list(map(lambda col: df[col], label_arr))

    layout = go.Layout(
        title=title,
        legend=dict(orientation="h"),
        xaxis=dict(type='date'),
        yaxis=dict(
            title=y_axis_label,
            showticklabels=not seperate_y_axis,
            type=scale
        )
    )

    y_axis_config = dict(
        overlaying='y',
        showticklabels=False,
        type=scale)

    visibility = 'visible'
    if initial_hide:
        visibility = 'legendonly'

    # Form Trace For Each Series
    trace_arr = []
    for index, series in enumerate(series_arr):
        trace = go.Scatter(
            x=series.index,
            y=series,
            name=label_arr[index],
            visible=visibility
        )

        # Add seperate axis for the series
        if seperate_y_axis:
            trace['yaxis'] = 'y{}'.format(index + 1)
            layout['yaxis{}'.format(index + 1)] = y_axis_config
        trace_arr.append(trace)

    fig = go.Figure(data=trace_arr, layout=layout)
    py.plot(fig)

'''Pull pricing data for multiple BTC exchanges'''
def get_BTC_Data(start, end):
    # Pull pricing data for multiple BTC exchanges
    exchanges = ['KRAKEN','COINBASE','BITSTAMP','ITBIT']# Exchange names
    exchange_data = {}
    for exchange in exchanges:
        exchange_code = 'BCHARTS/{}USD'.format(exchange)
        btc_exchange_df = get_quandl_data(exchange_code, start, end)
        exchange_data[exchange] = btc_exchange_df
    # Merge the BTC price dataseries' into a single dataframe
    btc_usd_datasets = merge_dfs(list(exchange_data.values()), list(exchange_data.keys()), 'Weighted Price')
    # Remove "0" values
    btc_usd_datasets.replace(0, np.nan, inplace=True)
    # Calculate the average BTC price as a new column
    btc_usd_datasets['avg_btc_price_usd'] = btc_usd_datasets.mean(axis=1)
    return btc_usd_datasets

'''--------------------------ALTCOIN--------------------------'''
'''Download and cache Altcoin Data'''
def get_json_data(json_url, cache_path):
    try:
        f = open(cache_path, 'rb')
        df = pickle.load(f)
        print('Loaded {} from cache'.format(json_url))
    except (OSError, IOError) as e:
        print('Downloading {}'.format(json_url))
        df = pd.read_json(json_url)
        df.to_pickle(cache_path)
        print('Cached {} at {}'.format(json_url, cache_path))
    return df

def get_crypto_data(poloniex_pair, start_date, end_date, period):
    '''Retrieve cryptocurrency data from poloniex'''
    base_polo_url = 'https://poloniex.com/public?command=returnChartData&currencyPair={}&start={}&end={}&period={}'
    json_url = base_polo_url.format(poloniex_pair, time.mktime(start_date.timetuple()), time.mktime(end_date.timetuple()), period)
    data_df = get_json_data(json_url, poloniex_pair + '_' + start_date.strftime('%m-%d-%Y') + '_' + end_date.strftime('%m-%d-%Y'))
    data_df = data_df.set_index('date')
    return data_df

def getAltCoinData(start_date, end_date, period):
    altcoin_data = {}
    # Get BTC
    btc_data = get_crypto_data('USDT_BTC', start_date, end_date, period)
    btc_data['price_usd'] = btc_data['weightedAverage']
    altcoins = ['ETH', 'LTC', 'XRP', 'ETC', 'STR', 'DASH', 'SC', 'XMR', 'XEM']
    for altcoin in altcoins:
        coinpair = 'BTC_{}'.format(altcoin)
        crypto_price_df = get_crypto_data(coinpair, start_date, end_date, period)
        altcoin_data[altcoin] = crypto_price_df

    # Calculate USD Price as a new column in each altcoin dataframe
    for altcoin in altcoin_data.keys():
        altcoin_data[altcoin]['price_usd'] =  altcoin_data[altcoin]['weightedAverage'] * btc_data['weightedAverage']

    # Add BTC
    altcoin_data['BTC'] = btc_data
    # Merge USD price of each altcoin into single dataframe
    combined_altcoin_data = merge_dfs(list(altcoin_data.values()), list(altcoin_data.keys()), 'price_usd')
    # Columns: Date close, high, low, open, quoteVolume, Volume, weightedAverage
    return combined_altcoin_data

'''--------------------------CORRELATION--------------------------'''
'''Visualize Correlation'''
def correlation_heatmap(df, title, absolute_bounds=True):
    heatmap = go.Heatmap(
        z=df.corr(method='pearson').as_matrix(),
        x=df.columns,
        y=df.columns,
        colorbar=dict(title='Pearson Coefficient'),
    )

    layout = go.Layout(title=title)

    if absolute_bounds:
        heatmap['zmax'] = 1.0
        heatmap['zmin'] = -1.0

    fig = go.Figure(data=[heatmap], layout=layout)
    py.plot(fig)

