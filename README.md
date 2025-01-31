# **OrderBook Project**

This repository is designed to work with multiple exchanges like **OKX** and **HTX** using different WebSocket libraries. It allows strategies to interact with exchanges, test Redis clients/servers, and run custom logic for trading strategies.

---

## **Table of Contents**

- [Project Overview](#project-overview)
- [Setup & Installation](#setup--installation)
- [Folder Structure](#folder-structure)
- [Running the Application](#running-the-application)
- [License](#license)

---

## **Project Overview**

This project supports running multiple exchanges, each having their own set of **WebSocket libraries**. To avoid conflicts, we use **virtual environments** for each exchange. The setup includes directories for:

- **OKX** library (`okx`)
- **HTX** library (`htx`)
- Customized versions (`okx2`, `htx2`) to support specific requirements
- **Redis channel** to test client-server communication
- **Strategies** folder for custom trading strategies

---

## **Setup & Installation**

### 1. **Create Virtual Environments**

To isolate dependencies and avoid conflicts between libraries (especially the WebSocket libraries used by different exchanges), create virtual environments for each exchange:

#### Create virtual environment for OKX
```bash
virtualenv /environments/okx/
source /environments/okx/bin/activate
```

#### Create virtual environment for HTX
```bash
virtualenv /environments/venv
source /environments/okx/bin/activate
```


### 2. Install Required Libraries

#### Install dependencies for OKX
```bash
pip install -r okx/requirements.txt
```

#### Install dependencies for HTX
```bash
pip install -r htx/requirements.txt
```

### 3. Enter Project Directory
```bash
cd /var/www/html/orderbook
```

## **Folder Structure**

```plaintext
orderbook/
├── okx/                    # OKX exchange WebSocket library
├── htx/                    # HTX exchange WebSocket library
├── okx2/                   # Customized OKX WebSocket library for specific requirements
├── htx2/                   # Customized HTX WebSocket library for specific requirements
├── redis_channel/          # Test Redis client-server communication
├── strategies/             # Custom trading strategies
├── requirements.txt        # Common dependencies for the project
└── README.md               # This file
```
## **Running the Application**
```bash
bash start_auth_server.sh
bash start_redis_connector.sh
bash start_display_engine.sh
bash start_trading_engine.sh
bash start_algo_engine.sh
```

## **License**
Custom License

Copyright (c) [2025] [Brennan Sze To]

1. This code is licensed for use only by Brennan Sze To.
2. No part of this code may be copied, modified, distributed, or sold without explicit written permission from [your company].
3. This code is not to be shared with third parties or made public in any form.
4. No reverse engineering, decompilation, or disassembly is allowed.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.



