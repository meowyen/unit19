import json
import os
import subprocess

from bit import PrivateKey, PrivateKeyTestnet
from bit.network import NetworkAPI
from dotenv import load_dotenv
from eth_account import Account
from web3 import Web3
from web3.middleware import geth_poa_middleware

from constants import *


class CryptoWallet:

    def __init__(self):
        """
        Initialize web3 and coins.
        """
        load_dotenv()
        mnemonic_phrase = os.getenv(
            "MNEMONIC", "soccer cousin badge snow chicken lamp soft note ugly crouch unfair biology symbol control heavy")

        # initialize w3
        self.w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
        # support PoA algorithm
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        self.coins = {}
        for coin in COINS:
            self.coins[coin] = self.derive_wallets(mnemonic_phrase, coin)

    def derive_wallets(self, mnemonic, coin, number_keys=10):
        """
        Derive wallets for a coin using mnemonic phrase.
        """
        command = f'derive -g --mnemonic="{mnemonic}" --coin={coin} --numderive={number_keys} --cols=path,address,privkey,pubkey --format=json'

        p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        output, err = p.communicate()
        p_status = p.wait()

        keys = json.loads(output)
        return keys

    def priv_key_to_account(self, coin, priv_key):
        """
        Return private key to account.
        """
        if coin is ETH:
            return Account.from_key(priv_key)
        elif coin is BTCTEST:
            return PrivateKeyTestnet(priv_key)
        elif coin is BTC:
            return PrivateKey(priv_key)
        else:
            return None

    def create_tx(self, coin, account, to, amount):
        """
        Return prepared transaction for coin and account.
        """
        if coin is ETH:
            gasEstimate = self.w3.eth.estimateGas(
                {"from": account.address, "to": to, "value": amount}
            )
            return {
                "from": account.address,
                "to": to,
                "value": self.w3.toWei(amount, 'ether'),
                "gasPrice": self.w3.eth.gasPrice,
                "gas": gasEstimate,
                "nonce": self.w3.eth.getTransactionCount(account.address),
            }
        elif coin is BTCTEST:
            return PrivateKeyTestnet.prepare_transaction(account.address, [(to, amount, BTC)])
        elif coin is BTC:
            return PrivateKey.prepare_transaction(account.address, [(to, amount, BTC)])
        else:
            return None

    def send_tx(self, coin, account, to, amount):
        """
        Send transaction.
        """
        raw_tx = self.create_tx(coin, account, to, amount)
        signed_tx = account.sign_transaction(raw_tx)

        if coin is ETH:
            return self.w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        elif coin is BTCTEST:
            return NetworkAPI.broadcast_tx_testnet(signed_tx)
        elif coin is BTC:
            return NetworkAPI.broadcast_tx(signed_tx)
        else:
            return None

    def get_coin_address(self, coin, idx=0):
        """
        Return coin addresses and keys.
        """
        return self.coins[coin][idx]

    def get_coin_privkey(self, coin, idx=0):
        """
        Return coin addresses and keys.
        """
        return self.get_coin_address(coin=coin, idx=idx)["privkey"]
