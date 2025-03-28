from huobi.connection.restapi_sync_client import RestApiSyncClient
from huobi.constant import *
from huobi.model.margin.general_repay_loan_result import GeneralRepayLoanResult
from huobi.utils.json_parser import default_parse_list_dict


class PostGeneralRepayLoanService:

    def __init__(self, params):
        self.params = params

    def request(self, **kwargs):
        def get_channel():
            path = "/v2/account/repayment"
            return path

        def parse(dict_data):
            return default_parse_list_dict(dict_data.get("data", {}), GeneralRepayLoanResult)

        return RestApiSyncClient(**kwargs).request_process(HttpMethod.POST_SIGN, get_channel(), self.params, parse)
