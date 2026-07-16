import datetime
import pytest
from decimal import Decimal
from pydantic import ValidationError, TypeAdapter

from core.iso20022.handelsbanken import HandelsbankenISO20022, SE_IBAN


class TestSeIban:
    def test_strips_spaces_and_uppercases(self):
        adapter = TypeAdapter(SE_IBAN)

        result = adapter.validate_python("se45 5000 0000 0583 9825 7466")

        assert result == "SE4550000000058398257466"

    def test_rejects_wrong_country_prefix(self):
        adapter = TypeAdapter(SE_IBAN)

        with pytest.raises(ValidationError):
            adapter.validate_python("DE4550000000058398257466")


class TestLocalAccountPayment:
    def test_renders_xml_with_expected_values(self):
        payment = HandelsbankenISO20022.LocalAccountPayment(
            debtor_iban="SE4550000000058398257466",
            creditor_iban="SE1110000000000123456789",
            amount=Decimal("1250.00"),
            date=datetime.date.today(),
            instr_id="INSTR-1",
            end_to_end_id="E2E-1",
        )

        xml = HandelsbankenISO20022().local_account_payment(
            [payment],
            debtor_iban="SE4550000000058398257466",
            msg_id="MSG-1",
            pmt_inf_id="PMT-1",
        )

        assert "<IBAN>SE4550000000058398257466</IBAN>" in xml
        assert "<IBAN>SE1110000000000123456789</IBAN>" in xml
        assert "<BICFI>HANDSESS</BICFI>" in xml
        assert '<InstdAmt Ccy="SEK">1250.00</InstdAmt>' in xml

    def test_ctrl_sum_and_count_reflect_batch_size(self):
        payments = [
            HandelsbankenISO20022.LocalAccountPayment(
                debtor_iban="SE4550000000058398257466",
                creditor_iban="SE1110000000000123456789",
                amount=Decimal("100.00"),
                date=datetime.date.today(),
                instr_id=f"INSTR-{i}",
                end_to_end_id=f"E2E-{i}",
            )
            for i in range(3)
        ]

        xml = HandelsbankenISO20022().local_account_payment(
            payments,
            debtor_iban="SE4550000000058398257466",
            msg_id="MSG-1",
            pmt_inf_id="PMT-1",
        )

        assert "<NbOfTxs>3</NbOfTxs>" in xml
        assert "<CtrlSum>300.00</CtrlSum>" in xml
