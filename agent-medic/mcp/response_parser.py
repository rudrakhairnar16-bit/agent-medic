class MCPResponseParser:
    @staticmethod
    def parse_traces(response: dict) -> list:
        result = response.get("result", [])
        if isinstance(result, list):
            return result
        return []

    @staticmethod
    def parse_metrics(response: dict) -> list:
        result = response.get("result", [])
        if isinstance(result, list):
            return result
        return []

    @staticmethod
    def parse_logs(response: dict) -> list:
        result = response.get("result", [])
        if isinstance(result, list):
            return result
        return []

    @staticmethod
    def has_error(response: dict) -> bool:
        return "error" in response or "Error" in str(response)


parser = MCPResponseParser()
