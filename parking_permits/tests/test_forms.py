from django.test import TestCase

from parking_permits.forms import DataExportForm


class DataExportFormTestCase(TestCase):
    def test_form_is_valid_when_valid_data_provided(self):
        data = {
            "data_type": "orders",
            "order_by": '{"order_fields": ["order_number"], "order_direction": "DESC"}',
            "search_items": '[{"matchType": "exact", "fields": ["order_number"], "value": 1}]',
        }
        form = DataExportForm(data)
        self.assertTrue(form.is_valid())

    def test_form_not_valid_when_fail_to_decode_error(self):
        data = {"data_type": "orders", "order_by": ";{}"}
        form = DataExportForm(data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error("order_by", code="decode_error"))

    def test_form_not_valid_when_invalid_order_by_provided(self):
        data = {"data_type": "orders", "order_by": '{"key": "value"}'}
        form = DataExportForm(data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error("order_by", code="invalid_data"))

    def test_form_not_valid_when_fail_to_decode_search_items(self):
        data = {"data_type": "orders", "search_items": "[,]"}
        form = DataExportForm(data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error("search_items", code="decode_error"))

    def test_form_not_valid_when_invalid_search_items_provided(self):
        data = {"data_type": "orders", "search_items": '[{"matchType": "exact"}]'}
        form = DataExportForm(data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error("search_items", code="invalid_data"))
