from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple

@dataclass
class LineItem:
    sku: str
    category: str
    unit_price: float
    qty: int
    fragile: bool = False


@dataclass
class Invoice:
    invoice_id: str
    customer_id: str
    country: str
    membership: str
    coupon: Optional[str]
    items: List[LineItem]


class InvoiceService:
    VALID_CATEGORIES = ("book", "food", "electronics", "other")

    def __init__(self) -> None:
        self._coupon_rate: Dict[str, float] = {
            "WELCOME10": 0.10,
            "VIP20": 0.20,
            "STUDENT5": 0.05,
        }
        self._tax_rates: Dict[str, float] = {
            "TH": 0.07,
            "JP": 0.10,
            "US": 0.08,
        }

    def _validate(self, inv: Invoice) -> List[str]:
        problems: List[str] = []
        if inv is None:
            return ["Invoice is missing"]
        if not inv.invoice_id:
            problems.append("Missing invoice_id")
        if not inv.customer_id:
            problems.append("Missing customer_id")
        if not inv.items:
            problems.append("Invoice must contain items")
        for it in inv.items or []:
            if not it.sku:
                problems.append("Item sku is missing")
            if it.qty <= 0:
                problems.append(f"Invalid qty for {it.sku}")
            if it.unit_price < 0:
                problems.append(f"Invalid price for {it.sku}")
            if it.category not in self.VALID_CATEGORIES:
                problems.append(f"Unknown category for {it.sku}")
        return problems

    def _calc_subtotal_and_fragile(self, items: List[LineItem]) -> Tuple[float, float]:
        subtotal = 0.0
        fragile_fee = 0.0
        for it in items:
            subtotal += it.unit_price * it.qty
            if it.fragile:
                fragile_fee += 5.0 * it.qty
        return subtotal, fragile_fee

    def _calc_shipping(self, subtotal: float, country: str) -> float:
        if country == "US":
            if subtotal < 100:
                return 15.0
            if subtotal < 300:
                return 8.0
            return 0.0
        if country == "TH":
            return 60.0 if subtotal < 500 else 0.0
        if country == "JP":
            return 600.0 if subtotal < 4000 else 0.0
        return 25.0 if subtotal < 200 else 0.0

    def _membership_discount(self, subtotal: float, membership: str) -> float:
        if membership == "gold":
            return subtotal * 0.03
        if membership == "platinum":
            return subtotal * 0.05
        return 20.0 if subtotal > 3000 else 0.0

    def _coupon_discount(self, subtotal: float, coupon: Optional[str], warnings: List[str]) -> float:
        if not coupon or coupon.strip() == "":
            return 0.0
        code = coupon.strip()
        rate = self._coupon_rate.get(code)
        if rate is None:
            warnings.append("Unknown coupon")
            return 0.0
        return subtotal * rate

    def _tax_amount(self, taxable: float, country: str) -> float:
        rate = self._tax_rates.get(country, 0.05)
        return taxable * rate

    def compute_total(self, inv: Invoice) -> Tuple[float, List[str]]:
        warnings: List[str] = []
        problems = self._validate(inv)
        if problems:
            raise ValueError("; ".join(problems))

        subtotal, fragile_fee = self._calc_subtotal_and_fragile(inv.items)

        shipping = self._calc_shipping(subtotal, inv.country)

        discount = self._membership_discount(subtotal, inv.membership)
        discount += self._coupon_discount(subtotal, inv.coupon, warnings)

        taxable = max(subtotal - discount, 0.0)
        tax = self._tax_amount(taxable, inv.country)

        total = subtotal + shipping + fragile_fee + tax - discount
        total = max(total, 0.0)

        if subtotal > 10000 and inv.membership not in ("gold", "platinum"):
            warnings.append("Consider membership upgrade")

        return total, warnings
