import abc

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from fpdf import FPDF

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


class BasePDF(FPDF, metaclass=abc.ABCMeta):
    def header(self):
        self.image(str(settings.STATIC_ROOT) + "/helsinki.png", 10, 8, 33)
        self.set_font("Arial", "B", 15)
        self.cell(80)
        self.cell(20, 10, self.get_title(), 0, 0, "C")
        self.ln(20)

    def footer(self):
        self.set_y(-25)
        self.set_font("Arial", "I", 8)
        self.cell(0, 5, _("City of Helsinki"), 0, 1, "C")
        self.cell(0, 5, _("Urban Environment Division"), 0, 1, "C")
        self.cell(0, 5, "https://www.hel.fi/kaupunkiymparisto/", 0, 0, "C")

    @abc.abstractmethod
    def get_title(self):
        pass

    @abc.abstractmethod
    def get_source_object(self, object_id):
        pass

    @abc.abstractmethod
    def set_content(self, obj):
        pass


class ParkingPermitPDF(BasePDF):
    def get_title(self):
        return _("Parking permits")

    def get_source_object(self, object_id):
        permit_qs = ParkingPermit.objects.filter(pk=object_id)
        if not permit_qs.exists():
            return None
        return permit_qs.first()

    def set_content(self, obj):
        permit = obj
        content = [
            _("Resident permit"),
            _("Permit ID") + ": " + f"{permit.id}",
            _("Customer")
            + ": "
            + f"{permit.customer.first_name} {permit.customer.last_name}",
            _("Address") + ": " + str(permit.address),
            _("Area") + ": " + str(permit.parking_zone.name),
            _("Vehicle")
            + ": "
            + f"{permit.vehicle.registration_number} ({permit.vehicle.manufacturer} {permit.vehicle.model})",
            _("Type") + ": " + permit.get_contract_type_display(),
            _("Validity period")
            + ": "
            + permit.start_time.strftime(DATETIME_FORMAT)
            + " - "
            + permit.end_time.strftime(DATETIME_FORMAT),
        ]
        for line in content:
            self.cell(0, 7, line, 0, 1)


PDF_MODEL_MAPPING = {
    "permit": ParkingPermitPDF,
}


class PdfExporter:
    def __init__(self, data_type, object_id):
        self.data_type = data_type
        self.object_id = object_id

    def get_pdf(self):
        pdf = PDF_MODEL_MAPPING[self.data_type]()
        obj = pdf.get_source_object(self.object_id)
        if not obj:
            return None
        pdf.add_page()
        pdf.set_font("Times", "", 12)
        pdf.set_content(obj)
        return pdf
