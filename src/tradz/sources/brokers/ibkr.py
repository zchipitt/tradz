"""
Interactive Brokers (IBKR) integration using ib_insync.

Requires:
- ib_insync package: pip install ib_insync
- TWS or IB Gateway running
"""
import logging
import os
from typing import Dict, List, Optional

from .base import BrokerBase, Position, Order

logger = logging.getLogger(__name__)

# Try to import ib_insync
try:
    from ib_insync import IB, Stock, Contract
    IB_AVAILABLE = True
except ImportError:
    IB_AVAILABLE = False
    logger.warning("ib_insync not installed. IBKR integration unavailable.")


class IBKRBroker(BrokerBase):
    """Interactive Brokers integration."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        client_id: Optional[int] = None
    ):
        """
        Initialize IBKR broker.

        Args:
            host: TWS/Gateway host (default: 127.0.0.1)
            port: TWS/Gateway port (default: 7497 for paper, 7496 for live)
            client_id: Client ID for connection
        """
        if not IB_AVAILABLE:
            raise ImportError(
                "ib_insync is required for IBKR integration. "
                "Install with: pip install ib_insync"
            )

        self.host = host or os.getenv('IBKR_HOST', '127.0.0.1')
        self.port = port or int(os.getenv('IBKR_PORT', '7497'))
        self.client_id = client_id or int(os.getenv('IBKR_CLIENT_ID', '1'))

        self.ib = IB()
        self._connected = False

    def authenticate(self) -> bool:
        """Connect to TWS/Gateway."""
        if self._connected:
            return True

        try:
            self.ib.connect(
                host=self.host,
                port=self.port,
                clientId=self.client_id,
                readonly=True  # Read-only for safety
            )
            self._connected = True
            logger.info(f"Connected to IBKR at {self.host}:{self.port}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to IBKR: {e}")
            self._connected = False
            return False

    def is_connected(self) -> bool:
        """Check if connected."""
        return self._connected and self.ib.isConnected()

    def disconnect(self):
        """Disconnect from IBKR."""
        if self._connected:
            self.ib.disconnect()
            self._connected = False
            logger.info("Disconnected from IBKR")

    def get_positions(self) -> List[Position]:
        """Get current positions."""
        if not self.is_connected():
            if not self.authenticate():
                return []

        try:
            positions = []
            ib_positions = self.ib.positions()

            for pos in ib_positions:
                contract = pos.contract
                symbol = contract.symbol

                # Get current price
                ticker = self.ib.reqTickers(contract)
                current_price = 0.0
                if ticker and ticker[0].marketPrice():
                    current_price = ticker[0].marketPrice()

                avg_cost = pos.avgCost
                quantity = pos.position
                market_value = quantity * current_price
                unrealized_pnl = market_value - (quantity * avg_cost)
                unrealized_pnl_pct = (unrealized_pnl / (quantity * avg_cost) * 100) if avg_cost > 0 else 0

                positions.append(Position(
                    symbol=symbol,
                    quantity=quantity,
                    avg_cost=avg_cost,
                    current_price=current_price,
                    market_value=market_value,
                    unrealized_pnl=unrealized_pnl,
                    unrealized_pnl_pct=unrealized_pnl_pct,
                ))

            logger.info(f"Fetched {len(positions)} positions from IBKR")
            return positions

        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return []

    def get_orders(self, status: str = 'all') -> List[Order]:
        """Get orders."""
        if not self.is_connected():
            if not self.authenticate():
                return []

        try:
            orders = []

            if status in ['all', 'open']:
                open_orders = self.ib.openOrders()
                for trade in self.ib.openTrades():
                    order = trade.order
                    contract = trade.contract

                    orders.append(Order(
                        order_id=str(order.orderId),
                        symbol=contract.symbol,
                        side='buy' if order.action == 'BUY' else 'sell',
                        quantity=order.totalQuantity,
                        order_type=order.orderType.lower(),
                        status='open',
                        filled_qty=trade.orderStatus.filled,
                        avg_fill_price=trade.orderStatus.avgFillPrice or None,
                        limit_price=order.lmtPrice if order.orderType == 'LMT' else None,
                    ))

            logger.info(f"Fetched {len(orders)} orders from IBKR")
            return orders

        except Exception as e:
            logger.error(f"Error fetching orders: {e}")
            return []

    def get_account_balance(self) -> Dict:
        """Get account balance."""
        if not self.is_connected():
            if not self.authenticate():
                return {}

        try:
            account_values = self.ib.accountValues()

            # Extract key values
            balance = {}
            for av in account_values:
                if av.tag in [
                    'NetLiquidation',
                    'TotalCashValue',
                    'BuyingPower',
                    'GrossPositionValue',
                    'MaintMarginReq',
                    'AvailableFunds',
                ]:
                    try:
                        balance[av.tag] = float(av.value)
                    except ValueError:
                        balance[av.tag] = av.value

            logger.info("Fetched account balance from IBKR")
            return balance

        except Exception as e:
            logger.error(f"Error fetching account balance: {e}")
            return {}

    def __enter__(self):
        self.authenticate()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
