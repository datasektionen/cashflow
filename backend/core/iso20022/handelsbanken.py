"""This file provides a class for creating ISO 20022 payment files.

These can be used to create payments without manually entering all information.

If you want more information on how a specific field works, you can look up the dataclass name,
e.g. `PaymentInstruction51` in the ISO 20022 specification for pain.001 (you should be able to search and find the documents on https://www.iso20022.org/iso-20022-message-definitions).
I have also used Handelsbanken's own guide for pain.001 version 3 (found on https://www.handelsbanken.com/en/our-services/digital-services/global-gateway/iso-20022-xml as of writing).
"""

import datetime
from django.conf import settings
from pydantic import StringConstraints, BeforeValidator, BaseModel, validate_call
from typing import Annotated
from xsdata.formats.dataclass.context import XmlContext
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig

from core.iso20022.pain001.pain_001_001_13 import *


def normalize_iban(v: str) -> str:
    if isinstance(v, str):
        return v.replace(" ", "").upper()
    return v


SE_IBAN = Annotated[
    str,
    BeforeValidator(normalize_iban),
    StringConstraints(pattern=r"^SE\d{22}$"),
]


class HandelsbankenISO20022:

    BIC = "HANDSESS"

    class LocalAccountPayment(BaseModel):
        debtor_iban: SE_IBAN
        creditor_iban: SE_IBAN
        creditor_message: (
            Annotated[str, StringConstraints(min_length=1, max_length=12)] | None
        ) = None
        amount: Decimal
        date: datetime.date
        instr_id: str
        end_to_end_id: str

    def create_transaction(
        self, payment: LocalAccountPayment
    ) -> CreditTransferTransaction76:
        return CreditTransferTransaction76(
            pmt_id=PaymentIdentification6(
                instr_id=payment.instr_id,
                end_to_end_id=payment.end_to_end_id,
            ),
            # Here's the transaction amount
            amt=AmountType4Choice(
                instd_amt=ActiveOrHistoricCurrencyAndAmount(
                    value=payment.amount,
                    ccy="SEK",
                )
            ),
            # Creditor account (who is getting the transfer)
            cdtr_acct=CashAccount40(
                id=AccountIdentification4Choice(
                    iban=payment.creditor_iban,
                )
            ),
        )

    def create_payment_instruction(
        self, payments: list[LocalAccountPayment], debtor_iban: SE_IBAN, pmt_inf_id: str
    ) -> PaymentInstruction51:
        return PaymentInstruction51(
            pmt_inf_id=pmt_inf_id,
            reqd_exctn_dt=DateAndDateTime2Choice(
                dt=XmlDate.from_date(datetime.date.today()),
            ),
            # Debtor information (who is sending the money)
            dbtr=PartyIdentification272(nm=settings.ORG_NAME),
            dbtr_acct=CashAccount40(
                id=AccountIdentification4Choice(
                    iban=debtor_iban,
                ),
            ),
            dbtr_agt=BranchAndFinancialInstitutionIdentification8(
                fin_instn_id=FinancialInstitutionIdentification23(
                    # BIC = Business Identifier Code
                    bicfi=self.BIC,
                )
            ),
            pmt_mtd=PaymentMethod3Code.TRF,
            pmt_tp_inf=PaymentTypeInformation26(
                svc_lvl=[ServiceLevel8Choice(cd="NURG")],
                ctgy_purp=CategoryPurpose1Choice(cd="SUPP"),
            ),
            cdt_trf_tx_inf=[self.create_transaction(p) for p in payments],
        )

    @validate_call
    def local_account_payment(
        self,
        payments: list[LocalAccountPayment],
        debtor_iban: SE_IBAN,
        msg_id: str,
        pmt_inf_id: str,
    ) -> str:
        doc = Document(
            cstmr_cdt_trf_initn=CustomerCreditTransferInitiationV13(
                grp_hdr=GroupHeader114(
                    msg_id=msg_id,
                    cre_dt_tm=XmlDateTime.from_datetime(datetime.datetime.now()),
                    nb_of_txs=str(len(payments)),
                    ctrl_sum=sum((p.amount for p in payments), Decimal(0)),
                    initg_pty=PartyIdentification272(),
                ),
                pmt_inf=[
                    self.create_payment_instruction(payments, debtor_iban, pmt_inf_id)
                ],
            )
        )
        serializer = XmlSerializer(
            context=XmlContext(),
            config=SerializerConfig(indent="  ", xml_declaration=True),
        )
        return serializer.render(
            doc, ns_map={None: "urn:iso:std:iso:20022:tech:xsd:pain.001.001.13"}
        )
