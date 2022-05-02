from django.utils.translation import ugettext_lazy as _

from parking_permits.models import Order, ParkingPermit, Product, Refund
from parking_permits.utils import apply_filtering, apply_ordering

DATETIME_FORMAT = "%-d.%-m.%Y, %H:%M"
DATE_FORMAT = "%-d.%-m.%Y"

MODEL_MAPPING = {
    "permits": ParkingPermit,
    "orders": Order,
    "refunds": Refund,
    "products": Product,
}


def _get_permit_row(permit):
    customer = permit.customer
    vehicle = permit.vehicle
    name = f"{customer.last_name}, {customer.first_name}"
    return [
        name,
        customer.national_id_number,
        vehicle.registration_number,
        str(customer.primary_address),
        str(customer.other_address),
        permit.parking_zone.name,
        permit.start_time.strftime(DATETIME_FORMAT) if permit.start_time else "",
        permit.end_time.strftime(DATETIME_FORMAT) if permit.end_time else "",
        permit.get_status_display(),
    ]


def _get_order_row(order):
    customer = order.customer
    permit_ids = order.order_items.values_list("permit")
    permits = ParkingPermit.objects.filter(id__in=permit_ids)
    reg_numbers = ", ".join([permit.vehicle.registration_number for permit in permits])
    name = f"{customer.last_name}, {customer.first_name}"
    return [
        name,
        reg_numbers,
        permits[0].parking_zone.name,
        str(permits[0].address),
        permits[0].get_type_display(),
        order.id,
        order.paid_time.strftime(DATETIME_FORMAT) if order.paid_time else "",
        order.total_price,
    ]


def _get_refund_row(refund):
    return [
        refund.name,
        refund.amount,
        refund.iban,
        refund.get_status_display(),
        refund.created_at.strftime(DATETIME_FORMAT),
    ]


def _get_product_row(product):
    start_date = product.start_date.strftime(DATE_FORMAT)
    end_date = product.end_date.strftime(DATE_FORMAT)
    valid_period = f"{start_date} - {end_date}"
    return [
        product.get_type_display(),
        product.zone.name,
        product.unit_price,
        product.vat,
        valid_period,
        product.modified_at.strftime(DATETIME_FORMAT),
        product.modified_by,
    ]


ROW_GETTER_MAPPING = {
    "permits": _get_permit_row,
    "orders": _get_order_row,
    "refunds": _get_refund_row,
    "products": _get_product_row,
}

PERMIT_HEADERS = [
    _("Name"),
    "Hetu",
    _("Registration number"),
    _("Permanent address"),
    _("Temporary address"),
    _("Parking zone"),
    _("Start time"),
    _("End time"),
    _("Status"),
]

ORDER_HEADERS = [
    _("Name"),
    _("Registration number"),
    _("Parking zone"),
    _("Address"),
    _("Permit type"),
    _("Order number"),
    _("Paid time"),
]

REFUND_HEADERS = [
    _("Name"),
    _("Amount"),
    "IBAN",
    _("Status"),
    _("Created at"),
]

PRODUCT_HEADERS = [
    _("Product type"),
    _("Parking zone"),
    _("Price"),
    _("VAT"),
    _("Valid period"),
    _("Modified at"),
    _("Modified by"),
]

HEADERS_MAPPING = {
    "permits": PERMIT_HEADERS,
    "orders": ORDER_HEADERS,
    "refunds": REFUND_HEADERS,
    "products": PRODUCT_HEADERS,
}


class DataExporter:
    def __init__(self, data_type, order_by=None, search_items=None):
        self.data_type = data_type
        self.order_by = order_by
        self.search_items = search_items

    def get_queryset(self):
        model_class = MODEL_MAPPING[self.data_type]
        qs = model_class.objects.all()
        if self.order_by:
            qs = apply_ordering(qs, self.order_by)
        if self.search_items:
            qs = apply_filtering(qs, self.search_items)
        return qs

    def get_headers(self):
        return HEADERS_MAPPING[self.data_type]

    def get_rows(self):
        row_getter = ROW_GETTER_MAPPING[self.data_type]
        return [row_getter(item) for item in self.get_queryset()]
