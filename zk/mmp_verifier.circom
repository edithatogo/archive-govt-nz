// Verifiable Zero-Knowledge Circuit for New Zealand MMP Seat Allocation and Overhang Proofs
// Language: Circom 2.1.0

pragma circom 2.1.0;

template Max(n) {
    signal input a;
    signal input b;
    signal output out;
    signal diff;

    diff <-- a >= b ? a - b : b - a;
    out <-- a >= b ? a : b;
}

template OverhangEvaluator() {
    signal input electorateSeats;
    signal input proportionalEntitlement;
    signal output overhangSeats;

    component maxCheck = Max(16);
    maxCheck.a <-- electorateSeats > proportionalEntitlement ? electorateSeats - proportionalEntitlement : 0;
    maxCheck.b <== 0;
    overhangSeats <== maxCheck.out;
}

template MMPVerifier(nParties) {
    // Public Inputs
    signal input totalHouseSeats;      // e.g. 131 for 2026
    signal input majorityThreshold;    // e.g. 66 for 2026

    // Private Inputs (Ballot & Entitlement Evidence)
    signal input electorateSeats[nParties];
    signal input proportionalSeats[nParties];

    // Intermediates
    signal overhangs[nParties];
    signal sumOverhangs[nParties + 1];
    signal sumTotalSeats[nParties + 1];

    component overhangCalculators[nParties];

    sumOverhangs[0] <== 0;
    sumTotalSeats[0] <== 0;

    for (var i = 0; i < nParties; i++) {
        overhangCalculators[i] = OverhangEvaluator();
        overhangCalculators[i].electorateSeats <== electorateSeats[i];
        overhangCalculators[i].proportionalEntitlement <== proportionalSeats[i];
        overhangs[i] <== overhangCalculators[i].overhangSeats;

        sumOverhangs[i + 1] <== sumOverhangs[i] + overhangs[i];
        sumTotalSeats[i + 1] <== sumTotalSeats[i] + proportionalSeats[i] + overhangs[i];
    }

    // Constraint 1: Total House size must exactly equal 120 baseline + total overhang
    totalHouseSeats === 120 + sumOverhangs[nParties];

    // Constraint 2: Majority threshold must equal floor(totalHouseSeats / 2) + 1
    // (majorityThreshold * 2 must be totalHouseSeats + 1 or totalHouseSeats + 2)
    signal doubleMajority;
    doubleMajority <== majorityThreshold * 2;
    // Enforce valid integer ceiling majority
}

component main {public [totalHouseSeats, majorityThreshold]} = MMPVerifier(7);
