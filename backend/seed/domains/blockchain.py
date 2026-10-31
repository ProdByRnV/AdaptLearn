"""Blockchain & Web3: how blockchains work, from hashes and consensus to smart contracts and dApps.

What Is a Blockchain? is the starting topic. The rest builds on Foundations (binary, how the
internet works, programming concepts and security basics) and, for dApps, on Async JavaScript from
Web Development. Topics stay technical: no investment or trading advice.
"""

from seed.model import Domain, Topic, article, docs, video

TOPICS: tuple[Topic, ...] = (
    # --- How blockchains work -----------------------------------------------------------------
    Topic(
        "bc_what_is_blockchain", "What Is a Blockchain?",
        "A shared ledger that many computers keep in agreement: blocks of transactions chained together "
        "by hashes, why changing old records is hard, and what decentralisation means.",
        1,
        (
            video("Blockchain 101 - A Visual Demo (Anders Brownworth)", "https://www.youtube.com/watch?v=_160oMzblY8"),
            article("Anders Brownworth: Interactive blockchain demo", "https://andersbrownworth.com/blockchain/"),
            article("IBM: What is blockchain?", "https://www.ibm.com/think/topics/blockchain"),
        ),
    ),
    Topic(
        "bc_hash_functions", "Hashes & Merkle Trees",
        "The cryptographic hash functions that hold a blockchain together: fixed-size fingerprints, why "
        "they can't be reversed or forged, how blocks link by hash, and Merkle trees and proofs.",
        2,
        (
            video("Hashing Algorithms and Security (Computerphile)", "https://www.youtube.com/watch?v=b4b8ktEV4Bg"),
            article("Decentralized Thoughts: What is a Merkle tree?", "https://decentralizedthoughts.github.io/2020-12-22-what-is-a-merkle-tree/"),
            docs("Bitcoin developer reference: Block chain", "https://developer.bitcoin.org/reference/block_chain.html"),
        ),
    ),
    Topic(
        "bc_keys_signatures", "Keys, Addresses & Signatures",
        "Proving ownership without a bank: public and private key pairs, addresses derived from public "
        "keys, and digital signatures that authorise transactions and can't be faked.",
        2,
        (
            video("Elliptic Curves (Computerphile)", "https://www.youtube.com/watch?v=NF1pwjL9-DE"),
            docs("ethereum.org: Ethereum accounts", "https://ethereum.org/developers/docs/accounts/"),
            docs("Bitcoin developer guide: Transactions", "https://developer.bitcoin.org/devguide/transactions.html"),
        ),
    ),
    Topic(
        "bc_p2p_networks", "Nodes & Peer-to-Peer Networks",
        "How a blockchain runs without a central server: nodes that store and check the chain, full and "
        "light nodes, and how transactions and blocks spread from peer to peer.",
        2,
        (
            docs("ethereum.org: Nodes and clients", "https://ethereum.org/developers/docs/nodes-and-clients/"),
            docs("ethereum.org: Networking layer", "https://ethereum.org/developers/docs/networking-layer/"),
            docs("Bitcoin developer guide: P2P network", "https://developer.bitcoin.org/devguide/p2p_network.html"),
        ),
    ),
    Topic(
        "bc_use_cases", "Uses, Limits & Risks",
        "When a blockchain helps and when an ordinary database is better: payments, provenance and "
        "shared records, the costs of irreversibility and energy use, common scams, and regulation.",
        2,
        (
            docs("NIST IR 8202: Blockchain technology overview", "https://csrc.nist.gov/pubs/ir/8202/final"),
            docs("ESMA: Markets in Crypto-Assets Regulation (MiCA)", "https://www.esma.europa.eu/esmas-activities/digital-finance-and-innovation/markets-crypto-assets-regulation-mica"),
        ),
    ),
    Topic(
        "bc_wallets", "Wallets & Key Safety",
        "What a wallet really holds: custodial and self-custody wallets, seed phrases and hardware "
        "wallets, why a lost key can't be recovered, and spotting phishing and wallet-draining scams.",
        3,
        (
            article("ethereum.org: Ethereum wallets explained", "https://ethereum.org/wallets/"),
            article("ethereum.org: Security and scam prevention", "https://ethereum.org/security/"),
            article("bitcoin.org: Securing your wallet", "https://bitcoin.org/en/secure-your-wallet"),
        ),
    ),
    Topic(
        "bc_consensus", "Consensus: Proof of Work & Proof of Stake",
        "How strangers agree on one history: mining and difficulty in proof of work, validators and "
        "staking in proof of stake, forks, finality, and why a 51% attack is expensive.",
        3,
        (
            docs("ethereum.org: Consensus mechanisms", "https://ethereum.org/developers/docs/consensus-mechanisms/"),
            docs("ethereum.org: Proof of work", "https://ethereum.org/developers/docs/consensus-mechanisms/pow/"),
            docs("ethereum.org: Proof of stake", "https://ethereum.org/developers/docs/consensus-mechanisms/pos/"),
        ),
    ),
    Topic(
        "bc_bitcoin", "How Bitcoin Works",
        "Bitcoin from end to end: transactions that spend unspent outputs (UTXOs), the mempool and "
        "fees, mining a block, confirmations, and the fixed supply schedule.",
        3,
        (
            video("But how does bitcoin actually work? (3Blue1Brown)", "https://www.youtube.com/watch?v=bBC-nXj3Ng4"),
            article("Satoshi Nakamoto: Bitcoin whitepaper", "https://bitcoin.org/bitcoin.pdf"),
            docs("Bitcoin developer guide: Block chain", "https://developer.bitcoin.org/devguide/block_chain.html"),
        ),
    ),
    Topic(
        "bc_ethereum", "Ethereum & the EVM",
        "A blockchain that runs programs: accounts and contract accounts, the Ethereum Virtual Machine, "
        "transactions that change shared state, and gas as the price of computation.",
        3,
        (
            docs("ethereum.org: Technical intro to Ethereum", "https://ethereum.org/developers/docs/intro-to-ethereum/"),
            docs("ethereum.org: Ethereum Virtual Machine", "https://ethereum.org/developers/docs/evm/"),
            docs("ethereum.org: Gas and fees", "https://ethereum.org/developers/docs/gas/"),
        ),
    ),
    # --- Building on Ethereum -----------------------------------------------------------------
    Topic(
        "bc_smart_contracts", "Smart Contracts",
        "Programs stored on a blockchain: deterministic code that anyone can call, state kept on chain, "
        "why deployed code can't simply be edited, and what contracts can't do on their own.",
        3,
        (
            docs("ethereum.org: Introduction to smart contracts", "https://ethereum.org/developers/docs/smart-contracts/"),
            docs("Solidity docs: Introduction to smart contracts", "https://docs.soliditylang.org/en/latest/introduction-to-smart-contracts.html"),
        ),
    ),
    Topic(
        "bc_solidity", "Solidity Basics",
        "Writing Ethereum contracts: state variables and types, functions and visibility, mappings, "
        "msg.sender and msg.value, modifiers, events, and require for checking inputs.",
        3,
        (
            video("Solidity in 100 Seconds (Fireship)", "https://www.youtube.com/watch?v=kdvVwGrV7ec"),
            docs("Solidity documentation", "https://docs.soliditylang.org/en/latest/"),
            article("Solidity by Example", "https://solidity-by-example.org/"),
        ),
    ),
    Topic(
        "bc_dev_tools", "Developing & Testing Contracts",
        "The contract developer's toolkit: frameworks such as Hardhat and Foundry, local development "
        "chains, automated tests, test networks, and deploying a contract.",
        4,
        (
            docs("Hardhat: Getting started", "https://hardhat.org/docs/getting-started"),
            docs("Foundry documentation", "https://www.getfoundry.sh/"),
            docs("ethereum.org: Development networks", "https://ethereum.org/developers/docs/development-networks/"),
        ),
    ),
    Topic(
        "bc_tokens", "Tokens & Standards (ERC-20, ERC-721)",
        "How tokens are just contracts: fungible ERC-20 tokens with balances, transfers and allowances, "
        "non-fungible ERC-721 tokens, and building on audited libraries such as OpenZeppelin.",
        4,
        (
            docs("ethereum.org: ERC-20 token standard", "https://ethereum.org/developers/docs/standards/tokens/erc-20/"),
            docs("ethereum.org: ERC-721 non-fungible token standard", "https://ethereum.org/developers/docs/standards/tokens/erc-721/"),
            docs("OpenZeppelin docs: Tokens", "https://docs.openzeppelin.com/contracts/5.x/tokens"),
        ),
    ),
    Topic(
        "bc_contract_security", "Smart Contract Security",
        "Defending code that holds value: reentrancy and checks-effects-interactions, access control, "
        "unchecked calls, front-running, careful upgrades, testing and independent audits.",
        4,
        (
            docs("ethereum.org: Smart contract security", "https://ethereum.org/developers/docs/smart-contracts/security/"),
            docs("Solidity docs: Security considerations", "https://docs.soliditylang.org/en/latest/security-considerations.html"),
            article("OWASP Smart Contract Top 10", "https://owasp.org/projects/smart-contract-top-10"),
        ),
    ),
    Topic(
        "bc_dapps", "Decentralised Apps (dApps)",
        "Connecting a web front end to contracts: wallet connections, reading contract data, sending "
        "transactions the user signs, listening for events, and libraries such as viem.",
        4,
        (
            docs("ethereum.org: Technical introduction to dapps", "https://ethereum.org/developers/docs/dapps/"),
            docs("viem documentation", "https://viem.sh/"),
        ),
    ),
    Topic(
        "bc_oracles_storage", "Oracles & Off-Chain Data",
        "Getting real-world data in and large files out: why contracts can't fetch data themselves, "
        "oracles and their trust problem, and content-addressed storage such as IPFS.",
        4,
        (
            docs("ethereum.org: Oracles", "https://ethereum.org/developers/docs/oracles/"),
            docs("IPFS docs: What is IPFS?", "https://docs.ipfs.tech/concepts/what-is-ipfs/"),
            docs("ethereum.org: Decentralized storage", "https://ethereum.org/developers/docs/storage/"),
        ),
    ),
    Topic(
        "bc_defi", "DeFi Concepts",
        "How decentralised finance works under the hood: stablecoins, automated market makers and the "
        "constant-product formula, lending with collateral, and the technical risks involved.",
        4,
        (
            article("ethereum.org: What is DeFi?", "https://ethereum.org/defi/"),
            docs("Uniswap docs: How Uniswap works", "https://developers.uniswap.org/docs/get-started/concepts/how-uniswap-works"),
            article("ethereum.org: Stablecoins explained", "https://ethereum.org/stablecoins/"),
        ),
    ),
    Topic(
        "bc_scaling", "Scaling & Layer 2",
        "Handling more transactions: the scalability trade-off, layer 2 rollups (optimistic and "
        "zero-knowledge) that post data back to the main chain, sidechains and payment channels.",
        4,
        (
            docs("ethereum.org: Scaling", "https://ethereum.org/developers/docs/scaling/"),
            docs("ethereum.org: Optimistic rollups", "https://ethereum.org/developers/docs/scaling/optimistic-rollups/"),
            docs("ethereum.org: Zero-knowledge rollups", "https://ethereum.org/developers/docs/scaling/zk-rollups/"),
        ),
    ),
)

PREREQUISITES: tuple[tuple[str, str], ...] = (
    ("bc_what_is_blockchain", "bc_hash_functions"),
    ("binary_data_representation", "bc_hash_functions"),
    ("bc_hash_functions", "bc_keys_signatures"),
    ("bc_what_is_blockchain", "bc_p2p_networks"),
    ("how_the_internet_works", "bc_p2p_networks"),
    ("bc_what_is_blockchain", "bc_use_cases"),
    ("bc_keys_signatures", "bc_wallets"),
    ("security_basics", "bc_wallets"),
    ("bc_hash_functions", "bc_consensus"),
    ("bc_p2p_networks", "bc_consensus"),
    ("bc_consensus", "bc_bitcoin"),
    ("bc_keys_signatures", "bc_bitcoin"),
    ("bc_consensus", "bc_ethereum"),
    ("bc_keys_signatures", "bc_ethereum"),

    ("bc_ethereum", "bc_smart_contracts"),
    ("programming_concepts", "bc_smart_contracts"),
    ("bc_smart_contracts", "bc_solidity"),
    ("bc_solidity", "bc_dev_tools"),
    ("bc_solidity", "bc_tokens"),
    ("bc_solidity", "bc_contract_security"),
    ("bc_smart_contracts", "bc_dapps"),
    ("bc_wallets", "bc_dapps"),
    ("async_javascript", "bc_dapps"),
    ("bc_smart_contracts", "bc_oracles_storage"),
    ("bc_tokens", "bc_defi"),
    ("bc_contract_security", "bc_defi"),
    ("bc_ethereum", "bc_scaling"),
)

BLOCKCHAIN = Domain(
    id="blockchain",
    name="Blockchain & Web3",
    description=(
        "How blockchains work and how to build on them: hashes, keys and consensus, Bitcoin and "
        "Ethereum, smart contracts in Solidity, tokens, contract security and decentralised apps."
    ),
    topics=TOPICS,
    prerequisites=PREREQUISITES,
)
