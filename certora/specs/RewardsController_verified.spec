import "methods/Methods_base.spec";

using DummyERC20_rewardToken as REWARD;

methods {
    function getTransferStrategy(address) external returns (address) envfree;
    function isContract(address) external returns (bool) envfree;
    function getRewardsList() external returns (address[]) envfree;
    function REWARD.balanceOf(address) external returns (uint256) envfree;
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