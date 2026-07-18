from llm.engine import _parse_llm

class ResponseParser:
    parse = staticmethod(_parse_llm)

response_parser = ResponseParser()
