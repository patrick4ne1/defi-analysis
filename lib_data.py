import requests
from datetime import datetime, timedelta
import pandas as pd
import lib_const
import ast
from web3 import Web3
import os
import sys
import json

import hypersync
from hypersync import (
    LogSelection,
    LogField,
    DataType,
    FieldSelection,
    ColumnMapping,
    TransactionField,
)
import asyncio

infura_eth_url = 'https://mainnet.infura.io/v3/7b3313791d464b1b8822f333e9a13476'
infura_polygon_url = 'https://polygon-mainnet.infura.io/v3/7b3313791d464b1b8822f333e9a13476'
web3_eth = Web3(Web3.HTTPProvider(infura_eth_url))
web3_polygon = Web3(Web3.HTTPProvider(infura_polygon_url))

# Check if connected to Ethereum
if not web3_eth.isConnected():
    print("Failed to connect to the Ethereum network")
    exit()
    
def get_crypto_price_data_csv(pool_address, date_begin=datetime(2000, 1,1), date_end=datetime(3000,1,1)):
    
    file_name = lib_const.get_pool_filename(pool_address)
    
    if os.path.exists(file_name):
        df=pd.read_csv(file_name)
    else:
        print("The historical data does not exist.")
        print("Please run lib_data.py first!")
        sys.exit(0)
    
    df['date'] = pd.to_datetime(df['date'], unit='s')
    if(isinstance(date_begin, str)) :
        date_begin = datetime.strptime(date_begin, "%Y-%m-%d")
    if(isinstance(date_end, str)) :
        date_end = datetime.strptime(date_end, "%Y-%m-%d")
        
    df = df[df['date'] >= date_begin]
    df = df[df['date'] <= date_end]
    
    df.set_index('date', inplace=True)
    df['price'] = df['token0Price']
    def extract_token0_symbols(pool_str):
        pool_dict = ast.literal_eval(pool_str)
        token0_symbol = pool_dict['token0']['symbol']
        return token0_symbol
    
    def extract_token1_symbols(pool_str):
        pool_dict = ast.literal_eval(pool_str)
        token1_symbol = pool_dict['token1']['symbol']
        return token1_symbol
    # Apply the function to extract token symbols
    df['token0_symbol'] = df['pool'].apply(extract_token0_symbols)
    df['token1_symbol'] = df['pool'].apply(extract_token1_symbols)
    return df

# API each time can only get 100 recoreds, hence break down the retrieve into year-month
def get_uniswap_v3_data_limit100(pool_address, from_timestamp, to_timestamp):
    # Uniswap V3 Subgraph endpoint
    endpoint = 'https://gateway.thegraph.com/api/8b29398e34a33f4bcd32fa6b3f7c9835/subgraphs/id/5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV'

    # GraphQL query to get historical data
    query = '''{
    poolDayDatas( orderBy: date, 
    where: { pool: "%s", 
      date_gte: %d } ) {
        date
        liquidity
        sqrtPrice
        token0Price
        token1Price
        volumeToken0
        volumeToken1
        feesUSD
      	volumeUSD
      	tvlUSD
        pool {
          token0 {
            symbol
          }
        token1 {
            symbol
          }
        }
    }
    }

    ''' % (pool_address, from_timestamp)
    
    # Make the GraphQL request
    response = requests.post(endpoint, json={'query': query})
    data = response.json()
    print(data)
    
    return data['data']['poolDayDatas']

def get_block_number_from_date(target_date):
    # Convert target date to timestamp
    target_timestamp = int(target_date.timestamp())

    # Start from the latest block
    latest_block = web3_polygon.eth.block_number
    for block_number in range(latest_block, 0, -1):
        block = web3_polygon.eth.getBlock(block_number)
        
        # Check if block timestamp matches the target timestamp
        if block.timestamp <= target_timestamp:
            return block_number

    return None

async def collect_events():
    client = hypersync.HypersyncClient(
        hypersync.ClientConfig(
            url="https://arbitrum.hypersync.xyz",
            # use secret bearer token for access
            # See https://docs.envio.dev/docs/HyperSync/api-tokens
            bearer_token="bf67d0dc-ca85-4631-828a-73b4ce787611",
        )
    )
    from_date = datetime.strptime('2019-01-01 12:00:00', '%Y-%m-%d %H:%M:%S')
    block_number = get_block_number_from_date(from_date)
    query = hypersync.Query(
        from_block=block_number,
        logs=[
            LogSelection(
                address=[
                    "0x2f5e87C9312fa29aed5c179E456625D79015299c"
                ],  # uniswap factory
                topics=[
                    [
                        "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
                    ]
                ],  # PoolCreated log
            )
        ],
        field_selection=FieldSelection(
            log=[
                LogField.TOPIC0,
                LogField.TOPIC1,
                LogField.TOPIC2,
                LogField.DATA,
                LogField.TRANSACTION_HASH,
            ],
            transaction=[
                TransactionField.BLOCK_NUMBER,
            ],
        ),
    )

    config = hypersync.StreamConfig(
        hex_output=hypersync.HexOutput.PREFIXED,
        event_signature="Swap (address sender, address recipient, int256 amount0, int256 amount1, uint160 sqrtPriceX96, uint128 liquidity, int24 tick)",
    )

    await client.collect_parquet("data", query, config)

def last_day_of_month(year, month):
    # Calculate the first day of the next month
    first_day_of_next_month = datetime(year, month, 1) + timedelta(days=32)

    # Subtract one day to get the last day of the current month
    last_day_of_month = first_day_of_next_month.replace(day=1) - timedelta(days=1)

    return last_day_of_month


def download_uniswap_v3_data_year(pool_address, years):
    pool_df=pd.DataFrame()

    # Get Uniswap V3 data
    for year in years:
        for month in range(1, 13):
            
            from_timestamp = int(datetime(year, month, 1).timestamp())  # Replace with your start date
            next_mon_first_day = last_day_of_month(year, month)+ timedelta(days=1)
            to_timestamp = int(next_mon_first_day.timestamp())
            uniswap_v3_data_month = get_uniswap_v3_data_limit100(pool_address, from_timestamp, to_timestamp)
            df = pd.DataFrame(uniswap_v3_data_month)
            pool_df = pd.concat([pool_df, df], ignore_index=True)
            
    return pool_df    

def get_uniswap_pool_data_csv(pool_address, date_begin=datetime(2000, 1,1), date_end=datetime(3000,1,1)):
    data_file_name = lib_const.get_pool_filename(pool_address)
    df = pd.read_csv(data_file_name)
    
    if(isinstance(date_begin, str)) :
        date_begin = datetime.strptime(date_begin, "%Y-%m-%d")
    if(isinstance(date_end, str)) :
        date_end = datetime.strptime(date_end, "%Y-%m-%d")
    
    df['date'] = pd.to_datetime(df['date'], unit='s')
    df = df[(df['date'] >= date_begin) & (df['date'] <= date_end)]
    df = df.sort_values(by='date',ascending=False)   
    return df


def download_crypto_price(symbol, token, start_date, end_date, vs_currency='usd'):
    url = f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart"
    params = {
        'vs_currency': vs_currency,
        'from': int(start_date.timestamp()),
        'to': int(end_date.timestamp()),
        'interval': 'daily',
        'days': 1200
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        prices = data.get('prices', [])
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None
    
    columns = ['date', 'price']
    df = pd.DataFrame(prices, columns=columns) 
    df.drop(df.index[-1], inplace=True) # last date has 2 records
    
    df['date'] = df['date'].apply( lambda x: datetime.utcfromtimestamp(x / 1000).date()   )
    df['token'] = token
    df['vs_currency'] = vs_currency
    
    return df
    




# Check if the script is being run as the main program
if __name__ == "__main__":
    
    import lib_const
    load_all_pool_related_data = True
    if load_all_pool_related_data: # getting pool fee/vol related data
        
        years = [2021, 2022, 2023, 2024]
        
        result_df = pd.DataFrame()
        for pool_info in lib_const.pool_info_list:
            pool_address = pool_info[0]
            result_df = download_uniswap_v3_data_year(pool_address, years)
            file_name = lib_const.get_pool_filename(pool_address, token0=pool_info[1], token1=pool_info[2])
            print("save data:",file_name )
            result_df.to_csv(file_name, index=False)
    
    # if only wanna run individual pool    
    # pool_address = '0xcbcdf9626bc03e24f779434178a73a0b4bad62ed' #WBTC WETH 0.3%
    # pool_address = '0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640' #USDC WETH
    # pool_address = '0x5777d92f208679db4b9778590fa3cab3ac9e2168' #DAI USDC
    # pool_address = '0x109830a1aaad605bbf02a9dfa7b0b92ec2fb7daa' #WSTETH WETH
    # pool_address = '0x4585fe77225b41b697c938b018e2ac67ac5a20c0' #WBTC WETH, 0.05%
    # result_df = get_uniswap_v3_data_year(pool_address, years)
    # file_name = lib_const.get_pool_filename(pool_address)
    # result_df.to_csv(file_name, index=False)
    # Display the DataFrame
    # result_df.head()


    load_price_related_data = False
    if load_price_related_data: # getting pool fee/vol related data
        # Set the start and end date
        start_date = datetime(2020, 11, 1)
        end_date = start_date + timedelta(days=1)


        df = pd.DataFrame()
        for token in lib_const.price_token_list:
            token_name = token[0]
            token_ticker = token[1] 
            df_price = download_crypto_price(token_name, token_ticker , start_date, end_date)
            print(f'get token {token_ticker} price in usd' )
            df_price_btc = pd.DataFrame()
            if(token_ticker != 'BTC'):
                df_price_btc = download_crypto_price(token_name, token_ticker , start_date, end_date, vs_currency='btc')
                print(f'get token {token_ticker} price in btc' )
                
            df = pd.concat([df, df_price, df_price_btc], ignore_index=True)

        price_file_name = 'output/price_data_all_token.csv'
        df.to_csv(price_file_name, index=False)

    #     print(f"DataFrame saved to {price_file_name}")