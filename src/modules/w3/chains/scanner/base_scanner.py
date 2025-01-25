from .chain_scanner import *

load_dotenv()

BASE_SCAN_API_KEY = os.getenv("BASE_SCAN_API_KEY")

class BaseScanner(ChainScanner):
    def __init__(self):
        super().__init__()
        self.url = "https://api.basescan.org/api"
        self.api_key = BASE_SCAN_API_KEY
