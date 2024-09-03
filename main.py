import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import lib_logic as lib_lgc
import lib_data
import sys
import inquirer  
import main_rebal_rebal
from lib_const import pool_info_list

# print("If you don't have data downloadeded and put as CSV in output folder, please run lib_data.py first!")
# print("Set load_all_pool_related_data and load_price_related_data = True before run ")
def get_df_daily_fees(pool_address, date_begin = "2009-01-01", date_end = "3000-01-01"):
 
    df = lib_data.get_uniswap_pool_data_csv(pool_address, date_begin, date_end )

    df['daily_fee_rate'] = df['feesUSD'] / df['tvlUSD']
    df['date_i'] = df['date']
    df.set_index('date_i', inplace=True)
    return df[[ 'feesUSD', 'tvlUSD', 'daily_fee_rate']] # 'date',

def get_df_daily_price(pool_address, date_begin = '2021-03-01', date_end ="3000-01-01"):

    # Load the CSV file
    df =  lib_data.get_crypto_price_data_csv(pool_address, date_begin, date_end)
    
    for pool_info in pool_info_list:
        if pool_info[0] == pool_address:
            token0 = pool_info[1]
            token1 = pool_info[2]
            break
            
    # Filter rows related to ETH price in terms of BTC
    df = df[df['token0_symbol'] == token0] 
    df = df[df['token1_symbol'] == token1]
    df["YYYYMM"] = df.index.strftime('%Y%m')
    df = add_monthly_price_change(df)
    
    df = df[~df.index.duplicated(keep='last')] # Remove duplicates by taking the last value for each date
    return df

def add_monthly_price_change(df):
    # Group by 'Token' and the month of the 'date' column
    grouped = df.groupby(['YYYYMM'])
    
    if 'date' not in df.columns:
        df['date'] = df.index
    
    # Calculate the first date and close price of each month for each group
    df['month_begin_date'] = grouped['date'].transform('min')
    df['month_last_date'] = grouped['date'].transform('max')
    
    df['price_month_begin_date'] = grouped['price'].transform('first')
    df['price_month_end_date'] = grouped['price'].transform('last')
    df['Price_chg_vs_MM01'] = df['price'] / df['price_month_begin_date'] -1
    return df

def get_df_comb_price_fee(df_price, df_fee):

    df = pd.merge(df_price, df_fee, left_index=True, right_index=True)
    # df = add_monthly_price_change(df)
    # df.drop(df[ df['month_last_date'].dt.day < 21 ].index, inplace=True) # filter out months with data < 3 weeks
    return df

def get_performance_by_range(range_down, df, rebalance_period='M', benchmark_down=-0.3):
    if rebalance_period == "M":
        df_mon_chg = df[[ 'YYYYMM', 'Price_chg_vs_MM01']][df['month_last_date'] == df['date']]
        df_mon_chg.dropna(inplace=True)

        df_mon_day_ret = df[['YYYYMM',  'Price_chg_vs_MM01','daily_fee_rate' ]][df['month_begin_date'] != df['date']]

        lower_bound = range_down
        benchmark_lower = benchmark_down
        upper_bound = lib_lgc.get_opposite_bin_limit_with_same_liquidity(lower_bound)

        ret_columns = ['YYYYMM', 'range_down', 'mon_total_price_chg', 'mon_total_fee_yield', 'coverage_rate', 'boost_factor', 'gross_return', 'imp_loss',  'net_return']

        boost_factor = lib_lgc.get_liquidity_boost_given_range(prince_range=lower_bound, benchmark=benchmark_lower)
        
        result_mon = np.empty((len(df_mon_chg), len(ret_columns)))

        for mon_i in range(len(df_mon_chg)):
                yyyymm = df_mon_chg['YYYYMM'].iloc[mon_i]

                mon_total_price_chg = df_mon_chg['Price_chg_vs_MM01'].iloc[mon_i]
                
                df_yyyymm =  df_mon_day_ret[df_mon_day_ret['YYYYMM'] == yyyymm]

                mon_total_observ = len(df_yyyymm)
                mon_within_range =df_yyyymm['Price_chg_vs_MM01'].between(lower_bound, upper_bound).sum()
                
                coverage_rate= (mon_within_range / mon_total_observ)

                mon_total_fee_yield = df_yyyymm['daily_fee_rate'].sum()

                gross_return = mon_total_fee_yield*coverage_rate*boost_factor

                imp_loss = lib_lgc.get_impermanent_loss_given_range(mon_total_price_chg, lower_bound)

                net_return = (1+gross_return)*(1+imp_loss) -1

                result_mon[mon_i, :] =np.array([int(yyyymm),lower_bound,mon_total_price_chg, mon_total_fee_yield,coverage_rate, boost_factor,gross_return, imp_loss, net_return ])

        df_mon_result = pd.DataFrame(data=result_mon, columns=ret_columns)
        return df_mon_result
    # Grouping data by rebalancing period
    elif rebalance_period == "W": 
        df['Week'] = df['date'].dt.to_period('W')
    
        # Filter for the last day of each week
        df_week_chg = df[df['date'] == df.groupby('Week')['date'].transform('max')]

        # Extract daily returns excluding the first day of each week
        df_week_day_ret = df[['Week', 'Price_chg_vs_MM01', 'daily_fee_rate']][df.groupby('Week')['date'].transform('min') != df['date']]

        lower_bound = range_down
        benchmark_lower = benchmark_down
        upper_bound = lib_lgc.get_opposite_bin_limit_with_same_liquidity(lower_bound)

        ret_columns = ['Week', 'range_down', 'week_total_price_chg', 'week_total_fee_yield', 'coverage_rate', 'boost_factor', 'gross_return', 'imp_loss', 'net_return']

        boost_factor = lib_lgc.get_liquidity_boost_given_range(prince_range=lower_bound, benchmark=benchmark_lower)
        
        result_week = np.empty((len(df_week_chg), len(ret_columns)))

        for week_i in range(len(df_week_chg)):
            week_period = df_week_chg['Week'].iloc[week_i].start_time.timestamp()  # Convert to Unix timestamp (float)

            week_total_price_chg = df_week_chg['Price_chg_vs_MM01'].iloc[week_i]
            
            df_week_period = df_week_day_ret[df_week_day_ret['Week'] == df_week_chg['Week'].iloc[week_i]]
            
            week_total_observ = len(df_week_period)
            week_within_range = df_week_period['Price_chg_vs_MM01'].between(lower_bound, upper_bound).sum()
            
            coverage_rate = week_within_range / week_total_observ
            week_total_fee_yield = df_week_period['daily_fee_rate'].sum()
            gross_return = week_total_fee_yield * coverage_rate * boost_factor
            imp_loss = lib_lgc.get_impermanent_loss_given_range(week_total_price_chg, lower_bound)
            net_return = (1 + gross_return) * (1 + imp_loss) - 1

            result_week[week_i, :] = np.array([week_period, lower_bound, week_total_price_chg, week_total_fee_yield, coverage_rate, boost_factor, gross_return, imp_loss, net_return])

        df_week_result = pd.DataFrame(data=result_week, columns=ret_columns)
        return df_week_result

    else :    
        df_daily_chg = df[['date', 'Price_chg_vs_MM01']][df['date'] == df['date']]
        df_daily_chg.dropna(inplace=True)

        # Daily return calculations
        df_daily_ret = df[['date', 'Price_chg_vs_MM01', 'daily_fee_rate']][df['date'] == df['date']]

        lower_bound = range_down
        benchmark_lower = benchmark_down
        upper_bound = lib_lgc.get_opposite_bin_limit_with_same_liquidity(lower_bound)

        ret_columns = ['date', 'range_down', 'daily_total_price_chg', 'daily_total_fee_yield', 
                    'coverage_rate', 'boost_factor', 'gross_return', 'imp_loss', 'net_return']

        # Get liquidity boost factor
        boost_factor = lib_lgc.get_liquidity_boost_given_range(prince_range=lower_bound, benchmark=benchmark_lower)

        result_daily = np.empty((len(df_daily_chg), len(ret_columns)), dtype=object)  # Change to object dtype

        for daily_i in range(len(df_daily_chg)):
            date = df_daily_chg['date'].iloc[daily_i]

            daily_total_price_chg = df_daily_chg['Price_chg_vs_MM01'].iloc[daily_i]
            df_date = df_daily_ret[df_daily_ret['date'] == date]

            if df_date.empty:
                print("No data for the date:", date)
                continue

            daily_total_observ = len(df_date)
            daily_within_range = df_date['Price_chg_vs_MM01'].between(lower_bound, upper_bound).sum()
            coverage_rate = (daily_within_range / daily_total_observ) if daily_total_observ > 0 else 0
            daily_total_fee_yield = df_date['daily_fee_rate'].sum()

            gross_return = daily_total_fee_yield * coverage_rate * boost_factor
            imp_loss = lib_lgc.get_impermanent_loss_given_range(daily_total_price_chg, lower_bound)
            net_return = (1 + gross_return) * (1 + imp_loss) - 1

            result_daily[daily_i, :] = np.array([
                date, lower_bound, daily_total_price_chg, daily_total_fee_yield,
                coverage_rate, boost_factor, gross_return, imp_loss, net_return
            ])

        df_daily_result = pd.DataFrame(data=result_daily, columns=ret_columns)
        return df_daily_result


def get_full_range_performance(range_down, df, rebalance_period = "M", benchmark_range =-0.3):
    array_range_rst = np.empty((len(range_down),4))
    for range_i in range(len(range_down)):
            range_down_i = range_down[range_i]
            df_i = get_performance_by_range(range_down_i, df, rebalance_period, benchmark_down=benchmark_range)
            average_gross_return = df_i['gross_return'].median() #.mean()
            average_imp_loss = df_i['imp_loss'].median() #mean()
            average_net_return = df_i['net_return'].median() #.mean()
            array_range_rst[range_i, :] = np.array([range_down_i, average_gross_return,average_imp_loss,average_net_return ])

    ret_columns = ['range_limit_down', 'gross_fee_gain', 'imp_loss', 'net_gain']
    len(ret_columns)
    df_result = pd.DataFrame(data=array_range_rst, columns=ret_columns)

    return df_result



def show_simulation_result(df_result, x_column, y_cols_name, main_y_col_name, y_annualise_factor = 12):
      
    # multiply with 12 convert from monthly to be yearly
    df_result[y_cols_name] = df_result[y_cols_name] * y_annualise_factor

    # Plotting the data
    for y_column in y_cols_name:
        plt.plot(df_result[x_column], df_result[y_column], marker='o', label=y_column)

    # Adding labels and a title
    plt.xlabel("LP range limit (down part)")
    plt.ylabel('value')
    plt.title('LP yield from WBTC/ETH pool against range')

    # Adding a legend
    plt.legend()
    plt.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
    plt.minorticks_on()
    plt.grid(which='minor', linestyle=':', linewidth=0.5, alpha=0.5)
    plt.show()

    # plt.plot(df_result[x_column], df_result[main_y_col_name], marker='o', label=y_column)
    # plt.show()





def main ():
    date_begin = '2022-12-01'
    date_end = '2023-11-30'
    range_down = np.arange(-0.5, 0, 0.02)
    benchmark_range = -0.3

    questions = [
        inquirer.List('option',
            message="Choose one",
            choices=['WETH/USDT', 'USDC/WETH' , 'WBTC/WETH', 'DAI/USDC', 'WSTETH/WETH', 'USDC/USDT'],
        ),
    ]
    answers = inquirer.prompt(questions)
    pool = main_rebal_rebal.pool_address(answers['option'])
    
    questions = [
        inquirer.List('option',
            message="Choose Rebalancing Frequency(days)",
            choices=["Day", "Week", "Month"],
        )
    ]

    answers = inquirer.prompt(questions)
    rebalance_period = answers['option']
    
    df_price = get_df_daily_price(pool, date_begin,date_end=date_end)
    print(df_price.head())
    df_fee = get_df_daily_fees(pool, date_begin = date_begin, date_end=date_end)
    df = get_df_comb_price_fee(df_price, df_fee)
    print("\n check df")
    print(df.head())
    if rebalance_period == "Day":
        rebalance_period = "D"
    elif rebalance_period == "Week":
        rebalance_period = "W"
    elif rebalance_period == "Month":
        rebalance_period = "M"
    df_result = get_full_range_performance(range_down, df, rebalance_period, benchmark_range)
    result_file_name = 'output/eth_btc_lp_range_result_v3.csv' 
    df_result.to_csv(result_file_name, index=False)
    print("result saved to ", result_file_name)

    y_cols_name = ['gross_fee_gain', 'imp_loss', 'net_gain']
    x_column = 'range_limit_down'
    main_y_col_name = 'net_gain'

    print("show net_yield, gross_yield, and imp loss chart.")
    print("Close the chart to end program.")
    show_simulation_result(df_result, x_column, y_cols_name,main_y_col_name, y_annualise_factor=12 )
    
    
if __name__ == "__main__" :
    main()