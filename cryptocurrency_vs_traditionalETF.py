from cryptocurrency import *
import pandas_datareader.data as web


'''--------------------------ETF--------------------------'''
'''Download ETF Price from Yahoo Finance'''

def get_data(ticker, start, end):
    cache_path = '{}.pkl'.format(ticker).replace('/','-')
    try:
        f = open(cache_path, 'rb')
        df = pickle.load(f)
        print('Loaded {} from cache'.format(ticker))
    except (OSError, IOError) as e:
        print('Downloading {} from Quandl'.format(ticker))
        df = web.DataReader(ticker, 'yahoo', start, end)['Adj Close']
        df.to_pickle(cache_path)
        print('Cached {} at {}'.format(ticker, cache_path))
    return df


