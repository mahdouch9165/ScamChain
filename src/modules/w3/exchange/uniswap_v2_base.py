from .exchange import *

class UniswapV2Base(Exchange):
    def __init__(self, w3: W3Connector, scanner: ChainScanner):
        super().__init__()
        # Uniswap V2 addresses
        self.name = "Uniswap V2"
        self.chain = "Base"
        self.factory_address = w3.to_checksum_address("0x8909Dc15e40173Ff4699343b6eB8132c65e18eC6")
        self.approval_address = w3.to_checksum_address("0x000000000022D473030F116dDEE9F6B43aC78BA3")
        self.router_address = w3.to_checksum_address("0x4752ba5dbc23f44d87826276bf6fd6b1c372ad24")
        self.factory_abi = scanner.get_contract_abi(self.factory_address)
        self.approval_abi = scanner.get_contract_abi(self.approval_address)
        self.router_abi = scanner.get_contract_abi(self.router_address)
        self.factory_contract = w3.get_contract_instance(self.factory_address, self.factory_abi)
        self.approval_contract = w3.get_contract_instance(self.approval_address, self.approval_abi)
        self.router_contract = w3.get_contract_instance(self.router_address, self.router_abi)                

    def get_pair_address(self, token0, token1):
        token0_address = token0.address
        token1_address = token1.address
        return self.factory_contract.functions.getPair(token0_address, token1_address).call()
    
    def get_price(self, token_0, token_1, pair):
        pair_address = pair.pair_address
        if pair_address == '0x0000000000000000000000000000000000000000':
            return None

        # 1) Match up which reserve corresponds to token_0 and token_1
        token0_address = token_0.address.lower()
        token1_address = token_1.address.lower()
        pair_token0_address = pair.token_0.address.lower()
        pair_token1_address = pair.token_1.address.lower()
        
        reserves = pair.get_reserves()  # e.g. [res0, res1, timestamp]
        
        if token0_address == pair_token0_address:
            token0_reserve = reserves[0]
            token1_reserve = reserves[1]
        else:
            token0_reserve = reserves[1]
            token1_reserve = reserves[0]

        # 2) Normalize each reserve by the token's decimals
        adjusted_reserve0 = token0_reserve / (10 ** token_0.decimals)
        adjusted_reserve1 = token1_reserve / (10 ** token_1.decimals)

        # 3) Return price of token_0 in terms of token_1
        # "How many token_1 do I get per 1 token_0?"
        if adjusted_reserve0 == 0:
            return None
        
        return adjusted_reserve1 / adjusted_reserve0

    def get_liquidity(self, pair):
        reserves = pair.get_reserves()
        token0 = pair.token_0
        token1 = pair.token_1
        dec0 = token0.decimals
        dec1 = token1.decimals

        return {
            token0.address: reserves[0] / 10**dec0,
            token1.address: reserves[1] / 10**dec1
        }

    def swap_tokens(
            self,
            w3,
            account,
            from_token,
            to_token,
            event,
            amount_in_tokens: Decimal = None,  # If None => use entire balance
            slippage_tolerance: Decimal = Decimal('0.01'),
            gas_limit_approve: int = 200_000,
            gas_limit_swap: int = 350_000,
            gas_speed: str = "low"  # "low", "medium", or "high"
        ):
            """
            Swaps from `from_token_address` to `to_token_address` using Uniswap (or similar),
            returning details about gas usage and transaction hashes, with gas costs in ETH.
            Uses EIP-1559 fields from Infura's Gas API instead of legacy gasPrice.
            """
            
            # Load the contract instances
            from_token_contract = from_token.contract
            to_token_contract = to_token.contract

            # 1. Fetch EIP-1559 gas parameters from Infura
            gas_settings = w3.fetch_gas_price(level=gas_speed)
            maxFeePerGas = gas_settings["maxFeePerGas"]
            maxPriorityFeePerGas = gas_settings["maxPriorityFeePerGas"]

            # 2. Fetch decimals and balances
            from_decimals = from_token.decimals
            to_decimals = to_token.decimals

            # Current balance in raw base units (integer)
            from_token_balance_raw = from_token_contract.functions.balanceOf(account.address).call()
            from_token_balance = from_base_units(from_token_balance_raw, from_decimals)

            # Before-swap "to" token balance (we'll use this for calculating actual amount out)
            initial_to_balance_raw = to_token_contract.functions.balanceOf(account.address).call()

            # 3. Determine amount_in_raw
            if amount_in_tokens is None:
                # Use the full balance minus 1 wei to avoid rounding off-by-1 issues
                margin_wei = 1
                if from_token_balance_raw <= margin_wei:
                    amount_in_raw = from_token_balance_raw  # fallback if balance is very small
                else:
                    amount_in_raw = from_token_balance_raw - margin_wei
                amount_in_tokens = from_base_units(amount_in_raw, from_decimals)  # for logging
            else:
                amount_in_raw = to_base_units(amount_in_tokens, from_decimals)

            # Check if user has enough balance
            if amount_in_raw > from_token_balance_raw:
                error_msg = (
                    f"Insufficient {from_token.address} balance. "
                    f"Needed: {amount_in_tokens}, Have: {from_token_balance}"
                )
                event.logger.error(error_msg)
                raise ValueError(error_msg)

            # 4. Check allowance
            current_allowance_raw = from_token_contract.functions.allowance(account.address, self.router_address).call()

            approval_receipt = None
            approval_tx_hash = None
            approval_gas_cost_eth = Decimal('0')

            # 5. Approve (if needed)
            if current_allowance_raw < amount_in_raw:
                try:
                    approve_tx = from_token_contract.functions.approve(
                        self.router_address,
                        2**256 - 1  # max uint256
                    ).build_transaction({
                        "from": account.address,
                        "nonce": w3.get_transaction_count(account.address),
                        "gas": gas_limit_approve,
                        "maxFeePerGas": maxFeePerGas,
                        "maxPriorityFeePerGas": maxPriorityFeePerGas
                    })

                    signed_approve_tx = w3.sign_transaction(approve_tx, private_key=account.key)
                    approval_tx_hash = w3.send_raw_transaction(signed_approve_tx.raw_transaction)
                    approval_receipt = w3.wait_for_transaction_receipt(approval_tx_hash)

                    # Log approval details
                    event.logger.info(f"Approval tx hash: {w3.to_hex(approval_tx_hash)}")
                    event.logger.info(f"Approval status: {'Success' if approval_receipt.status == 1 else 'Failed'}")

                    if approval_receipt.status != 1:
                        error_msg = "Approval transaction failed, aborting swap."
                        event.logger.error(error_msg)
                        raise Exception(error_msg)

                    # Calculate approval gas cost in ETH, using effectiveGasPrice
                    # (the actual gas price paid in the block)
                    approval_gas_cost_wei = approval_receipt.gasUsed * approval_receipt.effectiveGasPrice
                    approval_gas_cost_eth = Decimal(approval_gas_cost_wei) / Decimal(10**18)
                    event.logger.info(f"Approval gas cost: {approval_gas_cost_eth} ETH")

                except Exception as e:
                    event.logger.error(f"Error during token approval: {str(e)}")
                    raise

            # 6. Prepare swap: get quote & slippage
            try:
                path = [from_token.address, to_token.address]
                amounts_out_raw = self.router_contract.functions.getAmountsOut(amount_in_raw, path).call()
                estimated_out_raw = amounts_out_raw[-1]
                estimated_out = from_base_units(estimated_out_raw, to_decimals)
                min_amount_out_raw = int(Decimal(estimated_out_raw) * (Decimal('1') - slippage_tolerance))
            except Exception as e:
                event.logger.error(f"Error fetching amounts out: {str(e)}")
                raise

            # 7. Build swap transaction
            try:
                swap_tx = self.router_contract.functions.swapExactTokensForTokens(
                    amount_in_raw,
                    min_amount_out_raw,
                    path,
                    account.address,
                    int(time.time()) + 180  # 3-minute deadline
                ).build_transaction({
                    "from": account.address,
                    "nonce": w3.get_transaction_count(account.address),
                    "gas": gas_limit_swap,
                    "maxFeePerGas": maxFeePerGas,
                    "maxPriorityFeePerGas": maxPriorityFeePerGas
                })
            except Exception as e:
                event.logger.error(f"Error building swap transaction: {str(e)}")
                raise

            # 8. Sign & send swap transaction
            swap_receipt = None
            swap_tx_hash = None
            swap_gas_cost_eth = Decimal('0')
            try:
                signed_swap_tx = w3.sign_transaction(swap_tx, private_key=account.key)
                swap_tx_hash = w3.send_raw_transaction(signed_swap_tx.raw_transaction)
                swap_receipt = w3.wait_for_transaction_receipt(swap_tx_hash)

                # Log swap details
                event.logger.info(f"Swap tx hash: {w3.to_hex(swap_tx_hash)}")
                event.logger.info(f"Swap status: {'Success' if swap_receipt.status == 1 else 'Failed'}")

                # Calculate swap gas cost in ETH, using effectiveGasPrice
                swap_gas_cost_wei = swap_receipt.gasUsed * swap_receipt.effectiveGasPrice
                swap_gas_cost_eth = Decimal(swap_gas_cost_wei) / Decimal(10**18)

            except Exception as e:
                event.logger.error(f"Error during swap transaction: {str(e)}")
                raise

            # 9. Gather final info
            try:
                final_to_balance_raw = to_token_contract.functions.balanceOf(account.address).call()
                actual_amount_out_raw = final_to_balance_raw - initial_to_balance_raw
                actual_amount_out = from_base_units(actual_amount_out_raw, to_decimals)
            except Exception as e:
                event.logger.error(f"Error fetching final token balance: {str(e)}")
                actual_amount_out = Decimal('0')  # Fallback value

            # Total gas cost for this swap (approval + swap)
            total_gas_cost_eth = approval_gas_cost_eth + swap_gas_cost_eth

            # Return swap info
            result = {
                "approval_tx_hash":      w3.to_hex(approval_tx_hash) if approval_tx_hash else None,
                "approval_gas_cost_eth": float(approval_gas_cost_eth),
                "swap_tx_hash":          w3.to_hex(swap_tx_hash),
                "swap_gas_cost_eth":     float(swap_gas_cost_eth),
                "swap_status":           swap_receipt.status if swap_receipt else None,
                "amount_out":            float(actual_amount_out),
                "total_gas_cost_eth":    float(total_gas_cost_eth)
            }

            return result

