"""Curated fallback questions for Blockchain & Web3. Code is Markdown."""

from seed.questions import Bank, q

QUESTIONS: Bank = {
    # --- How blockchains work -----------------------------------------------------------------
    "bc_what_is_blockchain": [
        q("What links each block in a blockchain to the block before it?",
          "Each block stores the hash of the previous block",
          ("Each block stores a copy of every earlier block", "A central server keeps a list of block numbers",
           "Blocks are linked by the time they were created"),
          "Because each block includes the previous block's hash, changing an old block changes its hash and "
          "breaks every link after it."),
        q("Why is it hard to change a transaction recorded several blocks ago?",
          "Every later block would have to be redone and accepted by the network",
          ("The transaction is encrypted so no one can read it", "Old blocks are deleted once they are full",
           "Only the person who sent it is allowed to edit it"),
          "Editing an old block changes its hash, so all later blocks must be rebuilt, and the rest of the "
          "network would still have to accept the rewritten chain."),
        q("What does it mean that a public blockchain is decentralised?",
          "Many independent computers keep and check copies of the ledger",
          ("One company runs the ledger on a very large server", "The ledger is split so no one sees all of it",
           "Transactions are processed without any computers at all"),
          "There is no single owner: many nodes hold the full history and check new blocks against the same "
          "rules, so no one party can quietly change it."),
    ],
    "bc_hash_functions": [
        q("What happens to a SHA-256 hash if one character of the input changes?",
          "The hash changes completely and unpredictably",
          ("Only the last character of the hash changes", "The hash stays the same for small edits",
           "The hash becomes one character longer"),
          "Good hash functions have the avalanche effect: any change to the input gives a completely "
          "different fixed-length output."),
        q("Why can't you work out the input from a cryptographic hash?",
          "Hash functions are designed to be one-way",
          ("The hash is encrypted with a secret key", "The input is stored on a separate server",
           "Hashes are deleted after they are checked"),
          "A cryptographic hash is preimage-resistant: there is no practical way back from the output to the "
          "input other than guessing inputs."),
        q("A block has 1,024 transactions in a Merkle tree. Roughly how many hashes prove that one transaction is included?",
          "About 10", ("About 1,024", "About 512", "Exactly 1"),
          "A Merkle proof needs one sibling hash per level of the tree, and a tree of 1,024 leaves has "
          "log2(1024) = 10 levels."),
    ],
    "bc_keys_signatures": [
        q("Which key must you keep secret to control a blockchain account?", "The private key",
          ("The public key", "The address", "The transaction hash"),
          "The private key creates signatures. The public key and the address derived from it are meant to "
          "be shared so others can send to you and check your signatures."),
        q("What does a valid digital signature on a transaction prove?",
          "It was authorised by the holder of the matching private key",
          ("It was approved by a bank before being sent", "It was sent from a trusted IP address",
           "It has already been included in a block"),
          "Anyone can check the signature with the public key, but only the private key holder could have "
          "produced it, and it fails if the transaction is altered."),
        q("How is an Ethereum address related to its owner's keys?",
          "It is derived from the public key", ("It is the private key written in hex", "It is chosen freely by the owner",
                                                "It is assigned by the network at random"),
          "An Ethereum address is the last 20 bytes of the Keccak-256 hash of the public key, which itself "
          "comes from the private key."),
    ],
    "bc_p2p_networks": [
        q("What does a full node do?", "Stores the chain and checks every block against the rules",
          ("Mines new coins and sends them to users", "Stores only the user's own transactions",
           "Approves which users may join the network"),
          "A full node independently verifies every block and transaction, so it doesn't have to trust "
          "anyone else's copy."),
        q("How does a new transaction reach the rest of a blockchain network?",
          "Nodes pass it on to their peers, who pass it on again",
          ("It is emailed to a central coordinator", "It is uploaded to the main blockchain server",
           "Only miners in the same country receive it"),
          "Peer-to-peer gossip spreads transactions and blocks node by node until the whole network has seen "
          "them."),
        q("Why might a phone wallet use a light node instead of a full node?",
          "It checks block headers without downloading the whole chain",
          ("It stores more history than a full node", "It can create blocks without other nodes",
           "It doesn't need an internet connection at all"),
          "Light clients download block headers and ask for proofs of the data they need, trading some "
          "independence for far less storage and bandwidth."),
    ],
    "bc_use_cases": [
        q("When is an ordinary database usually a better choice than a blockchain?",
          "When one trusted organisation controls all the data",
          ("When the data needs to be searched quickly", "When more than ten people use the system",
           "When the data includes dates and times"),
          "A blockchain's cost and slowness pay off when parties who don't trust each other share records. "
          "With one trusted owner, a database is simpler and faster."),
        q("What happens if you send cryptocurrency to the wrong address by mistake?",
          "It usually can't be reversed by anyone",
          ("The network refunds it automatically after a day", "Your bank can cancel the payment for you",
           "The miners return it if you ask them politely"),
          "Confirmed transactions are final by design. Unless the recipient chooses to send it back, the "
          "funds are gone, which is why checking addresses matters."),
        q("Someone online promises to double any crypto you send them. What is this most likely to be?",
          "A scam", ("A normal staking reward", "A feature of proof of stake", "A test network giveaway"),
          "Giveaway and \"doubling\" offers are a common crypto scam: payments can't be reversed, so the money "
          "sent is simply lost."),
    ],
    "bc_wallets": [
        q("What is a seed (recovery) phrase?",
          "A list of words that can recreate all of a wallet's keys",
          ("A password for logging into an exchange website", "The public address shared to receive funds",
           "A code the network sends to confirm payments"),
          "The seed phrase encodes the master secret the wallet's private keys come from. Anyone who has it "
          "controls the funds, so it should never be shared or typed into websites."),
        q("A support agent in a chat asks for your seed phrase to fix your wallet. What should you do?",
          "Refuse: no genuine support ever needs it",
          ("Share it, as support staff are trusted", "Share only the first half of the words",
           "Send it by email instead, as that is safer"),
          "Asking for a seed phrase is a hallmark of a scam. With it, the scammer can move every asset in the "
          "wallet."),
        q("What is the main difference between a custodial and a self-custody wallet?",
          "Who holds the private keys", ("Which blockchain they connect to", "How fast transactions confirm",
                                         "Whether the wallet has an app"),
          "With a custodial wallet a company such as an exchange holds the keys for you. With self-custody, "
          "only you hold them, and only you can recover them."),
    ],
    "bc_consensus": [
        q("In proof of work, what makes creating a valid block costly?",
          "Finding a hash below the target takes huge amounts of computation",
          ("Each block must be approved by a central bank", "Miners must pay a fee to the network founder",
           "Every node must vote on each transaction by hand"),
          "Miners repeatedly change a nonce and hash the block until the result is below the difficulty "
          "target, which takes a lot of work but is quick for others to check."),
        q("In proof of stake, what can happen to a validator who signs two conflicting blocks?",
          "Part of its staked funds is destroyed (slashed)", ("It receives a double reward", "It is promoted to lead validator",
                                                              "Nothing, as signatures are not checked"),
          "Slashing makes dishonest behaviour expensive: provable misbehaviour costs the validator part of the "
          "stake it locked up."),
        q("What can an attacker who controls most of the mining power still NOT do?",
          "Spend coins from other people's addresses",
          ("Reverse their own recent transactions", "Refuse to include some transactions",
           "Build a longer chain than everyone else"),
          "A 51% attacker can reorder or censor recent transactions and double-spend their own coins, but "
          "can't forge signatures, so they can't take other people's funds."),
    ],
    "bc_bitcoin": [
        q("Alice has one unspent output worth 1 BTC and pays Bob 0.3 BTC. What happens to the rest?",
          "It goes back to Alice as change, minus the fee", ("It stays locked in the old output", "It is sent to the miner",
                                                             "It is split between Alice and Bob"),
          "A UTXO is spent in full, so the transaction creates an output to Bob and a change output back to "
          "Alice. Whatever isn't assigned to an output is the miner's fee."),
        q("Roughly how often is a new Bitcoin block found?", "About every 10 minutes",
          ("About every 10 seconds", "About once an hour", "About once a day"),
          "The network adjusts mining difficulty every 2,016 blocks to keep the average close to ten minutes."),
        q("What is the maximum number of bitcoins that will ever exist?", "21 million",
          ("100 million", "1 billion", "There is no limit"),
          "The block reward halves every 210,000 blocks, so total issuance approaches 21 million BTC."),
    ],
    "bc_ethereum": [
        q("What is gas in Ethereum?", "A measure of the computation a transaction uses",
          ("The fuel used by miners' computers", "A separate token used for voting", "The size of a block in megabytes"),
          "Each EVM operation costs a set amount of gas. The fee paid is the gas used multiplied by the price "
          "per unit of gas."),
        q("What is the difference between an externally owned account and a contract account?",
          "Only an externally owned account is controlled by a private key",
          ("Only a contract account can hold Ether", "Only an externally owned account can store code",
           "There is no difference between them"),
          "Externally owned accounts are controlled by private keys and start transactions. Contract accounts "
          "are controlled by their code and run when called."),
        q("Why must the Ethereum Virtual Machine be deterministic?",
          "Every node must get the same result running the same transaction",
          ("So that transactions run faster on phones", "So that contracts can access the internet",
           "So that only one node needs to run the code"),
          "Nodes re-execute transactions to check blocks. If results differed between nodes, they couldn't "
          "agree on the state."),
    ],
    # --- Building on Ethereum -----------------------------------------------------------------
    "bc_smart_contracts": [
        q("What is a smart contract?", "A program stored and run on a blockchain",
          ("A legal agreement signed online", "A contract written by an AI model", "A private chat between two wallets"),
          "A smart contract is code deployed to an address. Anyone can call it, and its results are agreed "
          "by the whole network."),
        q("A bug is found in a deployed contract that was written without any upgrade mechanism. What can its developers do?",
          "Deploy a new contract and move users to it",
          ("Edit the code at the same address", "Ask miners to delete the contract",
           "Roll the blockchain back to before deployment"),
          "Deployed bytecode can't be changed. Unless the contract was built to be upgradeable, the fix is a "
          "new deployment and a migration."),
        q("Why can't a smart contract fetch today's weather from a website by itself?",
          "Every node must get the same result, and websites can change",
          ("Contracts are not allowed to use numbers", "Weather data is too large to store",
           "The EVM can only add and subtract"),
          "Calls to outside services wouldn't give every node the same answer, so contracts rely on oracles "
          "to bring data on chain."),
    ],
    "bc_solidity": [
        q("In Solidity, what does `msg.sender` hold?", "The address that called the current function",
          ("The address that deployed the contract", "The contract's own address", "The address of the miner"),
          "`msg.sender` is the immediate caller: a user's account or another contract. The deployer is a "
          "different address unless saved at deployment."),
        q("What does `require(balance >= amount, \"Too low\");` do when the condition is false?",
          "Reverts the call and undoes its changes", ("Prints a warning and carries on", "Sets `balance` to `amount`",
                                                      "Skips only the next line of code"),
          "`require` checks a condition. If it fails, the whole call reverts with the message, and its state "
          "changes are undone."),
        q("Which declaration maps each address to a token balance?", "`mapping(address => uint256) balances;`",
          ("`array(address, uint256) balances;`", "`dict[address] uint256 balances;`",
           "`uint256 => address balances;`"),
          "A `mapping` stores a value for each key. `mapping(address => uint256)` is the usual way to track "
          "balances per account."),
    ],
    "bc_dev_tools": [
        q("Why test a contract on a local development chain first?",
          "It's free, fast and can be reset at will",
          ("Contracts can only be deployed from local chains", "Local chains run the code more securely",
           "Real networks don't allow contracts to be tested"),
          "A local chain such as Hardhat's or Anvil gives instant blocks, funded test accounts and easy "
          "resets, with nothing real at stake."),
        q("What is a testnet?", "A public network for testing whose coins have no real value",
          ("A paid network for professional developers", "A tool that scans contracts for bugs",
           "A copy of the main network run by one company"),
          "Testnets such as Sepolia behave like the real network, but their Ether comes free from faucets, so "
          "mistakes cost nothing."),
        q("Why is thorough automated testing especially important for smart contracts?",
          "Deployed code is hard to change and often controls real money",
          ("Contracts can't be read once they are deployed", "Testing makes gas fees cheaper",
           "Blockchains reject contracts without tests"),
          "A bug in deployed code can't simply be patched, and attackers can call any public function, so "
          "contracts need tests before they go live."),
    ],
    "bc_tokens": [
        q("What is the main difference between an ERC-20 and an ERC-721 token?",
          "ERC-721 tokens are each unique; ERC-20 units are interchangeable",
          ("ERC-20 tokens can't be transferred between users", "ERC-721 tokens are stored outside the blockchain",
           "ERC-20 only works on Bitcoin"),
          "ERC-20 tracks balances of identical units. ERC-721 tracks who owns each individual token ID."),
        q("In ERC-20, what does `approve(spender, amount)` allow?",
          "The spender to transfer up to that amount of your tokens", ("The spender to mint new tokens for you",
                                                                       "Your tokens to be frozen until a date",
                                                                       "The contract to change its own code"),
          "`approve` sets an allowance. The spender can then use `transferFrom` to move up to that many tokens "
          "from your account."),
        q("Why do many projects build tokens on OpenZeppelin's contracts instead of writing their own?",
          "They are widely used, audited implementations of the standards",
          ("They are required by the Ethereum network", "They make every transfer free of gas",
           "They hide token balances from other users"),
          "Reusing audited, battle-tested code avoids subtle mistakes in reimplementing a standard."),
    ],
    "bc_contract_security": [
        q("""Which change fixes the weakness in this function?

```solidity
function withdraw() external {
    uint256 amount = balances[msg.sender];
    (bool ok, ) = msg.sender.call{value: amount}("");
    require(ok);
    balances[msg.sender] = 0;
}
```""",
          "Set the balance to zero before sending the Ether",
          ("Send the Ether twice to make sure it arrives", "Make the function `public` instead of `external`",
           "Remove the `require(ok)` check"),
          "Sending Ether hands control to the caller before the balance is cleared, so it could call "
          "`withdraw` again (reentrancy). Checks-effects-interactions updates state first."),
        q("A function that changes the contract owner has no access check. What is the risk?",
          "Anyone can call it and take control of the contract",
          ("The function will cost more gas to run", "Only the owner will be able to read it",
           "The contract will refuse to deploy"),
          "Public functions can be called by anyone. Sensitive functions need checks such as `onlyOwner` or "
          "role-based access control."),
        q("What is a smart contract audit?",
          "An expert review of the code for security flaws before launch",
          ("A tax report on the contract's earnings", "A test that measures the contract's gas use",
           "A vote by token holders to approve the code"),
          "Independent auditors review the code and its design for vulnerabilities. Audits reduce risk but "
          "don't replace testing or guarantee safety."),
    ],
    "bc_dapps": [
        q("In a dApp, who signs a transaction that changes a contract's state?",
          "The user, in their own wallet", ("The dApp's web server", "The developer who deployed it",
                                            "The browser, automatically"),
          "The front end builds the transaction, but the user's wallet asks them to approve and sign it, so "
          "the dApp never sees the private key."),
        q("Why does reading data from a contract cost the user no gas?",
          "A read-only call is run by one node and changes nothing", ("Reading is paid for by the contract's owner",
                                                                       "Gas is charged only once per day",
                                                                       "Reads are stored in the browser's cache"),
          "Calling a `view` function locally doesn't create a transaction or change state, so nothing needs "
          "to be mined or paid for."),
        q("How can a dApp update its page when a contract does something?",
          "Listen for the events the contract emits",
          ("Ask the user to refresh every few seconds", "Read the contract's source code again",
           "Wait for an email from the network"),
          "Contracts emit events into transaction logs. Libraries such as viem let a front end subscribe to "
          "them and react."),
    ],
    "bc_oracles_storage": [
        q("What is a blockchain oracle?", "A service that brings outside data onto the chain",
          ("A tool that predicts future prices", "The node that creates the first block", "A wallet with extra security"),
          "Oracles fetch data such as prices or results and post it on chain so contracts can use it."),
        q("Why is relying on a single oracle risky?",
          "If it is wrong or compromised, every contract using it is too",
          ("A single oracle costs more gas than several", "Oracles can only report one value per year",
           "Contracts can't read data from one oracle"),
          "An oracle is a trusted input. Using several independent sources reduces the chance that one bad "
          "feed misleads the contract."),
        q("Why do many NFTs store their images on IPFS rather than on chain?",
          "Storing large files on chain is very expensive",
          ("Blockchains can't store any data at all", "IPFS makes images load without the internet",
           "Images on chain can be seen by everyone"),
          "On-chain storage costs gas per byte. IPFS addresses files by their content hash, so the contract "
          "can store a short, tamper-evident link instead."),
    ],
    "bc_defi": [
        q("A pool following \\(x \\cdot y = k\\) holds 10 A and 1,000 B. Ignoring fees, how many B does adding 10 A pay out?",
          "500 B", ("1,000 B", "250 B", "100 B"),
          "\\(k = 10 \\cdot 1000 = 10000\\). With 20 A in the pool, B must fall to \\(10000 / 20 = 500\\), so "
          "500 B come out: each extra A buys less B."),
        q("What is a stablecoin designed to do?", "Keep a steady value, usually one US dollar",
          ("Rise in value at a fixed rate", "Pay interest to everyone who holds it", "Work only on one exchange"),
          "Stablecoins track a reference such as the dollar, backed by reserves or by collateral held in "
          "contracts."),
        q("Why do DeFi lending protocols require borrowers to deposit more collateral than they borrow?",
          "There is no credit check, so the excess protects lenders",
          ("Smart contracts can't count exact amounts", "The extra is paid as a fee to miners",
           "It makes the loan cheaper to repay early"),
          "Loans are anonymous, so over-collateralisation and automatic liquidation protect lenders if the "
          "collateral's value falls."),
    ],
    "bc_scaling": [
        q("How does a rollup increase throughput?",
          "It runs transactions off the main chain and posts compressed data back",
          ("It makes every block on the main chain bigger", "It removes signatures from transactions",
           "It lets nodes skip checking blocks"),
          "Rollups execute many transactions on layer 2, then publish their data and results to layer 1, "
          "which keeps it secure."),
        q("How does an optimistic rollup catch an invalid batch?",
          "Anyone can submit a fraud proof during a challenge window",
          ("A validity proof is checked for every batch", "The main chain re-runs every transaction",
           "Users vote on each batch with their tokens"),
          "Optimistic rollups assume batches are valid but allow a challenge period. Zero-knowledge rollups "
          "instead post a validity proof with each batch."),
        q("What is the \"blockchain trilemma\"?",
          "The difficulty of being decentralised, secure and scalable at once",
          ("A rule limiting each chain to three tokens", "The three keys every wallet must hold",
           "The three steps of mining a block"),
          "Raising throughput by, for example, using fewer powerful nodes tends to weaken decentralisation or "
          "security, which is why layer 2 designs exist."),
    ],
}
