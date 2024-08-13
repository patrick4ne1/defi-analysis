# how to run it
* poetry install
* poetry run python main.py (get monthly optimal yield with trading off between capital efficiency and imp loss)
* poetry run python main_avg_yld.py (range to get average yeild)

# detail
methodology explanation can be found in medium article: 
* https://medium.com/@xben12/defi-decode-liquidity-mining-yield-impermanent-loss-and-set-optimal-range-e20c3472d2bb


Code: 
* main: main.py, main_avg_yld.py
* data: use library_data.py. This file will pre save data into csv in the output folder.
* logic (imp loss, range, coverage %): library_logic.py

# document
## Just Hold (No LP)
- Overview: This strategy involves holding the assets (e.g., WBTC and ETH) without participating in any liquidity provision (LP). You simply retain your assets in your wallet, not exposing them to the risks and potential rewards of liquidity mining.
- Performance: The "Just Hold" strategy serves as a benchmark for evaluating other LP strategies. Its performance is stable but does not capture any trading fees or potential yield from liquidity mining. However, it avoids impermanent loss.
- Use Case: Ideal for investors who want to avoid the complexity and risks of LP mining, particularly impermanent loss.
## LP Fixed Range (No Rebalance)
- Overview: This strategy involves providing liquidity within a fixed price range without any rebalancing. The LP position is set and left unchanged, allowing for the capture of trading fees within the set range.
- Performance: LP Fixed Range can achieve better performance than "Just Hold" when prices revert to the initial range. However, it may suffer in one-sided market moves as it does not adapt to price changes.
- Use Case: Suitable for investors who expect the price to stay within a specific range or revert to the initial position.
## Rebalance to Centre
- Overview: In this strategy, the LP position is periodically rebalanced to the center of the current price range. This method aims to keep the position centered around the prevailing market price.
- Performance: Rebalancing to the center helps mitigate impermanent loss but may result in realized losses if the market moves against the position. It can be more effective in a mean-reverting market.
- Use Case: Best for investors who expect price oscillations around a central value, allowing for consistent fee capture without significant impermanent loss.
## LP Rebalance Buy Low Sell High (BL_SH)
- Overview: This strategy involves shifting the liquidity bin opposite to the price movement when the bin is crossed. The idea is to "buy low and sell high," adjusting the LP position to capture price gaps.
- Performance: This method can achieve higher yields when prices revert back. It is a dynamic approach that tries to exploit price oscillations for profit, but it requires precise timing and can result in missed opportunities if the price trend continues in one direction.
- Use Case: Suitable for investors who anticipate price reversals and have the ability to actively manage and adjust their LP positions.
## LP Price-Follow with Mode
- Overview: This strategy tracks the price movements closely by shifting the liquidity range to follow the price trend. It can follow either the left(bearish), right(bullish), or both directions, depending on the expected market movement.
- Performance: LP Price-Follow can maximize fee capture by staying within the active trading range but may increase exposure to impermanent loss if the market does not revert as expected.
- Use Case: Ideal for traders who expect a trending market and want to maximize fee earnings by staying within the most active price range.


* The numbers represent the final value of the portfolio or the end value of assets (normalized to the starting value) after applying each strategy under the given scenario.
For instance, in the "1 year price revert-back" scenario, the "just_hold" strategy results in a normalized value of `1.000`, meaning that the value of the portfolio remains unchanged. In contrast, the "LP_reb_BL_SH" strategy results in a value of `1.295`, indicating a 12% increase in value compared to just holding the assets.
