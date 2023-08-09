// SPDX-License-Identifier: BUSL-1.1
pragma solidity ^0.8.10;

import {RewardsController} from '../../contracts/rewards/RewardsController.sol';

contract RewardsControllerHarness is RewardsController {
    
    constructor(address emissionManager) RewardsController(emissionManager) {}
    // returns an asset's reward index
    function getAssetRewardIndex(address asset, address reward) external view returns (uint256) {
        return _assets[asset].rewards[reward].index;
    }

    function getLastUpdateTimestamp(address asset, address reward) external view returns (uint256) {
        return _assets[asset].rewards[reward].lastUpdateTimestamp;
    }

    function getEmissionRate(address asset, address reward) external view returns (uint256) {
        return _assets[asset].rewards[reward].emissionPerSecond;
    }

    function getAvailableRewardsCount(address asset) external view returns (uint256) {
        return _assets[asset].availableRewardsCount;
    }

    function isRewardEnabled(address reward) external view returns (bool) {
        return _isRewardEnabled[reward];
    }

    function isContract(address account) external view returns (bool) {
        return _isContract(account);
    }

    function getAssetsList() external view returns (address[] memory) {
        return _assetsList;
    }
}