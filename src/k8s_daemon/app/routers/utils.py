from kubernetes import client, config
from kubernetes.client import configuration
from kubernetes.stream import stream
import multiprocessing as mp
import redis

import app.cluster_info.config as clusters

#REDIS_HOST = "redis_pubsub_traces"
#TODO: Change to .env
REDIS_HOST = "10.3.3.223"
REDIS_PORT = 6379
DS_CONTAINER_NAME = "sysdig"
DS_CONTAINER_IMAGE = "usherlock/collector:latest"


class SysdigMonitor:
    def __init__(self, cluster_name, app_name, pod_name):
        self.cluster_name = cluster_name
        self.app_name = app_name
        self.pod_name = pod_name
        self.condition = mp.Condition()
        self.sysdig_process = None

    def start_monitoring(self, namespace, params, filters):
        self.sysdig_process = mp.Process(
            target=sysdig_collect_and_send,
            args=(
                self.condition,
                self.cluster_name,
                self.app_name,
                self.pod_name,
                namespace,
                params,
                filters,
            ),
        )
        self.sysdig_process.start()

    def update_monitoring(self, namespace, params, filters):
        self.stop_monitoring()
        self.start_monitoring(namespace, params, filters)

    def stop_monitoring(self):
        with self.condition:
            self.condition.notify_all()
        self.sysdig_process.join()
        self.sysdig_process = None


def sysdig_collect_and_send(
    condition, cluster_name, app_name, name, namespace, params, filters
):
    # config.load_kube_config()
    # configuration.assert_hostname = False
    # api_instance = client.CoreV1Api()
    api_instance = clusters.get_corev1_api_client(cluster_name)

    with condition:
        resp = stream(
            api_instance.connect_get_namespaced_pod_exec,
            name,
            namespace,
            container=DS_CONTAINER_NAME,
            command=["./usherlock_collector", ' '.join(params), " or ".join(filters), REDIS_HOST, app_name, "-p", str(REDIS_PORT), "-w", "2"],
            stderr=False,
            stdin=True,
            stdout=True,
            tty=False,
            _preload_content=False,
        )

        proc_pid = None
        while not proc_pid and resp.is_open():
            resp.update(timeout=3)
            if resp.peek_stdout():
                proc_pid = resp.read_stdout()

        condition.wait()
    resp.close()

    # Terminate sysdig command on pod
    # api_instance = client.CoreV1Api()
    api_instance = clusters.get_corev1_api_client(cluster_name)
    exec_command = ["/bin/sh", "-c", f"kill -15 {proc_pid}"]
    stream(
        api_instance.connect_get_namespaced_pod_exec,
        name,
        namespace,
        container=DS_CONTAINER_NAME,
        command=exec_command,
        stderr=False,
        stdin=False,
        stdout=True,
        tty=False,
    )

    redis_pub = redis.StrictRedis(
        "redis_pubsub_traces", 6379, charset="utf-8", decode_responses=True
    )
    redis_pub.publish(app_name, "CLOSE")

    return


def create_monitoring_daemon_set_object(name, nodes_taints=[]):
    # Volume Mounts
    volume_mounts = [
        client.V1VolumeMount(
            mount_path="/host/var/run/docker.sock",
            name="docker-sock",
            read_only=False,
        ),
        client.V1VolumeMount(
            mount_path="/host/dev",
            name="dev-vol",
            read_only=False,
        ),
        client.V1VolumeMount(
            mount_path="/host/proc",
            name="proc-vol",
            read_only=True,
        ),
        client.V1VolumeMount(
            mount_path="/host/boot",
            name="boot-vol",
            read_only=True,
        ),
        client.V1VolumeMount(
            mount_path="/host/lib/modules",
            name="modules-vol",
            read_only=True,
        ),
        client.V1VolumeMount(
            mount_path="/host/usr",
            name="usr-vol",
            read_only=True,
        ),
    ]

    # Tolerations
    tolerations = [
        client.V1Toleration(
            effect="NoSchedule",
            key="nodePermit",
            operator="Equal",
            value=f"{taint}",
        )
        for taint in nodes_taints
    ]

    # Volumes
    volumes = [
        client.V1Volume(
            name="docker-sock",
            host_path=client.V1HostPathVolumeSource(path="/var/run/docker.sock"),
        ),
        client.V1Volume(
            name="dev-vol", host_path=client.V1HostPathVolumeSource(path="/dev")
        ),
        client.V1Volume(
            name="proc-vol", host_path=client.V1HostPathVolumeSource(path="/proc")
        ),
        client.V1Volume(
            name="boot-vol", host_path=client.V1HostPathVolumeSource(path="/boot")
        ),
        client.V1Volume(
            name="modules-vol",
            host_path=client.V1HostPathVolumeSource(path="/lib/modules"),
        ),
        client.V1Volume(
            name="usr-vol", host_path=client.V1HostPathVolumeSource(path="/usr")
        ),
    ]

    # Containers
    container = client.V1Container(
        name=DS_CONTAINER_NAME,
        image=DS_CONTAINER_IMAGE,
        # image="usherlock-daemon:latest",
        image_pull_policy="IfNotPresent",
        # ports=[client.V1ContainerPort(container_port=6379)],
        command=["tail", "-f", "/dev/null"],
        security_context=client.V1SecurityContext(privileged=True),
        volume_mounts=volume_mounts,
    )

    # Template
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"name": f"{name}"}),
        spec=client.V1PodSpec(
            host_network=True,
            host_pid=True,
            containers=[container],
            tolerations=tolerations,
            volumes=volumes,
        ),
    )

    # Spec
    spec = client.V1DaemonSetSpec(
        selector=client.V1LabelSelector(match_labels={"name": f"{name}"}),
        template=template,
    )

    # DaemonSet
    daemonset = client.V1DaemonSet(
        api_version="apps/v1",
        kind="DaemonSet",
        metadata=client.V1ObjectMeta(name=name),
        spec=spec,
    )

    return daemonset
