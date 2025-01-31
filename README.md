# **OrderBook Project**

This repository is designed to work with multiple exchanges like **OKX** and **HTX** using different WebSocket libraries. It allows strategies to interact with exchanges, test Redis clients/servers, and run custom logic for trading strategies.

---

## **Table of Contents**

- [Project Overview](#project-overview)
- [Setup & Installation](#setup--installation)
- [Folder Structure](#folder-structure)
- [Running the Application](#running-the-application)
- [How to Add Strategies](#how-to-add-strategies)
- [Testing Redis](#testing-redis)
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

# Create virtual environment for OKX
**virtualenv /environments/okx/**
**source /environments/okx/bin/activate**

# Create virtual environment for HTX
virtualenv /environments/venv
source /environments/okx/bin/activate


### 1b. Install Required Libraries

#### Install dependencies for OKX
pip install -r okx/requirements.txt

#### Install dependencies for HTX
pip install -r htx/requirements.txt

### 1c. Enter Project Directory
cd /var/www/html/orderbook

## **Folder Structure**

### 2. Folder Structure

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




# <!-- Understanding files -->
1) okx folder is for okx library
2) htx folder is for htx library
3) okx2 and htx2 folders are customised codes adapted from okx and htx to accomodate specific requirements
4) redis_channel folder is to test redis client and server
5) strategies folder is to add strategies


