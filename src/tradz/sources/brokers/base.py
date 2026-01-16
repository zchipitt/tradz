"""
Base class for broker integrations.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional


@dataclass
class Position:
    """Portfolio position."""
    symbol: str
    quantity: float
    avg_cost: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Order:
    """Trade order."""
    order_id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: float
    order_type: str  # 'market', 'limit', etc.
    status: str
    filled_qty: float
    avg_fill_price: Optional[float]
    limit_price: Optional[float] = None
    created_at: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)


class BrokerBase(ABC):
    """Abstract base class for broker integrations."""

    @abstractmethod
    def authenticate(self) -> bool:
        """
        Authenticate with broker API.

        Returns:
            True if authentication successful
        """
        pass

    @abstractmethod
    def get_positions(self) -> List[Position]:
        """
        Get current portfolio positions.

        Returns:
            List of Position objects
        """
        pass

    @abstractmethod
    def get_orders(self, status: str = 'all') -> List[Order]:
        """
        Get orders (open, filled, all).

        Args:
            status: Filter by status ('open', 'filled', 'all')

        Returns:
            List of Order objects
        """
        pass

    @abstractmethod
    def get_account_balance(self) -> Dict:
        """
        Get account balance and buying power.

        Returns:
            Dict with account info
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if connected to broker.

        Returns:
            True if connected
        """
        pass

    def get_portfolio_summary(self) -> Dict:
        """
        Get portfolio summary.

        Returns:
            Dict with portfolio overview
        """
        positions = self.get_positions()
        balance = self.get_account_balance()

        total_value = sum(p.market_value for p in positions)
        total_pnl = sum(p.unrealized_pnl for p in positions)

        return {
            'positions_count': len(positions),
            'total_market_value': total_value,
            'total_unrealized_pnl': total_pnl,
            'positions': [p.to_dict() for p in positions],
            'account': balance,
        }
