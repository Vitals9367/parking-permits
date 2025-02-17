import datetime

import requests_mock
from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from freezegun import freeze_time
from helusers.settings import api_token_auth_settings
from jose import jwt
from rest_framework.test import APIClient, APITestCase

from parking_permits.models.order import OrderStatus
from parking_permits.models.parking_permit import ParkingPermit, ParkingPermitStatus
from parking_permits.tests.factories.customer import CustomerFactory
from parking_permits.tests.factories.order import OrderFactory
from parking_permits.tests.factories.parking_permit import ParkingPermitFactory
from users.tests.factories.user import UserFactory

from ..models import Customer
from ..models.common import SourceSystem
from .keys import rsa_key


class OrderViewTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()

    def test_order_view_should_return_bad_request_if_talpa_order_id_missing(self):
        url = reverse("parking_permits:order-notify")
        data = {
            "eventType": "PAYMENT_PAID",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)

    @override_settings(DEBUG=True)
    def test_order_view_should_update_order_and_permits_status(self):
        talpa_order_id = "D86CA61D-97E9-410A-A1E3-4894873B1B35"
        permit_1 = ParkingPermitFactory(status=ParkingPermitStatus.PAYMENT_IN_PROGRESS)
        permit_2 = ParkingPermitFactory(status=ParkingPermitStatus.PAYMENT_IN_PROGRESS)
        order = OrderFactory(talpa_order_id=talpa_order_id, status=OrderStatus.DRAFT)
        order.permits.add(permit_1, permit_2)
        url = reverse("parking_permits:order-notify")
        data = {"eventType": "PAYMENT_PAID", "orderId": talpa_order_id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        permit_1.refresh_from_db()
        permit_2.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.CONFIRMED)
        self.assertEqual(permit_1.status, ParkingPermitStatus.VALID)
        self.assertEqual(permit_1.status, ParkingPermitStatus.VALID)


@override_settings(
    OIDC_API_TOKEN_AUTH={
        "AUDIENCE": "test_audience",
        "API_SCOPE_PREFIX": "testprefix",
        "ISSUER": "http://localhost/openid",
        "TOKEN_AUTH_REQUIRE_SCOPE_PREFIX": True,
    },
    GDPR_API_QUERY_SCOPE="testprefix.gdprquery",
    GDPR_API_DELETE_SCOPE="testprefix.gdprdelete",
)
class ParkingPermitsGDPRAPIViewTestCase(APITestCase):
    CUSTOMER_SOURCE_ID = "profile-source-id"

    def create_customer(self):
        user = UserFactory()
        customer = CustomerFactory(
            user=user,
            source_system=SourceSystem.HELSINKI_PROFILE,
            source_id=self.CUSTOMER_SOURCE_ID,
        )
        ParkingPermitFactory(
            customer=customer,
            status=ParkingPermitStatus.CLOSED,
            end_time=datetime.datetime(2020, 2, 1),
        )
        return customer

    def assertCustomerDeleted(self):
        self.assertFalse(
            Customer.objects.filter(source_id=self.CUSTOMER_SOURCE_ID).exists()
        )
        self.assertFalse(ParkingPermit.objects.exists())

    def assertCustomerNotDeleted(self):
        self.assertTrue(
            Customer.objects.filter(source_id=self.CUSTOMER_SOURCE_ID).exists()
        )
        self.assertTrue(ParkingPermit.objects.exists())

    def get_auth_header(self, user, scopes, req_mock):
        audience = api_token_auth_settings.AUDIENCE
        issuer = api_token_auth_settings.ISSUER
        auth_field = api_token_auth_settings.API_AUTHORIZATION_FIELD
        config_url = f"{issuer}/.well-known/openid-configuration"
        jwks_url = f"{issuer}/jwks"
        configuration = {
            "issuer": issuer,
            "jwks_uri": jwks_url,
        }
        keys = {"keys": [rsa_key.public_key_jwk]}

        now = datetime.datetime.now()
        expire = now + datetime.timedelta(days=14)
        jwt_data = {
            "iss": issuer,
            "aud": audience,
            "sub": str(user.uuid),
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
            auth_field: scopes,
        }
        encoded_jwt = jwt.encode(
            jwt_data, key=rsa_key.private_key_pem, algorithm=rsa_key.jose_algorithm
        )

        req_mock.get(config_url, json=configuration)
        req_mock.get(jwks_url, json=keys)

        return f"{api_token_auth_settings.AUTH_SCHEME} {encoded_jwt}"

    @requests_mock.Mocker()
    def test_get_profile_should_return_customer_profile_detail(self, req_mock):
        customer = self.create_customer()
        auth_header = self.get_auth_header(
            customer.user, [settings.GDPR_API_QUERY_SCOPE], req_mock
        )
        url = reverse("parking_permits:gdpr_v1", kwargs={"id": customer.source_id})
        self.client.credentials(HTTP_AUTHORIZATION=auth_header)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    @requests_mock.Mocker()
    def test_get_profile_should_be_forbidden_with_wrong_scope(self, req_mock):
        customer = self.create_customer()
        auth_header = self.get_auth_header(
            customer.user, ["testprefix.invalid"], req_mock
        )
        url = reverse("parking_permits:gdpr_v1", kwargs={"id": customer.source_id})
        self.client.credentials(HTTP_AUTHORIZATION=auth_header)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    @requests_mock.Mocker()
    def test_delete_profile_should_delete_profile_and_related_data(self, req_mock):
        with freeze_time(datetime.datetime(2020, 1, 1)):
            customer = self.create_customer()

        with freeze_time(datetime.datetime(2022, 3, 1)):
            auth_header = self.get_auth_header(
                customer.user, [settings.GDPR_API_DELETE_SCOPE], req_mock
            )
            url = reverse("parking_permits:gdpr_v1", kwargs={"id": customer.source_id})
            self.client.credentials(HTTP_AUTHORIZATION=auth_header)
            response = self.client.delete(url)
            self.assertEqual(response.status_code, 204)
            self.assertCustomerDeleted()

    @requests_mock.Mocker()
    def test_delete_profile_should_be_forbidden_when_using_wrong_scope(self, req_mock):
        with freeze_time(datetime.datetime(2020, 1, 1)):
            customer = self.create_customer()

        with freeze_time(datetime.datetime(2022, 3, 1)):
            auth_header = self.get_auth_header(
                customer.user, ["testprefix.wrong_scope"], req_mock
            )
            url = reverse("parking_permits:gdpr_v1", kwargs={"id": customer.source_id})
            self.client.credentials(HTTP_AUTHORIZATION=auth_header)
            response = self.client.delete(url)
            self.assertEqual(response.status_code, 403)
            self.assertCustomerNotDeleted()

    @requests_mock.Mocker()
    def test_delete_profile_should_be_forbidden_if_customer_cannot_be_deleted(
        self, req_mock
    ):
        with freeze_time(datetime.datetime(2020, 1, 1)):
            customer = self.create_customer()
            ParkingPermitFactory(
                customer=customer,
                status=ParkingPermitStatus.CLOSED,
                end_time=datetime.datetime(2020, 2, 1),
            )

        with freeze_time(datetime.datetime(2022, 1, 15)):
            auth_header = self.get_auth_header(
                customer.user, [settings.GDPR_API_DELETE_SCOPE], req_mock
            )
            url = reverse("parking_permits:gdpr_v1", kwargs={"id": customer.source_id})
            self.client.credentials(HTTP_AUTHORIZATION=auth_header)
            response = self.client.delete(url)
            self.assertEqual(response.status_code, 403)
            self.assertCustomerNotDeleted()

    @requests_mock.Mocker()
    def test_delete_profile_should_keep_profile_and_related_data_when_dry_run(
        self, req_mock
    ):
        with freeze_time(datetime.datetime(2020, 1, 1)):
            customer = self.create_customer()
            ParkingPermitFactory(
                customer=customer,
                status=ParkingPermitStatus.CLOSED,
                end_time=datetime.datetime(2020, 2, 1),
            )

        with freeze_time(datetime.datetime(2022, 3, 1)):
            auth_header = self.get_auth_header(
                customer.user, [settings.GDPR_API_DELETE_SCOPE], req_mock
            )
            url = reverse("parking_permits:gdpr_v1", kwargs={"id": customer.source_id})
            self.client.credentials(HTTP_AUTHORIZATION=auth_header)
            # make sure we do not deleted the profile when client specify different types of true values
            true_values = ["true", "True", "TRUE", "1", 1, True]
            for true_value in true_values:
                response = self.client.delete(url, data={"dry_run": true_value})
                self.assertEqual(response.status_code, 204)
                self.assertCustomerNotDeleted()
