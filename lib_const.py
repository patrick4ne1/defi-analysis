pool_info_list = [
    ['0xcbcdf9626bc03e24f779434178a73a0b4bad62ed', 'WBTC',  'WETH',  0.003],
    ['0x4585fe77225b41b697c938b018e2ac67ac5a20c0' , 'WBTC' ,'WETH', 0.0005],
    ['0xc7bbec68d12a0d1830360f8ec58fa599ba1b0e9b', 'WETH', 'USDT', 0.01],
    ['0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640' , 'USDC', 'WETH', ],
    ['0x5777d92f208679db4b9778590fa3cab3ac9e2168' , 'DAI', 'USDC', ], 
    ['0x109830a1aaad605bbf02a9dfa7b0b92ec2fb7daa', 'wstETH', 'WETH',],
    ['0x3416cf6c708da44db2624d63ea0aaef7113527c6', 'USDC', 'USDT', 0.0001],
]

pool_info_list_polygon = [
    ['0x50eaEDB835021E4A108B7290636d62E9765cc6d7', 'WBTC', 'WETH', 0.0005],
    ['0xBB98B3D2b18aeF63a3178023A920971cf5F29bE4', 'WETH', 'USDT', 0.0005],
    ['0x45dDa9cb7c25131DF268515131f647d726f50608', 'USDC', 'WETH', 0.0005],
    ['0xeEF1A9507B3D505f0062f2be9453981255b503c8', 'WBTC', 'USDC', 0.0005],
    ['0xf369277650aD6654f25412ea8BFBD5942733BaBC', 'USDC', 'DAI', 0.0001]
]

pool_info_list_arbitrum = [
    ['0x2f5e87C9312fa29aed5c179E456625D79015299c', 'WBTC', 'WETH', 0.0005],
    ['0x641C00A822e8b671738d32a431a4Fb6074E5c79d', 'WETH', 'USDT', 0.0005],
    ['0xC6962004f452bE9203591991D15f6b388e09E8D0', 'WETH', 'USDC', 0.0005],
    ['0xac70bD92F89e6739B3a08Db9B6081a923912f73D', 'WBTC', 'USDC', 0.0005],
    ['0x53C6ca2597711Ca7a73b6921fAf4031EeDf71339', 'WBTC', 'USDT', 0.0005],
    ['0x7CF803e8d82A50504180f417B8bC7a493C0a0503', 'USDC', 'DAI', 0.0001],
    ['0xA961F0473dA4864C5eD28e00FcC53a3AAb056c1b', 'WETH', 'DAI', 0.003],
]

pool_info_list_optimism = [
    ['0x85C31FFA3706d1cce9d525a00f1C7D4A2911754c', 'WETH', 'WBTC', 0.0005],
    ['0xc858A329Bf053BE78D6239C4A4343B8FbD21472b', 'WETH', 'USDT', 0.0005],
    ['0x85149247691df622eaF1a8Bd0CaFd40BC45154a9', 'WETH', 'USDC', 0.0005],
    ['0x394A9fcBab8599437d9Ec4e5A4a0EB7cb1fd2F69', 'USDC', 'WBTC', 0.0005],
    ['0x0843e0F56B9e7fDc4fb95faBBA22a01ef4088f41', 'WBTC', 'USDT', 0.003],
    ['0xd28f71e383E93C570D3EdFe82EBbcEb35Ec6C412', 'USDC', 'DAI', 0.0001],
    ['0x03aF20bDAaFfB4cC0A521796a223f7D85e2aAc31', 'WETH', 'DAI', 0.003]
]

pool_info_list_bsc = [
    ['0xb125aa15Ad943D96e813E4A06d0c34716F897e26', 'WETH', 'USDT', 0.0001],
    ['0x17507bEF4c3abC1Bc715be723eE1baF571256E05', 'WETH', 'USDC', 0.003],
    ['0x039df62583Ddc1C5FdA75DB152b87113D863B6d6', 'DAI', 'USDT', 0.0001]
]


user_data = [
    '0x0aff782b30a81eb4d4104eb9bf0ddb0a19920981'
]
# data needed by coingecko API
price_token_list =[
    ['bitcoin', 'BTC' ],
    ['ethereum',  'ETH']
]

def get_pool_filename(pool_address, token0=None, token1=None):   
    print(pool_address) 
    if token0 is None or token1 is None:
        for pool_info in pool_info_list:
            if pool_info[0] == pool_address:
                token0 = pool_info[1]
                token1 = pool_info[2]
                break
    file_name_addon = "_".join([pool_address, token0, token1])
    file_name = 'output/pool_data_' + file_name_addon + '.csv'
    return file_name

def get_crypto_price_filename(filename):
    return 'output/' + filename

#    date_begin = datetime.strptime(date_begin_yyyymmdd, '%Y%m%d')
#    date_end = datetime.strptime(date_end_yyyymmdd, '%Y%m%d')