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
    
    address[] rewardsList = getRewardsList();   
    // precondition
    require to != transferStrategy;
    require assets.length > 0;
    require rewardsList.length >= 2;

    uint256 strategyBalanceBefore = REWARD.balanceOf(transferStrategy);
    uint256 strategyBalanceBeforeB = REWARD_B.balanceOf(transferStrategy);
    uint256 userBalanceBefore = REWARD.balanceOf(to);
    uint256 userBalanceBeforeB = REWARD_B.balanceOf(to);

    address[] rewards;
    uint256[] amounts;

    // action
    rewards, amounts = claimAllRewards(e, assets, to);
    require rewards[0] == REWARD && rewards[1] == REWARD_B;

    uint256 strategyBalanceAfter = REWARD.balanceOf(transferStrategy);
    uint256 strategyBalanceAfterB = REWARD_B.balanceOf(transferStrategy);
    uint256 userBalanceAfter = REWARD.balanceOf(to);
    uint256 userBalanceAfterB = REWARD_B.balanceOf(to);

    // effects
    mathint strategyBalanceDecrease = strategyBalanceBefore - strategyBalanceAfter;
    mathint strategyBalanceDecreaseB = strategyBalanceBeforeB - strategyBalanceAfterB;
    mathint userBalanceIncrease = userBalanceAfter - userBalanceBefore;
    mathint userBalanceIncreaseB = userBalanceAfterB - userBalanceBeforeB;

    // postconditions
    assert strategyBalanceDecrease == to_mathint(amounts[0]);
    assert userBalanceIncrease == to_mathint(amounts[0]);
    assert strategyBalanceDecreaseB == to_mathint(amounts[1]);
    assert userBalanceIncreaseB == to_mathint(amounts[1]);
}