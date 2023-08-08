import "methods/Methods_base.spec";

using DummyERC20_rewardToken as REWARD;
using DummyERC20_rewardTokenB as REWARD_B;
using TransferStrategyMultiRewardHarnessWithLinks as transferStrategy;

methods {
    function getRewardsList() external returns (address[]) envfree;
    function REWARD.balanceOf(address) external returns (uint256) envfree;
    function REWARD_B.balanceOf(address) external returns (uint256) envfree;
}

///////////////// Properties ///////////////////////

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