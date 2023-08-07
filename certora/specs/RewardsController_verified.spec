import "methods/Methods_base.spec";

using DummyERC20_rewardToken as REWARD;

methods {
    function getTransferStrategy(address) external returns (address) envfree;
    function getRewardOracle(address) external returns (address) envfree;
    function getClaimer(address) external returns (address) envfree;
    function isContract(address) external returns (bool) envfree;
    function getRewardsList() external returns (address[]) envfree;
    function getDistributionEnd(address, address) external returns (uint256) envfree;
    function getEmissionRate(address, address) external returns (uint256) envfree;
    function getAvailableRewardsCount(address) external returns (uint256) envfree;
    function isRewardEnabled(address) external returns (bool) envfree;
    function REWARD.balanceOf(address) external returns (uint256) envfree;
    function EMISSION_MANAGER() external returns (address) envfree;
}

///////////////// Properties ///////////////////////

/**
 * transferStrategy for any reward is a contract address if ever set
 */
invariant transferStrategy_is_contract(address reward)
    getTransferStrategy(reward) != 0 => isContract(getTransferStrategy(reward));

/**
 * claimRewards function call reverts if the `to` address param is zero
 */
rule claimRewards_revert_on_zero_address() {
    env e;
    address[] assets;
    uint256 amount;
    address to;
    address reward;
    
    // precondition
    require to == 0;
    // action
    claimRewards@withrevert(e, assets, amount, to, reward); 
    // postcondition
    assert lastReverted;
}

/**
 * claimRewardsOnBehalf function call reverts if the `user` or `to` address param is zero
 */
rule claimRewardsOnBehalf_revert_on_zero_addresses() {
    env e;
    address[] assets;
    uint256 amount;
    address user;
    address to;
    address reward;

    // precondition
    require user == 0 || to == 0;
    // action
    claimRewardsOnBehalf@withrevert(e, assets, amount, user, to, reward);
    // postcondition
    assert lastReverted;
}


/**
 * claimAllRewards function call reverts if the `to` address param is zero
 */
rule claimAllRewards_revert_on_zero_address() {
    env e;
    address[] assets;
    address to;

    // precondition
    require to == 0;
    // action
    claimAllRewards@withrevert(e, assets, to);
    // postcondition
    assert lastReverted;
}

/**
 * claimAllRewardsOnBehalf function call reverts if the `user` or `to` address param is zero
 */
rule claimAllRewardsOnBehalf_revert_on_zero_addresses() {
    env e;
    address[] assets;
    address user;
    address to;

    // precondition
    require user == 0 || to == 0;
    // action
    claimAllRewardsOnBehalf@withrevert(e, assets, user, to);
    // postcondition
    assert lastReverted;
}

/**
 * The effect of claimAllRewards function call covers that of the claimRewards function call
 */
rule claimAllRewards_cover_claimRewards() {
    storage init = lastStorage;
    env e;
    address[] assets;
    uint256 amount;
    address to;
    address[] rewards = getRewardsList();

    // precondition
    require rewards.length > 0;
    require rewards[0] == REWARD; // so that claimAllRewards will include REWARD when unravelling the loop

    // action 1
    claimRewards(e, assets, amount, to, REWARD);
    // effect 1
    uint256 balanceAfterClaim = REWARD.balanceOf(to);

    // action 2
    claimAllRewards(e, assets, to) at init;
    // effect 2
    uint256 balanceAfterClaimAll = REWARD.balanceOf(to);

    // postcondition
    assert balanceAfterClaimAll >= balanceAfterClaim;
}

/**
 * claimRewards and claimRewardsOnBehalf are equivalent if the user param of claimRewardsOnBehalf is msg.sender
 */
rule claim_and_claimOnBehalf_are_equivalent() {
    storage init = lastStorage;
    env e;
    address[] assets;
    uint256 amount;
    address to;
    address reward;

    // action 1
    claimRewards(e, assets, amount, to, reward);
    // effect 1
    storage afterClaim = lastStorage;

    // action 2
    claimRewardsOnBehalf(e, assets, amount, e.msg.sender, to, reward) at init;
    // effect 2
    storage afterClaimOnBehalf = lastStorage;

    // postcondition
    assert afterClaim == afterClaimOnBehalf;
}

/**
 * claimRewards and claimRewardsToSelf are equivalent if the to param of claimRewards is msg.sender
 */
rule claim_and_claimToSelf_are_equivalent() {
    storage init = lastStorage;
    env e;
    address[] assets;
    uint256 amount;
    address reward;

    // action 1
    claimRewards(e, assets, amount, e.msg.sender, reward);
    // effect 1
    storage afterClaim = lastStorage;
    
    // action 2
    claimRewardsToSelf(e, assets, amount, reward) at init;
    // effect 2
    storage afterClaimToSelf = lastStorage;

    // postcondition
    assert afterClaim == afterClaimToSelf;
}

/**
 * claimAllRewards and claimAllRewardsOnBehalf are equivalent if 
 * the user param of claimAllRewardsOnBehalf is msg.sender
 */
rule claimAll_and_claimAllOnBehalf_are_equivalent() {
    storage init = lastStorage;
    env e;
    address[] assets;
    address to;

    // action 1
    claimAllRewards(e, assets, to);
    // effect 1
    storage afterClaim = lastStorage;

    // action 2
    claimAllRewardsOnBehalf(e, assets, e.msg.sender, to) at init;
    // effect 2
    storage afterClaimOnBehalf = lastStorage;

    // postcondition
    assert afterClaim == afterClaimOnBehalf;
}


/**
 * claimAllRewards and claimAllToSelf are equivalent if 
 * the to param of claimAllRewards is msg.sender
 */
rule claimAll_and_claimAllToSelf_are_equivalent() {
    storage init = lastStorage;
    env e;
    address[] assets;

    // action 1
    claimAllRewards(e, assets, e.msg.sender);
    // effect 1
    storage afterClaim = lastStorage;

    // action 2
    claimAllRewardsToSelf(e, assets) at init;
    // effect 2
    storage afterClaimToSelf = lastStorage;

    // postcondition
    assert afterClaim == afterClaimToSelf;
}


/**
 * claimRewards function call decrease the transfer strategy's reward balance and 
 * increase recipient's reward balance by the return value of the function call, and
 * the return value is not more than the amount parameter. 
 */
rule integrity_of_claimRewards() {
    env e;
    address[] assets;
    uint256 amount;
    address to;

    address transferStrategy = getTransferStrategy(REWARD);

    // precondition
    require to != transferStrategy;

    uint256 strategyBalanceBefore = REWARD.balanceOf(transferStrategy);
    uint256 userBalanceBefore = REWARD.balanceOf(to);

    // action
    uint256 claimed = claimRewards(e, assets, amount, to, REWARD);

    uint256 strategyBalanceAfter = REWARD.balanceOf(transferStrategy);
    uint256 userBalanceAfter = REWARD.balanceOf(to);

    // effects
    mathint strategyBalanceDecrease = strategyBalanceBefore - strategyBalanceAfter;
    mathint userBalanceIncrease = userBalanceAfter - userBalanceBefore;

    // postconditions
    assert claimed <= amount;
    assert strategyBalanceDecrease == to_mathint(claimed);
    assert userBalanceIncrease == to_mathint(claimed);
}

/**
 * reward index does not change after its distribution end
 */
rule index_not_change_after_distributionEnd() {
    env e;
    address[] assets;
    uint256 amount;
    address reward;
    // preconditions
    require assets.length == 1;
    require e.block.timestamp > getDistributionEnd(assets[0], reward);

    // action 1
    claimRewardsToSelf(e, assets, amount, reward); // make sure index gets updated
    // effect 1
    uint256 indexBefore = getAssetRewardIndex(assets[0], reward);

    // action 2
    claimRewardsToSelf(e, assets, amount, reward); // make sure index gets updated again
    // effect 2
    uint256 indexAfter = getAssetRewardIndex(assets[0], reward);

    // postcondition
    assert indexBefore == indexAfter;
}

/** 
 * only emission manager can change transferStrategy
 */
rule only_emissionManager_changes_transferStrategy(method f) filtered { f -> !f.isView } {

    address reward;
    address transferStrategyBefore = getTransferStrategy(reward);

    env e; calldataarg args;
    f(e, args);

    address transferStragegyAfter = getTransferStrategy(reward);

    assert transferStragegyAfter != transferStrategyBefore => e.msg.sender == EMISSION_MANAGER();
}


/** 
 * only emission manager can change rewardOracle
 */
rule only_emissionManager_changes_rewardOracle(method f) filtered { f -> !f.isView } {

    address reward;
    address rewardOracleBefore = getRewardOracle(reward);

    env e; calldataarg args;
    f(e, args);

    address rewardOracleAfter = getRewardOracle(reward);

    assert rewardOracleAfter != rewardOracleBefore => e.msg.sender == EMISSION_MANAGER();
}


/** 
 * only emission manager can change claimer
 */
rule only_emissionManager_changes_claimer(method f) filtered { f -> !f.isView } {

    address user;
    address claimerBefore = getClaimer(user);

    env e; calldataarg args;
    f(e, args);

    address claimerAfter = getClaimer(user);

    assert claimerAfter != claimerBefore => e.msg.sender == EMISSION_MANAGER();
}


/** 
 * only emission manager can change distributionEnd
 */
rule only_emissionManager_changes_distributionEnd(method f) filtered { f -> !f.isView } {

    address asset; address reward;
    uint256 distributionEndBefore = getDistributionEnd(asset, reward);

    env e; calldataarg args;
    f(e, args);

    uint256 distributionEndAfter = getDistributionEnd(asset, reward);

    assert distributionEndAfter != distributionEndBefore => e.msg.sender == EMISSION_MANAGER();
}


/** 
 * only emission manager can change emission rate
 */
rule only_emissionManager_changes_emissionRate(method f) filtered { f -> !f.isView } {

    address asset; address reward;
    uint256 emissionRateBefore = getEmissionRate(asset, reward);

    env e; calldataarg args;
    f(e, args);

    uint256 emissionRateAfter = getEmissionRate(asset, reward);

    assert emissionRateAfter != emissionRateBefore => e.msg.sender == EMISSION_MANAGER();
}


/** 
 * only emission manager can change rewards count
 */
rule only_emissionManager_changes_rewardsCount(method f) filtered { f -> !f.isView } {

    address asset; 
    uint256 rewardsCountBefore = getAvailableRewardsCount(asset);

    env e; calldataarg args;
    f(e, args);

    uint256 rewardsCountAfter = getAvailableRewardsCount(asset);

    assert rewardsCountAfter != rewardsCountBefore => e.msg.sender == EMISSION_MANAGER();
}


/** 
 * only emission manager can change reward enabled status
 */
rule only_emissionManager_changes_rewardEnabled(method f) filtered { f -> !f.isView } {

    address reward; 
    bool rewardEnabledBefore = isRewardEnabled(reward);

    env e; calldataarg args;
    f(e, args);

    bool rewardEnabledAfter = isRewardEnabled(reward);

    assert rewardEnabledAfter != rewardEnabledBefore => e.msg.sender == EMISSION_MANAGER();
}