from huobi.model.market import Mbp, PriceDepth


class MbpReq:
    """
    The market price depth.

    :member
        rep: request Topic
        id: The UNIX formatted timestamp generated by server in UTC.
        data: The price depth.
    """

    def __init__(self):
        self.rep = ""
        self.id = ""

        self.data = Mbp()

    @staticmethod
    def json_parse(data_json):
        mbp_event = MbpReq()
        mbp_event.id = data_json.get("id")
        mbp_event.rep = data_json.get("rep")
        data = data_json.get("data", {})
        mbp = Mbp.json_parse(data)
        mbp_event.data = mbp
        return mbp_event

    def print_object(self, format_data=""):
        from huobi.utils.print_mix_object import PrintBasic
        PrintBasic.print_basic(self.rep, format_data + "Topic")
        PrintBasic.print_basic(self.id, format_data + "Timestamp")

        self.data.print_object(format_data + "\t")