import "methods/Methods_base.spec";

using DummyERC20_rewardToken as REWARD;
using DummyERC20_rewardTokenB as REWARD_B;
using TransferStrategyMultiRewardHarnessWithLinks as transferStrategy;

methods {
    function getAssetsList() external returns (address[]) envfree;
    function getRewardsList() external returns (address[]) envfree;
    function getAssetDecimals(address) external returns (uint8) envfree;
    function REWARD.balanceOf(address) external returns (uint256) envfree;
    function REWARD_B.balanceOf(address) external returns (uint256) envfree;
    function getAssetIndex(address, address) external returns (uint256, uint256) envfree;
    function isRewardEnabled(address) external returns (bool) envfree;
}

///////////////// Properties ///////////////////////

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
 * claimAllRewards function call decrease the transfer strategy's reward balance and 
 * increase recipient's reward balance by the return value of the function call.
 */
rule integrity_of_claimAllRewards() {
    env e;
    address[] assets;
    address to;
    
    address[] rewards = getRewardsList();   
    // preconditions
    require to != transferStrategy;
    require assets.length > 0;
    require rewards.length >= 2;
    require rewards[0] == REWARD && rewards[1] == REWARD_B;

    uint256 strategyBalanceBefore = REWARD.balanceOf(transferStrategy);
    uint256 strategyBalanceBefore_B = REWARD_B.balanceOf(transferStrategy);
    uint256 userBalanceBefore = REWARD.balanceOf(to);
    uint256 userBalanceBefore_B = REWARD_B.balanceOf(to);

    uint256[] amounts;

    // action
    _, amounts = claimAllRewards(e, assets, to);

    // effects
    uint256 strategyBalanceAfter = REWARD.balanceOf(transferStrategy);
    uint256 strategyBalanceAfter_B = REWARD_B.balanceOf(transferStrategy);
    uint256 userBalanceAfter = REWARD.balanceOf(to);
    uint256 userBalanceAfter_B = REWARD_B.balanceOf(to);
    mathint strategyBalanceDecrease = strategyBalanceBefore - strategyBalanceAfter;
    mathint strategyBalanceDecrease_B = strategyBalanceBefore_B - strategyBalanceAfter_B;
    mathint userBalanceIncrease = userBalanceAfter - userBalanceBefore;
    mathint userBalanceIncrease_B = userBalanceAfter_B - userBalanceBefore_B;

    // postconditions
    assert strategyBalanceDecrease == to_mathint(amounts[0]);
    assert strategyBalanceDecrease_B == to_mathint(amounts[1]);
    assert userBalanceIncrease == to_mathint(amounts[0]);
    assert userBalanceIncrease_B == to_mathint(amounts[1]);
}

/**
 * claimAllRewards function call claims all the rewards so that further claim ends up nothing
 */
rule claimAllRewards_claims_all() {
    env e;
    address[] assets;
    address to;
    
    address[] rewards = getRewardsList();

    // preconditions
    require to != transferStrategy;
    require assets.length > 0;
    require rewards.length >= 2;
    require rewards[0] == REWARD && rewards[1] == REWARD_B;

    // action 1
    claimAllRewards(e, assets, to);

    address recipient;
    uint256 amount;
    // action 2
    uint256 claimedReward = claimRewards(e, assets, amount, recipient, REWARD);
    // action 3
    uint256 claimedReward_B = claimRewards(e, assets, amount, recipient, REWARD_B);

    // postconditions
    assert claimedReward == 0;
    assert claimedReward_B == 0;
}

/**
 * User reward index monotonically increase
 */
rule user_index_keeps_growing(method f) filtered { f -> !f.isView } {
    address user;
    address asset; 
    address reward;
    requireInvariant user_index_LEQ_index(asset, reward, user);

    uint256 _index = getUserAssetIndex(user, asset, reward);

    env e; calldataarg args;
    f(e, args);

    uint256 index_ = getUserAssetIndex(user, asset, reward);
        
    assert index_ >= _index;
}


///////////////// Properties copied from RewardsController_base.spec ///////////////////////

// Property: Reward index monotonically increase
rule index_keeps_growing(address asset, address reward, method f) filtered { f -> !f.isView } {
    uint256 _index = getAssetRewardIndex(asset, reward);

    env e; calldataarg args;
    f(e, args);

    uint256 index_ = getAssetRewardIndex(asset, reward);
        
    assert index_ >= _index;
}

// Property: User index cannot surpass reward index
invariant user_index_LEQ_index(address asset, address reward, address user)
    getUserAssetIndex(user, asset, reward) <= getAssetRewardIndex(asset, reward);


// check this rule for every change in setup to make sure all is reachable 
// use builtin rule sanity;

//  Property: claiming reward twice is equivalent to one claim reward 
//  Note : this rule is implemented by comparing the whole storage 
rule noDoubleClaim() {

    env e; 
    //arbitrary array of any length (might be constrained due to loop unrolling )
    address[] assets; 
    uint256 l = assets.length;
    address to;
    claimAllRewards(e, assets, to);
    storage afterFirst = lastStorage;
    claimAllRewards(e, assets, to);
    storage afterSecond = lastStorage;

    assert afterSecond == afterFirst;
}

// Property: only an authorized user or the user itself can cause a reduction in accrued rewards for this user
rule onlyAuthorizeCanDecrease(method f) filtered { f -> !f.isView } {

    address user; address reward;
    uint256 before = getUserAccruedRewards(user, reward);

    env e;
    calldataarg args;
    f(e,args);

    uint256 after = getUserAccruedRewards(user, reward);

    assert after < before => (getClaimer(user) == e.msg.sender || user == e.msg.sender);
}

/**
 * getUserRewards includes pending rewards and accrued rewards, hence it is 
 * greater than or equal to the accrued rewards
 */
rule userRewards_GEQ_userAccruedRewards() {
    env e;
    address user;
    address reward;
    address[] assets = getAssetsList();
    // simplification
    require assets.length > 0 && assets.length <= 2;

    uint256 userRewards = getUserRewards(e, assets, user, reward);
    uint256 userAccruedRewards = getUserAccruedRewards(user, reward);

    assert userRewards >= userAccruedRewards;
}

/**
 * the data returned from getUserRewards and getAllUserRewards are consistent
 */
rule consistency_between_allUserRewards_and_userRewards() {
    env e;
    address user;
    address reward;
    address[] assets;
    address[] rewardList = getRewardsList();
    // simplification
    require assets.length == 1;
    require getAssetDecimals(assets[0]) == 6;
    require rewardList.length == 1;
    require rewardList[0] == reward;

    uint256 userRewards = getUserRewards(e, assets, user, reward);
    address[] rewards;
    uint256[] amounts;
    rewards, amounts = getAllUserRewards(e, assets, user);

    assert rewards[0] == reward && amounts[0] == userRewards;
}

/**
 * old index never exceeds new index
 */
rule old_index_LEQ_new_index() {
    address asset;
    address reward;
    uint256 oldIndex;
    uint256 newIndex;
    oldIndex, newIndex = getAssetIndex(asset, reward);
    assert oldIndex <= newIndex;
}

/**
 * no duplicate asset can be added
 */
rule no_duplicate_assets(method f) filtered { f -> !f.isView } {
    env e;
    calldataarg args;
    address[] assets1 = getAssetsList();
    require assets1.length == 1;
    require getAssetDecimals(assets1[0]) > 0;
    f(e, args);
    address[] assets2 = getAssetsList();

    assert assets2.length == 2 && getAssetDecimals(assets2[1]) > 0 => assets1[0] != assets2[1];
}

/**
 * no duplicate reward can be added
 */
rule no_duplicate_rewards(method f) filtered { f-> !f.isView } {
    env e;
    calldataarg args;
    address[] rewards1 = getRewardsList();
    require rewards1.length == 1;
    require isRewardEnabled(rewards1[0]);
    f(e, args);
    address[] rewards2 = getRewardsList();

    assert rewards2.length == 2 && isRewardEnabled(rewards2[1]) => rewards1[0] != rewards2[1];
}