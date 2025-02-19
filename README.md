# BSV Network Setup Guide

This repository contains configuration and setup instructions for a 5-node Bitcoin SV network with mainnet-like settings.

## Network Architecture

- 3 Local nodes (Docker containers)
- 2 Remote nodes (AWS EC2 instances)
- Network Mode: Mainnet (regtest=0, testnet=0)
- Initial Difficulty: 1.0

## Prerequisites

- Docker and Docker Compose
- AWS Account with EC2 access
- Ubuntu 20.04 or later

## Node Configuration

### Local Nodes (1-3)
```yaml
# docker-compose.yml
version: '3.7'
services:
  node1:
    image: bitcoinsv/bitcoin-sv:1.0.8.beta
    ports:
      - "18332:18332"
      - "18333:18333"
      - "28332:28332"

  node2:
    image: bitcoinsv/bitcoin-sv:1.0.8.beta
    ports:
      - "18501:18333"
      - "18502:18332"

  node3:
    image: bitcoinsv/bitcoin-sv:1.0.8.beta
    ports:
      - "18601:18333"
      - "18602:18332"
```

### Remote Nodes (4-5)
- AWS EC2 t2.micro instances
- Ubuntu 20.04
- Security Group Configuration:
  - TCP ports: 18332-18333, 28332

## Configuration Files

### bitcoin.conf (Base Configuration)
```ini
server=1
wallet=1
disablewallet=0
rest=1
listen=1
regtest=0
testnet=0
txindex=1
dnsseed=0
upnp=1

rpcport=18332
port=18333
rpcuser=bitcoin
rpcpassword=bitcoin
rpcallowip=0.0.0.0/0
rpcbind=0.0.0.0

excessiveblocksize=2000000000
maxblocksize=2000000000
maxmineblocksize=128000000
maxstackmemoryusageconsensus=200000000
```

## Setup Instructions

1. Local Nodes Setup:
```bash
# Clone repository
git clone https://github.com/space0org/BTC-Network.git
cd BTC-Network

# Start local nodes
docker-compose up -d
```

2. Remote Node Setup:
```bash
# On AWS EC2 instances
docker run -d \
  --name node4 \
  -p 18332:18332 \
  -p 18333:18333 \
  -p 28332:28332 \
  -v $(pwd)/bitcoin.conf:/data/bitcoin.conf \
  bitcoinsv/bitcoin-sv:1.0.8.beta
```

3. Network Verification:
```bash
# Check node status
bitcoin-cli -rpcuser=bitcoin -rpcpassword=bitcoin getinfo

# Check peer connections
bitcoin-cli -rpcuser=bitcoin -rpcpassword=bitcoin getpeerinfo
```

## Network Details

- Protocol Version: 70015
- RPC Credentials: bitcoin/bitcoin
- Default Ports: 18332-18333, 28332

## Mining Configuration

The network is configured for competitive mining with:
- Initial difficulty: 1.0
- All nodes participating in mining
- Natural difficulty adjustment based on block times

## Maintenance

To reset to genesis block:
1. Stop all nodes
2. Clear blockchain data
3. Restart nodes with updated configuration

## Security Considerations

- RPC access is restricted by credentials
- Network connections are authenticated
- Firewall rules control access to ports

## Troubleshooting

1. Connection Issues:
   - Verify security group settings
   - Check node connectivity
   - Ensure correct port forwarding

2. Mining Issues:
   - Verify difficulty settings
   - Check node synchronization
   - Monitor hash power distribution

## License

This project is licensed under the MIT License - see the LICENSE file for details.
