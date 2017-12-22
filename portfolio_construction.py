from cryptocurrency_vs_traditionalETF import *
import matplotlib.pyplot as plt
import scipy.optimize as sco

#Reference : https://s3-us-west-2.amazonaws.com/baczuk.com/Cryptocurrency+Return+Analysis.html
#Data Analysis to calculate the Return, Risk, and Correlation for each stock
def data_analysis(weights, data):
    rets = np.log(data / data.shift(-1))
    rf = 0.05  # risk free interest rate, constant
    weights = np.array(weights)
    annual_ret = np.sum(rets.mean() * weights) * 252
    annual_vol = np.sqrt(np.dot(weights.T, np.dot(rets.cov() * 252, weights)))
    return np.array([annual_ret, annual_vol, (annual_ret - rf) / annual_vol])

#Define onjection function for portfolio optimization
def objective_function(intial_weights, data, choice):
    if choice == 'Maximize Return':
        func = -data_analysis(intial_weights, data)[0]
    elif choice == 'Minimize Volatility':
        func = data_analysis(intial_weights, data)[1]
    elif choice == 'Maxmize Sharpe Ratio':
        func = -data_analysis(intial_weights, data)[2]
    return func

#calculate optimal weight for each stock
def optimal_weight(numTicker, data, choice):
    cons = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bnds = tuple((0, 1) for x in range(numTicker))
    intial_weights = numTicker * [1 / numTicker]
    statistics = sco.minimize(objective_function, intial_weights, args=(data, choice,), method='SLSQP', bounds=bnds,
                              constraints=cons)
    weights = statistics['x'].round(2)
    return weights

#statistics for the portfolio
def test(final_weight, data, choice):
    output = data_analysis(final_weight, data)
    print('If your goal is to {}'.format(choice),
          ', then your portfolio statistics is:\nannualized return = {}'.format(output[0].round(3)),
          '\nvolatilites = {}'.format(output[1].round(3)), '\nsharpe ratio = {}'.format(output[2].round(3)))

#portfolio growth visualization
def portfolio_growth_visualization(data, weights, choice):
    rets = np.log(data / data.shift(-1))
    value = rets * weights
    portRet = np.sum(value, axis=1)
    portRet = np.flip(portRet, 0)
    portRet = portRet.cumsum()
    portVal = 10000 * np.exp(portRet) #portfolio value started with $10000 initial investment

    #graph, portfolio growth
    portVal.plot(figsize=(8, 5))
    plt.title('Portfolio Growth Visualization, Type:{}'.format(choice))
    plt.xlabel('Time')
    plt.ylabel('Portfolio Value')

    plt.show()
    return portVal

#portfolio risk visualization(measured by 5% Value-at-Risk(VaR)
def value_at_risk_visualization(data,weights,choice):
    rets = np.log(data / data.shift(-1))
    value = rets * weights
    portRet = np.sum(value, axis=1)
    portRet = np.flip(portRet, 0)
    portRet = portRet.cumsum()
    portVal = 10000 * np.exp(portRet)
    portVal = pd.Series.to_frame(portVal)

    #graph, portfolio returns
    portVal.plot.hist()
    plt.title('Portfolio 5% Value-at-Risk Visualization, Type:{}'.format(choice))
    plt.xlabel('Daily Return')
    plt.ylabel('Frequency')
    plt.grid(True)
    plt.show()

    #calculate portfolio risk, the 5th percentile(VaR)
    p5 = np.percentile(portVal, 5)
    return p5


if __name__ == '__main__':
    '''--------------------------BITCOIN--------------------------'''
    btc_data = get_BTC_Data(datetime.strptime('2010-01-07', '%Y-%m-%d'), datetime.now())
    df_scatter(btc_data, 'BTC Historical Prices (USD)', seperate_y_axis=False, y_axis_label='Coin Value (USD)')  # , scale='log')
    # Plot the average BTC price
    btc_trace = go.Scatter(x=btc_data.index, y=btc_data['avg_btc_price_usd'])
    py.plot([btc_trace])

    '''--------------------------ALTCOIN--------------------------'''
    alt_coin_data = getAltCoinData(datetime.strptime('2015-01-01', '%Y-%m-%d'), datetime.now(), 86400)
    # Plot altcoin price
    df_scatter(alt_coin_data, 'Cryptocurrency Prices (USD)', seperate_y_axis=False, y_axis_label='Coin Value (USD)', scale='log')


    '''--------------------------CORRELATION--------------------------'''
    # 2016
    correlation_data_2016 = alt_coin_data[alt_coin_data.index.year == 2016]
    correlation_data_2016.pct_change().corr(method='pearson')
    correlation_heatmap(correlation_data_2016.pct_change(), "Cryptocurrency Correlation in 2016")  # Chart all of the altocoin prices

    # 2017
    correlation_data_2017 = alt_coin_data[alt_coin_data.index.year == 2017]
    correlation_data_2017.pct_change().corr(method='pearson')
    correlation_heatmap(correlation_data_2017.pct_change(), "Cryptocurrency Correlation in 2017")  # Chart all of the altocoin prices


    '''--------------------------ETF--------------------------'''
    '''Download ETF data from Yahoo Finance'''
    ticker = ['XLY', 'XLP', 'XLE', 'XLF', 'XLV', 'XLI', 'XLB', 'XLRE', 'XLK', 'XLU']
    start = datetime.strptime('2012-01-07', '%Y-%m-%d')
    end = datetime.strptime('2017-12-30', '%Y-%m-%d')

    etf_data = pd.DataFrame()
    #data['BTC'] = btc_data['avg_btc_price_usd']
    etf_data[ticker] = get_data(ticker, start, end)
    etf_data.colums = ticker
    # Plot the all ETF price
    #df_scatter(data, 'S&P 500 Component ETF Historical Prices (USD)', seperate_y_axis=False, y_axis_label='ETF Value (USD)')  # , scale='log')

    #Merge BTC to ETF price
    etf_data['BTC'] = btc_data['avg_btc_price_usd']


    '''--------------------------Correlation between Bitcoin and traditional ETFs--------------------------'''
    # Calculate correlation coefficients, 2016
    correlation_data = etf_data[etf_data.index.year == 2016]
    correlation_data.pct_change().corr(method='pearson')
    correlation_heatmap(correlation_data.pct_change(), "Bitcoin and ETF Correlation in 2016")

    # Calculate correlation coefficients, 2017
    correlation_data = etf_data[etf_data.index.year == 2017]
    correlation_data.pct_change().corr(method='pearson')
    correlation_heatmap(correlation_data.pct_change(), "Bitcoin and ETF Correlation in 2017")


    '''--------------------------Portfolio Construction--------------------------'''
    #ticker = ['XLY', 'XLP', 'XLE', 'XLF', 'XLV', 'XLI', 'XLB', 'XLRE', 'XLK', 'XLU']
    ticker = ['XLY', 'XLP', 'XLE', 'XLF', 'XLV', 'XLI', 'XLB', 'XLRE', 'XLK', 'XLU', 'BTC']
    numTicker = len(ticker)
    data = etf_data

    # max return
    choice = 'Maximize Return'
    final_weight = optimal_weight(numTicker, data, choice)
    dict_weights = dict(zip(ticker, final_weight))
    print('----------Optimal weights if your goal is to {}'.format(choice), '---------')
    print(dict_weights)
    print('\nIn sample test results--->')
    test_result = test(final_weight, data, choice)
    portfolio_growth_visualization(data, final_weight, choice)
    var5 = value_at_risk_visualization(data,final_weight,choice) #calculate 5% Value at Risk(VaR)
    print('\nThe 5% VaR is --->')
    print(var5)

    # min volatility
    choice = 'Minimize Volatility'
    final_weight = optimal_weight(numTicker, data, choice)
    dict_weights = dict(zip(ticker, final_weight))
    print('----------Optimal weights if your goal is to {}'.format(choice), '---------')
    print(dict_weights)
    print('\nIn sample test results--->')
    test_result = test(final_weight, data, choice)
    portfolio_growth_visualization(data, final_weight, choice)
    var5 = value_at_risk_visualization(data,final_weight,choice) #calculate 5% Value at Risk(VaR)
    print('\nThe 5% VaR is --->')
    print(var5)

    # max sharpe ratio
    choice = 'Maxmize Sharpe Ratio'
    final_weight = optimal_weight(numTicker, data, choice)
    dict_weights = dict(zip(ticker, final_weight))
    print('----------Optimal weights if your goal is to {}'.format(choice), '---------')
    print(dict_weights)
    print('\nIn sample test results--->')
    test_result = test(final_weight, data, choice)
    portfolio_growth_visualization(data, final_weight, choice)
    var5 = value_at_risk_visualization(data,final_weight,choice) #calculate 5% Value at Risk(VaR)
    print('\nThe 5% VaR is --->')
    print(var5)