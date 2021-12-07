from datetime import datetime

from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from parking_permits.constants import ParkingPermitEndType
from parking_permits.exceptions import PermitCanNotBeEnded, RefundCanNotBeCreated
from parking_permits.models.parking_permit import ContractType, ParkingPermitStatus
from parking_permits.tests.factories import ParkingZoneFactory, PriceFactory
from parking_permits.tests.factories.customer import CustomerFactory
from parking_permits.tests.factories.parking_permit import ParkingPermitFactory
from parking_permits.utils import get_end_time


class ParkingZoneTestCase(TestCase):
    @freeze_time(timezone.make_aware(datetime(2021, 11, 15)))
    def test_should_return_correct_months_used(self):
        start_time = timezone.make_aware(datetime(2021, 9, 15))
        end_time = get_end_time(start_time, 6)
        fixed_period_permit_started_2_months_ago = ParkingPermitFactory(
            contract_type=ContractType.FIXED_PERIOD,
            start_time=start_time,
            end_time=end_time,
            month_count=6,
        )
        self.assertEqual(fixed_period_permit_started_2_months_ago.months_used, 3)

        start_time = timezone.make_aware(datetime(2021, 11, 16))
        end_time = get_end_time(start_time, 6)
        fixed_period_permit_start_tomorrow = ParkingPermitFactory(
            contract_type=ContractType.FIXED_PERIOD,
            start_time=start_time,
            end_time=end_time,
            month_count=6,
        )
        self.assertEqual(fixed_period_permit_start_tomorrow.months_used, 0)

        start_time = timezone.make_aware(datetime(2019, 11, 15))
        end_time = get_end_time(start_time, 6)
        fixed_period_permit_started_2_years_ago = ParkingPermitFactory(
            contract_type=ContractType.FIXED_PERIOD,
            start_time=start_time,
            end_time=end_time,
            month_count=6,
        )
        self.assertEqual(fixed_period_permit_started_2_years_ago.months_used, 6)

        start_time = timezone.make_aware(datetime(2019, 11, 15))
        open_ended_permit_started_two_years_ago = ParkingPermitFactory(
            contract_type=ContractType.OPEN_ENDED,
            start_time=start_time,
        )
        self.assertEqual(open_ended_permit_started_two_years_ago.months_used, 25)

    @freeze_time(timezone.make_aware(datetime(2021, 11, 15)))
    def test_should_return_correct_months_left(self):
        start_time = timezone.make_aware(datetime(2021, 9, 15))
        end_time = get_end_time(start_time, 6)
        fixed_period_permit_started_2_months_ago = ParkingPermitFactory(
            contract_type=ContractType.FIXED_PERIOD,
            start_time=start_time,
            end_time=end_time,
            month_count=6,
        )
        self.assertEqual(fixed_period_permit_started_2_months_ago.months_left, 3)

        start_time = timezone.make_aware(datetime(2021, 11, 16))
        end_time = get_end_time(start_time, 6)
        fixed_period_permit_start_tomorrow = ParkingPermitFactory(
            contract_type=ContractType.FIXED_PERIOD,
            start_time=start_time,
            end_time=end_time,
            month_count=6,
        )
        self.assertEqual(fixed_period_permit_start_tomorrow.months_left, 6)

        start_time = timezone.make_aware(datetime(2019, 11, 15))
        end_time = get_end_time(start_time, 6)
        fixed_period_permit_started_2_years_ago = ParkingPermitFactory(
            contract_type=ContractType.FIXED_PERIOD,
            start_time=start_time,
            end_time=end_time,
            month_count=6,
        )
        self.assertEqual(fixed_period_permit_started_2_years_ago.months_left, 0)

        start_time = timezone.make_aware(datetime(2019, 11, 15))
        open_ended_permit_started_two_years_ago = ParkingPermitFactory(
            contract_type=ContractType.OPEN_ENDED,
            start_time=start_time,
        )
        self.assertEqual(open_ended_permit_started_two_years_ago.months_left, None)

    @freeze_time(timezone.make_aware(datetime(2022, 1, 20)))
    def test_should_return_correct_end_time_of_current_time(self):
        start_time = timezone.make_aware(datetime(2021, 11, 15))
        end_time = get_end_time(start_time, 6)
        permit = ParkingPermitFactory(
            contract_type=ContractType.FIXED_PERIOD,
            start_time=start_time,
            end_time=end_time,
            month_count=6,
        )
        self.assertEqual(
            permit.current_period_end_time,
            timezone.make_aware(datetime(2022, 2, 14, 23, 59)),
        )

        start_time = timezone.make_aware(datetime(2021, 11, 20))
        end_time = get_end_time(start_time, 6)
        permit = ParkingPermitFactory(
            contract_type=ContractType.FIXED_PERIOD,
            start_time=start_time,
            end_time=end_time,
            month_count=6,
        )
        self.assertEqual(
            permit.current_period_end_time,
            timezone.make_aware(datetime(2022, 2, 19, 23, 59)),
        )

    @freeze_time(timezone.make_aware(datetime(2021, 11, 20, 12, 10, 50)))
    def test_should_set_end_time_to_now_if_end_permit_immediately(self):
        start_time = timezone.make_aware(datetime(2021, 11, 15))
        end_time = get_end_time(start_time, 6)
        permit = ParkingPermitFactory(
            contract_type=ContractType.FIXED_PERIOD,
            start_time=start_time,
            end_time=end_time,
            month_count=6,
        )
        permit.end_permit(ParkingPermitEndType.IMMEDIATELY)
        self.assertEqual(
            permit.end_time, timezone.make_aware(datetime(2021, 11, 20, 12, 10, 50))
        )

    @freeze_time(timezone.make_aware(datetime(2021, 11, 20, 12, 10, 50)))
    def test_should_set_end_time_to_period_end_if_end_permit_after_current_period(self):
        start_time = timezone.make_aware(datetime(2021, 11, 15))
        end_time = get_end_time(start_time, 6)
        permit = ParkingPermitFactory(
            contract_type=ContractType.FIXED_PERIOD,
            start_time=start_time,
            end_time=end_time,
            month_count=6,
        )
        permit.end_permit(ParkingPermitEndType.AFTER_CURRENT_PERIOD)
        self.assertEqual(
            permit.end_time, timezone.make_aware(datetime(2021, 12, 14, 23, 59))
        )

    @freeze_time(timezone.make_aware(datetime(2021, 11, 20, 12, 10, 50)))
    def test_should_raise_error_when_end_primary_vehicle_permit_with_active_secondary_vehicle_permit(
        self,
    ):
        customer = CustomerFactory()
        primary_start_time = timezone.make_aware(datetime(2021, 11, 15))
        primary_end_time = get_end_time(primary_start_time, 6)
        primary_vehicle_permit = ParkingPermitFactory(
            customer=customer,
            primary_vehicle=True,
            contract_type=ContractType.FIXED_PERIOD,
            status=ParkingPermitStatus.VALID,
            start_time=primary_start_time,
            end_time=primary_end_time,
            month_count=6,
        )
        secondary_start_time = timezone.make_aware(datetime(2022, 1, 1))
        secondary_end_time = get_end_time(secondary_start_time, 2)
        ParkingPermitFactory(
            customer=customer,
            contract_type=ContractType.FIXED_PERIOD,
            status=ParkingPermitStatus.VALID,
            start_time=secondary_start_time,
            end_time=secondary_end_time,
            month_count=2,
        )
        with self.assertRaises(PermitCanNotBeEnded):
            primary_vehicle_permit.end_permit(ParkingPermitEndType.AFTER_CURRENT_PERIOD)

    @freeze_time(timezone.make_aware(datetime(2021, 11, 20, 12, 10, 50)))
    def test_should_raise_error_when_create_refund_for_open_ended_permit(self):
        start_time = timezone.make_aware(datetime(2021, 11, 15))
        permit = ParkingPermitFactory(
            contract_type=ContractType.OPEN_ENDED,
            start_time=start_time,
        )
        with self.assertRaises(RefundCanNotBeCreated):
            permit.create_refund("dummy-iban")

    @freeze_time(timezone.make_aware(datetime(2021, 11, 20, 12, 10, 50)))
    def test_should_create_refund_when_create_refund_for_fixed_period_permit(self):
        start_time = timezone.make_aware(datetime(2021, 11, 15))
        end_time = get_end_time(start_time, 6)
        zone = ParkingZoneFactory()
        PriceFactory(zone=zone, price=30, year=2021)
        permit = ParkingPermitFactory(
            parking_zone=zone,
            contract_type=ContractType.FIXED_PERIOD,
            start_time=start_time,
            end_time=end_time,
            month_count=6,
        )
        permit.end_permit(ParkingPermitEndType.AFTER_CURRENT_PERIOD)
        permit.create_refund("dummy-iban")
        self.assertTrue(permit.has_refund)
        self.assertEqual(permit.refund.amount, 150)