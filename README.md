# unique_Token-Code.finder
Code utilizes pancakeswap PairCreated events and bscscan source code api endpoint to accumulate and group token contracts by their source code


Sample of the data for this project is in unique_tokens.json. The real file is 100+ mb and is too large for github.
There are some extra bits in the code that are there because of the fact that this repo is a part of a larger project which is a composable, automated token audit. The hope is that the larger project will be useful to regular DeFi users who would like to know more information regarding the tokens they may be considering investing in. The project could also be transformed into some sort of PairCreated trading strategy, analyzing the newest tokens on pancakeswap.

As a fair warning, the code utilizes multiprocessing and running it for long periods of time will strain your cpu. My R5 3600X took roughly a week at 90% utilization to get through all of the existence of Pancake Swap V2.
