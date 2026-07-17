from kubernetes import client, config


def _load_config():
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()


def _detect_issue(pod):
    namespace = pod.metadata.namespace
    name = pod.metadata.name
    statuses = pod.status.container_statuses or []

    for cs in statuses:
        waiting = cs.state.waiting
        if waiting and waiting.reason in ("CrashLoopBackOff",):
            return {
                "namespace": namespace,
                "resource_name": name,
                "resource_kind": "Pod",
                "issue_type": "crashloop",
                "description": f"Pod {name} in namespace {namespace} is in CrashLoopBackOff. "
                                f"Container: {cs.name}. Message: {waiting.message}",
                "raw_details": {
                    "container": cs.name,
                    "reason": waiting.reason,
                    "message": waiting.message,
                    "restart_count": cs.restart_count,
                },
            }

        if waiting and waiting.reason in ("ImagePullBackOff", "ErrImagePull"):
            return {
                "namespace": namespace,
                "resource_name": name,
                "resource_kind": "Pod",
                "issue_type": "image_pull_error",
                "description": f"Pod {name} in namespace {namespace} cannot pull its image. "
                                f"Container: {cs.name}. Message: {waiting.message}",
                "raw_details": {
                    "container": cs.name,
                    "reason": waiting.reason,
                    "message": waiting.message,
                },
            }

        last_terminated = cs.last_state.terminated if cs.last_state else None
        if last_terminated and last_terminated.reason == "OOMKilled":
            return {
                "namespace": namespace,
                "resource_name": name,
                "resource_kind": "Pod",
                "issue_type": "oom_killed",
                "description": f"Pod {name} in namespace {namespace} was OOMKilled. "
                                f"Container: {cs.name}.",
                "raw_details": {
                    "container": cs.name,
                    "reason": last_terminated.reason,
                    "exit_code": last_terminated.exit_code,
                },
            }

    return None


def scan_namespace(namespace="default"):
    _load_config()
    v1 = client.CoreV1Api()
    pods = v1.list_namespaced_pod(namespace)

    incidents = []
    for pod in pods.items:
        issue = _detect_issue(pod)
        if issue:
            incidents.append(issue)

    return incidents