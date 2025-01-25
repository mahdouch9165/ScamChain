import time
import json
import psutil
import pandas as pd
import os
from dotenv import load_dotenv
from pathlib import Path
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box
from rich.console import Console
from rich.progress import Progress
from rich.style import Style
from collections import deque
from typing import Dict, List, Any, Generator, Optional

# Import your chain/wallet/exchange modules:
# (Adjust these imports as necessary based on your folder structure)
from src.modules.w3.chains.official_base import OfficialBaseChain
from src.modules.w3.w3_connector import W3Connector
from src.modules.w3.wallet.wallet import Wallet
from src.modules.w3.exchange.token.token import Token
from src.modules.w3.exchange.pair.pair import Pair
from src.modules.w3.chains.scanner.base_scanner import BaseScanner
from src.modules.w3.exchange.uniswap_v2_base import UniswapV2Base

load_dotenv()

class HoneypotDashboard:
    """
    A refactored Honeypot Dashboard with:
    - Real-time monitoring
    - System metrics
    - Performance tracking
    - Recent transactions
    - Log monitoring
    """

    def __init__(self):
        # Directories for data/log storage
        self.data_dir = Path("data/honeypot_timer_flow")
        self.log_dir = Path("logs/honeypot_timer_flow")
        self.max_events = 20  # for recent events
        self.event_history = deque(maxlen=self.max_events)

        # Initialize empty DataFrame for historical data
        self.df = pd.DataFrame()

        # Keep track of already-loaded files to avoid re-reading them
        self.loaded_files = set()

        # Load environment variables
        load_dotenv()
        self.initial_account_value = 0.0

        # Initialize W3/chain
        self.chain = OfficialBaseChain()     # Adapt based on your actual chain class
        self.w3 = W3Connector(self.chain)
        self.wallet = Wallet(mnemonic=os.getenv("MNEMONIC"))
        self.scanner = BaseScanner()
        self.exchange = UniswapV2Base(self.w3, self.scanner)

        # Initialize tokens/pairs for the reference price
        self.weth = Token(
            self.w3.to_checksum_address("0x4200000000000000000000000000000000000006"),
            self.w3,
            self.scanner
        )
        self.usdc = Token(
            self.w3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"),
            self.w3,
            self.scanner
        )
        self.weth_usdc_pair = Pair(self.weth, self.usdc, self.w3, self.scanner, self.exchange)

        # Initial data load
        self.load_historical_data_incrementally(first_load=True)
        if not self.df.empty:
            self.initial_account_value = self.df["account_value"].iloc[0]

    def load_historical_data_incrementally(self, first_load: bool = False) -> None:
        """Loads new JSON data files incrementally"""
        if not self.data_dir.is_dir():
            return

        new_rows = []
        for file_path in sorted(self.data_dir.glob("*.json"), key=lambda x: x.stat().st_mtime):
            if file_path.name in self.loaded_files:
                continue

            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
            except Exception:
                continue

            try:
                new_rows.extend([
                    {
                        "token_address": data["token"]["address"],
                        "timestamp": data["pre_transaction_observation_timestamp"],
                        "account_value": data["account_value_pre_transaction"],
                        "yield_percent": data.get("yield_percent", 0),
                        "can_sell": len(data["successful_sell_hashes"]) > 0,
                        "wait_time": data["wait_time_minutes"],
                        "open_source": data["token"]["open_source"]
                    },
                    {
                        "token_address": data["token"]["address"],
                        "timestamp": data["post_transaction_observation_timestamp"],
                        "account_value": data["account_value_post_transaction"],
                        "yield_percent": data.get("yield_percent", 0),
                        "can_sell": len(data["successful_sell_hashes"]) > 0,
                        "wait_time": data["wait_time_minutes"],
                        "open_source": data["token"]["open_source"]
                    }
                ])
            except KeyError:
                continue

            self.loaded_files.add(file_path.name)

        if not new_rows:
            return

        new_df = pd.DataFrame(new_rows)
        if new_df.empty:
            return

        new_df.sort_values("timestamp", inplace=True)
        self.df = pd.concat([self.df, new_df], ignore_index=True) if not self.df.empty else new_df
        self.df.sort_values("timestamp", inplace=True, ignore_index=True)

        if first_load and not self.df.empty:
            self.initial_account_value = self.df["account_value"].iloc[0]

    def get_total_eth_balance(self) -> float:
        """Returns total ETH balance (native + WETH)"""
        eth_balance = self.w3.get_eth_balance(self.wallet.address)
        weth_balance = self.weth.get_balance(self.wallet.address)
        return eth_balance + weth_balance

    def get_system_metrics(self) -> Dict[str, float]:
        """Returns system and performance metrics"""
        current_value = self.get_total_eth_balance()
        weth_usdc_price = self.exchange.get_price(self.weth, self.usdc, self.weth_usdc_pair) or 0.0

        if self.df.empty:
            return {
                "cpu": psutil.cpu_percent(),
                "mem": psutil.virtual_memory().percent,
                "eth_balance": current_value,
                "processed": 0,
                "profit_eth": 0.0,
                "profit_usd": 0.0,
                "success_rate": 0.0,
                "avg_yield": 0.0,
                "open_source_ratio": 0.0,
                "avg_wait": 0.0,
            }

        profit_eth = current_value - self.initial_account_value
        profit_usd = profit_eth * weth_usdc_price

        return {
            "cpu": psutil.cpu_percent(),
            "mem": psutil.virtual_memory().percent,
            "eth_balance": current_value,
            "processed": len(self.df) // 2,
            "profit_eth": profit_eth,
            "profit_usd": profit_usd,
            "success_rate": self.df["can_sell"].mean(),
            "avg_yield": self.df["yield_percent"].mean(),
            "open_source_ratio": self.df["open_source"].mean(),
            "avg_wait": self.df["wait_time"].mean(),
        }

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Returns recent events as a list of dictionaries for flexible formatting.
        We return more data so we can colorize based on yield, etc.
        """
        if self.df.empty:
            return []
        
        grouped_df = self.df.groupby("token_address").max()
        # reset_index() is needed to convert the groupby object back to a DataFrame
        grouped_df = grouped_df.reset_index()

        last_rows = grouped_df.sort_values("timestamp", ascending=False).head(limit)
        events = []
        for _, row in last_rows.iterrows():
            events.append({
                "token_address": row["token_address"],
                "yield_percent": row["yield_percent"],
                "can_sell": row["can_sell"],
                "timestamp": row["timestamp"]
            })
        return events

    def _build_header_panel(self, metrics: Dict[str, float]) -> Panel:
        """Builds the header panel"""
        return Panel(
            Text(
                f"🐝 Honeypot Monitor | ETH: {metrics['eth_balance']:.4f} | "
                f"Profit: {metrics['profit_eth']:.4f} ETH (${metrics['profit_usd']:.2f})",
                style="bold blue"
            ),
            style="on black",
            box=box.SQUARE
        )

    def _build_system_metrics_panel(self, metrics: Dict[str, float]) -> Panel:
        """Builds system metrics panel"""
        table = Table(show_header=False, box=None)
        table.add_row("CPU Usage", f"{metrics['cpu']:.1f}%")
        table.add_row("Memory Usage", f"{metrics['mem']:.1f}%")
        table.add_row("Processed Events", str(metrics["processed"]))
        table.add_row("Success Rate", f"{metrics['success_rate']:.1%}")
        table.add_row("Open Source Ratio", f"{metrics['open_source_ratio']:.1%}")
        return Panel(table, title="System Metrics", box=box.ROUNDED)

    def _build_performance_panel(self, metrics: Dict[str, float]) -> Panel:
        """Builds performance metrics panel"""
        table = Table(box=None)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")
        table.add_row("Avg Yield", f"{metrics['avg_yield']:.2f}%")
        table.add_row("Avg Wait Time", f"{metrics['avg_wait']:.1f} min")
        table.add_row("Initial Value", f"{self.initial_account_value:.4f} ETH")
        table.add_row("Current Value", f"{metrics['eth_balance']:.4f} ETH")
        return Panel(table, title="Performance Metrics", box=box.ROUNDED)

    def _build_recent_events_panel(self) -> Panel:
        """Builds recent events panel with color logic for negative yields."""
        events = self.get_recent_events()
        if not events:
            return Panel("No events yet.", title="Recent Transactions", style="dim", box=box.ROUNDED)
        
        content_lines = []
        for e in events:
            # Construct the display string
            sold_symbol = "✅" if e["can_sell"] else "❌"
            display_str = (
                f"{e['token_address']} | "
                f"Yield: {e['yield_percent']:.1f}% | "
                f"Sold: {sold_symbol}"
            )

            # Color logic:
            # 1) If it was sold (✅) but yield < 0 => red line (still has check mark).
            # 2) If sold with yield >= 0 => green line.
            # 3) If not sold (❌), always red line.
            if e["can_sell"]:
                if e["yield_percent"] < 0:
                    # Negative yield but still sold => red check
                    content_lines.append(f"[red]{display_str}[/red]")
                else:
                    content_lines.append(f"[green]{display_str}[/green]")
            else:
                # Not sold
                content_lines.append(f"[red]{display_str}[/red]")

        return Panel(
            "\n".join(content_lines),
            title="Recent Transactions",
            style="dim",
            box=box.ROUNDED
        )

    def _build_logs_panel(self) -> Panel:
        """Builds log monitoring panel"""
        if not self.log_dir.is_dir():
            return Panel("Log directory not found.", title="Logs Needing Attention", style="dim", box=box.ROUNDED)

        log_files = list(self.log_dir.glob("*.log"))
        attention_logs = []

        for log_file in log_files:
            # skip general_errors.log
            if "general_errors" in log_file.name:
                continue
            try:
                with open(log_file, "r") as f:
                    lines = f.readlines()
                    if not lines:
                        continue
                    last_line = lines[-1].strip()
                    # If the last line is not indicating "Waiting", we highlight it
                    if "Waiting" not in last_line:
                        truncated = last_line[23:73] + "..." if len(last_line) > 50 else last_line
                        attention_logs.append(f"{log_file.name}: {truncated}")
            except Exception as e:
                attention_logs.append(f"[red]Error reading {log_file.name}: {str(e)}[/red]")

        if not attention_logs:
            return Panel("All logs are normal.", title="Logs Needing Attention", style="green", box=box.ROUNDED)

        return Panel(
            Text("\n".join(attention_logs), style="italic"),
            title="Logs Needing Attention", 
            style="yellow",
            box=box.ROUNDED
        )

    def update_display(self) -> Layout:
        """Updates the dashboard layout"""
        self.load_historical_data_incrementally()
        metrics = self.get_system_metrics()

        layout = Layout(name="root")
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
        )
        layout["main"].split_row(
            Layout(name="metrics", ratio=1),
            Layout(name="logs", ratio=3),
        )

        layout["header"].update(self._build_header_panel(metrics))

        right_column = Layout()
        right_column.split_column(
            Layout(self._build_recent_events_panel(), ratio=1),
            Layout(self._build_logs_panel(), ratio=1)
        )
        
        left_column = Layout()
        left_column.split_column(
            Layout(self._build_performance_panel(metrics), ratio=1),
            Layout(self._build_system_metrics_panel(metrics), ratio=1)
        )
            
        layout["logs"].update(right_column)
        layout["metrics"].update(left_column)
        return layout

    def run(self):
        """Main execution loop"""
        console = Console()
        with Live(self.update_display(), console=console, refresh_per_second=2) as live:
            while True:
                time.sleep(1)
                live.update(self.update_display())


if __name__ == "__main__":
    dashboard = HoneypotDashboard()
    dashboard.run()
