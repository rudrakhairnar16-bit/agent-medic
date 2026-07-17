DOCKER_ACTIONS = {
    "restart_container": {
        "description": "Restart a Docker container by service name",
        "required_params": ["service_name"],
        "timeout": 30
    },
    "scale_service": {
        "description": "Scale a Docker Compose service to N replicas",
        "required_params": ["service_name", "replicas"],
        "timeout": 60
    },
    "clear_cache": {
        "description": "Flush Redis cache",
        "required_params": ["cache_type", "host"],
        "timeout": 10
    }
}


def get_supported_actions() -> list:
    return list(DOCKER_ACTIONS.keys())


def validate_action(action_type: str, params: dict) -> bool:
    action = DOCKER_ACTIONS.get(action_type)
    if not action:
        return False
    for param in action["required_params"]:
        if param not in params:
            return False
    return True
