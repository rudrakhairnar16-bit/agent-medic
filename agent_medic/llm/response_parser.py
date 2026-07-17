from llm.engine import _parse_llm

response_parser = type("LP", (), {"parse": staticmethod(_parse_llm)})()
