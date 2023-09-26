## Overview

`RewardsController` contract configures, calculates users' reward data and allow users and claimers to claim those rewards. The state variables include:

1. `_assets`, type `mapping(address => RewardsDataTypes.AssetData)`, where `AssetData` is defined as below

   ```
   struct AssetData {
        // Map of reward token addresses and their data (rewardTokenAddress => rewardData)
        mapping(address => RewardData) rewards;
        // List of reward token addresses for the asset
        mapping(uint128 => address) availableRewards;
        // Count of reward tokens for the asset
        uint128 availableRewardsCount;
        // Number of decimals of the asset
        uint8 decimals;
   }
   ```

   , where `RewardData` is defined as below

   ```
    struct RewardData {
        // Liquidity index of the reward distribution
        uint104 index;
        // Amount of reward tokens distributed per second
        uint88 emissionPerSecond;
        // Timestamp of the last reward index update
        uint32 lastUpdateTimestamp;
        // The end of the distribution of rewards (in seconds)
        uint32 distributionEnd;
        // Map of user addresses and their rewards data (userAddress => userData)
        mapping(address => UserData) usersData;
    }
   ```

   , where `UserData` is defined as below

   ```
   struct UserData {
    // Liquidity index of the reward distribution for the user
    uint104 index;
    // Amount of accrued rewards for the user since last user index update
    uint128 accrued;
   }
   ```

   From the data structure above, we can see that

   - One asset can have multiple available reward tokens
   - each reward token has its own data, which will be described below
   - each reward token has it liquidity index, emission rate, last update timestamp, distribution end and its users' data
   - each reward user has its liquidity index and amount of accrued reward

   Please note that RewardData.index records the amount of reward tokens accumulated since the previous RewardData.lastUpdateTimestamp, while current RewardData.lastUpdateTimestamp is for the calculation of RewardData.index in the future.

   RewardData.index affects RewardData.UserData[user].index, which in turn affects RewardData.UserData[user].accrued

2. `_isRewardEnabled`, type `mapping(address => bool)`. We can see that reward can be disabled by this flag

3. `_rewardsList`, type `address[]`

4. `_assetsList`, type `address[]`

5. `_authorizedClaimers`, type `mapping(address => address)`. Each user can authorize a claimer to claim rewards on behalf of her/him

6. `_transferStrategy`, type `mapping(address => ITransferStrategyBase)`. Each reward can have one transfer strategy

7. `_rewardOracle`, type `mapping(address => IEACAggregatorProxy)`. Each reward can have one reward oracle

It has the following state modifying functions:

1. `setDistributionEnd(address asset, address reward, uint32 newDistributionEnd)`, which obviously sets the distributionEnd of an reward on an asset
2. `setEmissionPerSecond(address asset, address[] calldata rewards, uint88[] calldata newEmissionsPerSecond)`, which sets emission rate in batch mode
3. `configureAssets(RewardsDataTypes.RewardsConfigInput[] memory config)`, which configures the asset and its rewards
4. `setTransferStrategy(address reward, ITransferStrategyBase transferStrategy)`
5. `setRewardOracle(address reward, IEACAggregatorProxy rewardOracle)`
6. `handleAction(address user, uint256 totalSupply, uint256 userBalance)`, hook function to update rewards distribution
7. `claimRewards(address[] calldata assets, uint256 amount, address to, address reward)`
8. `claimRewardsOnBehalf(address[] calldata assets, uint256 amount, address user, address to, address reward)`
9. `claimRewardsToSelf(address[] calldata assets, uint256 amount, address reward)`
10. `claimAllRewards(address[] calldata assets, address to)`
11. `claimAllRewardsOnBehalf(address[] calldata assets, address user, address to)`
12. `claimAllRewardsToSelf(address[] calldata assets)`

It has a bunch of view functions which I would omit here

### Properties

1. For any asset, its asset data integrity should be assured, i.e., for any number `i` less than `availableRewardsCount`, `availableRewards[i]` should not be zero address, and `rewards[availableRewards[i]]` should be valid `RewardData`
2. For any asset in `_assetsList`, there should be its `AssetData` in `_assets` and vice versa
3. For any reward token found in `_rewardsList`, there should be the same reward found in `_assets` and vice versa
4. the `index` in `RewardData` should be the same as the `index` in the `UserData` inside the `RewardData`
5. `claimAllRewards`, `claimAllRewardsOnBehalf` and `claimAllRewardsToSelf` should be equivalent with certain parameters
6. `claimRewards`, `claimRewardsOnBehalf` and `claimRewardsToSelf` should be equivalent with certain parameters
7. `claimAllRewards` should claim not less than `claimRewards`
