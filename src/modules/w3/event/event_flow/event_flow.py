import logging
import os
from ...exchange.token.token import Token
from ...exchange.pair.pair import Pair
from ...exchange.exchange import to_base_units, from_base_units
from ..event import Event
from ..security.security_manager import *
from ..llm.llm_manager import LLMManager
from decimal import Decimal, getcontext
import time
import json

getcontext().prec = 28


class EventFlow:
    def __init__(self, w3, scanner, exchange, account):
        self.w3 = w3
        self.scanner = scanner
        self.exchange = exchange
        self.account = account

    def handle_event(self, event_data):
        raise NotImplementedError
    
    def setup_logs(self):
        raise NotImplementedError