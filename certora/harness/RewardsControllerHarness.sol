// SPDX-License-Identifier: BUSL-1.1
pragma solidity ^0.8.10;

import {RewardsController} from '../../contracts/rewards/RewardsController.sol';

contract RewardsControllerHarness is RewardsController {
    
    constructor(address emissionManager) RewardsController(emissionManager) {}
    // returns an asset's reward index
    function getAssetRewardIndex(address asset, address reward) external view returns (uint256) {
        return _assets[asset].rewards[reward].index;
    }

    function isRewardEnabled(address asset) external view returns (bool) {
        return _isRewardEnabled[asset];
    }

    function isContract(address account) external view returns (bool) {
        return _isContract(account);
    }

    function getRewardsCountByAsset(address asset) external returns (uint256) {
        return this.getRewardsByAsset(asset).length;
    }

    function getRewardsCount() external returns (uint256) {
        return this.getRewardsList().length;
    } 
}