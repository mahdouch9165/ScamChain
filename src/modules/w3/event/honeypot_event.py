from .event import Event

class HoneypotEvent(Event):
    def __init__(self, token, logger):
        super().__init__()
        self.token = token
        self.logger = logger
        
        # Pair object is set externally (e.g., in honeypot_timer_flow_base_uniswap_v2)
        self.pair = None
        
        # Security findings
        self.bad_functions = []
        self.bad_lines = []
        
        # Transaction/flow details
        self.successful_buy_hashes = []
        self.failed_buy_hashes = []
        self.successful_sell_hashes = []
        self.failed_sell_hashes = []
        
        self.buy_slippage = None
        self.sell_slippage = None
        self.amount_in = 0.0
        self.amount_out = 0.0
        self.profit = 0.0
        self.yield_percent = 0.0
        
        self.wait_time_minutes = 0
        self.wait_time_seconds = 0
        
        # You can track success/failure states
        self.LLM_can_sell = None
        self.short_term_outcome = None
        self.fail_reason = None
        
        # Liquidity (set in your flow)
        self.initial_liquidity = 0

        # Transaction details
        self.account_value_pre_transaction = 0
        self.account_value_post_transaction = 0

        self.pre_transaction_observation_timestamp = 0
        self.post_transaction_observation_timestamp = 0
        self.buy_gas_used = 0
        self.amount_in_raw = 0
        self.amount_out_raw = 0
        self.sell_gas_used = 0
        self.can_sell = None
        self.long_term_outcome = None
        self.max_profit_time = None
        self.rug_pull_time = None
        self.max_yield_percent = None

    def to_dict(self):
        return {
            'token': self.token.to_dict(),
            'pair': self.pair.to_dict(),
            'bad_functions': self.bad_functions,
            'bad_lines': self.bad_lines,
            'successful_buy_hashes': self.successful_buy_hashes,
            'failed_buy_hashes': self.failed_buy_hashes,
            'successful_sell_hashes': self.successful_sell_hashes,
            'failed_sell_hashes': self.failed_sell_hashes,
            'buy_slippage': self.buy_slippage,
            'sell_slippage': self.sell_slippage,
            'amount_in': self.amount_in,
            'amount_out': self.amount_out,
            'profit': self.profit,
            'yield_percent': self.yield_percent,
            'wait_time_minutes': self.wait_time_minutes,
            'wait_time_seconds': self.wait_time_seconds,
            'LLM_can_sell': self.LLM_can_sell,
            'short_term_outcome': self.short_term_outcome,
            'fail_reason': self.fail_reason,
            'initial_liquidity': self.initial_liquidity,
            'account_value_pre_transaction': self.account_value_pre_transaction,
            'account_value_post_transaction': self.account_value_post_transaction,
            'pre_transaction_observation_timestamp': self.pre_transaction_observation_timestamp,
            'post_transaction_observation_timestamp': self.post_transaction_observation_timestamp,
            'buy_gas_used': self.buy_gas_used,
            'amount_in_raw': self.amount_in_raw,
            'amount_out_raw': self.amount_out_raw,
            'sell_gas_used': self.sell_gas_used,
            'can_sell': self.can_sell,
            'long_term_outcome': self.long_term_outcome,
            'max_profit_time': self.max_profit_time,
            'rug_pull_time': self.rug_pull_time,
            'max_yield_percent': self.max_yield_percent
        }