import paramiko
import os
from datetime import datetime
import logging
import warnings
import time
import re
import random

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)
log_path = 'action.log'
file_handler = logging.FileHandler(log_path)
formatter = logging.Formatter("%(asctime)s\t%(levelname)s\t%(message)s",
                              datefmt="%Y-%m-%d %H:%M:%S")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)


ns = "hipster"
deploy_nodes = [
]
def get_total_pod_name():
    command = "kubectl get pod -n %s| awk '{print $1}'" %(ns)
    temp = os.popen(command).read().split('\n')[1:]
    pods = []
    for pod in temp:
        if "load" in pod or "redis" in pod or "mysql" in pod or pod == '':
            continue
        pods.append(pod)
    return pods
    

def get_node_name(pod_name):
    command = "kubectl get pod -n %s -o wide | grep %s | awk '{print $7}'" % (
        ns, pod_name)
    node = os.popen(command).read()

    if "\n" in node:
        node = node.strip("\n")
    return node


def get_pod_name(service):
    command = "kubectl get pod -n %s -o wide | grep %s| awk '{print $1}'" % (
        ns, service)
    pod_name = os.popen(command).read()

    pod_list = []
    if "\n" in pod_name:
        for line in pod_name.strip("\n").split("\n"):
            pod_list.append(line)

    return pod_list[random.randint(0, len(pod_list) - 1)]

def get_pod_name_v2(service):
    command = "kubectl get pod -n %s -o wide | grep %s| awk '{print $1}'" % (
        ns, service)
    pod_name = os.popen(command).read()

    if "\n" in pod_name:
        for line in pod_name.strip("\n").split("\n"):
            if "v2" in line:
                return line

    return ""

def wait_for_all_pods_ready(service_name, namespace):
    while True:
        try:
            jsonpath = "{range .items[*]}{.status.containerStatuses[*].ready}{'\\n'}{end}"
            command = f"""kubectl get pod -l app={service_name} -n {namespace} -o jsonpath='{jsonpath}' | grep -c true """
            all_ready = os.popen(command).read()
            total_pods_info = os.popen(f"kubectl get pod -l app={service_name} -n {namespace} --no-headers").read().strip()
            total_pods = len(total_pods_info.split("\n"))
            if all_ready == total_pods:
                break
        except Exception as e:
            print("An error occurred:", e)
        
        time.sleep(1)


def wait_for_ready(service, old_pod):
    start_time = int(time.time())
    while True:
        command = 'kubectl get pod -n %s -o wide | grep "%s"' % (ns, service)
        ready_result = os.popen(command).read()
        cur_pod = re.split(r'\s+', ready_result)[0]
        is_ready = re.split(r'\s+', ready_result)[1]

        if cur_pod != old_pod and is_ready == "2/2":
            logger.info("container %s ready" % (cur_pod))
            return True
        current_time = int(time.time())
        if current_time - start_time > 300:
            logger.error("container %s start fails" % (pod_name))
            return False


def reboot_container(pod_name, container_name="server"):
    node = get_node_name(pod_name=pod_name)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(node, 22, 'root', '******')
    get_docker_id_command = 'docker ps --format "{{.ID}}\\t{{.Image}}\\t{{.Names}}" | grep %s_%s  | awk \'{print $1}\' ' % (
        container_name, pod_name)
    _, stdout, _ = ssh.exec_command(get_docker_id_command)
    docker_id = bytes.decode(stdout.read())

    if "\n" in docker_id:
        docker_id = docker_id.strip("\n")
    container_restart_command = "docker restart %s" % (docker_id)
    print(container_restart_command)
    try:
        ssh.exec_command(container_restart_command)
        return True
    except Exception as e:
        return False


def restart(pod_name):
    restart_start_time = time.time()
    node = get_node_name(pod_name=pod_name)
    service = pod_name.split("_")[0]
    logger.info("Restrict the nodes")
    for temp_node in deploy_nodes:
        if temp_node != node:
            os.popen("kubectl cordon %s" % (temp_node))
    delete_command = "kubectl delete pod -n %s %s" % (ns, pod_name)
    try:
        os.popen(delete_command)
        logger.info(delete_command)
    except Exception as e:
        logger.error(e)
    logger.info(f"Restart the pod {pod_name}")
    service = pod_name.split("-")[0]
    new_pod = ""
    command = 'kubectl get pod -n hipster | grep "%s" | awk \'{print $2}\'' % (service)
    replicas = len(os.popen(command).read().split('\n')[:-1])
    try:
        s_time = time.time()
        while(time.time()-s_time < 60):
            status = os.popen(command).read().split('\n')[:-1]
            replicas_temp = len(status)
            flag = True
            # print(status)
            for statu in status:
                if statu != "2/2":
                    flag = False
            if flag:
                break
        # wait_command = f"kubectl wait --for=condition=Ready pod -l app={service} -n {ns} --timeout=90s"
        # os.popen(wait_command)
        # logger.info(wait_command)
        get_pod_command = f"kubectl get pod -l app={service} -n {ns} --sort-by=.metadata.creationTimestamp"
        result = os.popen(get_pod_command).read()
        new_pod = result.strip().split("\n")[-1].split()[0]
        logger.info(f"New pod: {new_pod}")
    except Exception as e:
        logger.error(e)
    for temp_node in deploy_nodes:
        if temp_node != node:
            os.popen("kubectl uncordon %s" % (temp_node))
    restart_end_time = time.time()   
    restart_duration = int(restart_end_time - restart_start_time)
    logger.info(f"Restart duration: {restart_duration}")
    return new_pod




def migrate(pod_name):
    migrate_start_time = time.time()
    node = get_node_name(pod_name=pod_name)
    service = pod_name.split("-")[0]
    new_pod = ""

    cordon_command = "kubectl cordon %s" % (node)
    migrate_command = "kubectl delete pod %s -n %s" % (pod_name, ns)
    uncordon_command = "kubectl uncordon %s" % (node)
    wait_command = f"kubectl wait --for=condition=Ready pod -l app={service} -n {ns} --timeout=90s"
    get_pod_command = f"kubectl get pod -l app={service} -n {ns} --sort-by=.metadata.creationTimestamp"
    try:
        os.popen(cordon_command)
        logger.info(cordon_command)
        os.popen(migrate_command)
        logger.info(migrate_command)
        os.popen(wait_command)
        logger.info(wait_command)
        time.sleep(5)
        result = os.popen(get_pod_command).read()
        new_pod = result.strip().split("\n")[-1].split()[0]
        logger.info(f"Create a new pod: {new_pod}")
        new_node = get_node_name(pod_name=new_pod)
        logger.info(f"Migrate from {node} to {new_node} Successful! New pod: {new_pod}")
        migrate_end_time = time.time()
        time.sleep(10)
        os.popen(uncordon_command)
        logger.info(uncordon_command)
    except Exception as e:
        logger.error(e)
    migrate_duration = int(migrate_end_time - migrate_start_time)
    logger.info(f"Migrate duration: {migrate_duration}")
    return new_pod




def rollback(pod_name):
    deployment = pod_name.split("-")[0]+ "-"+ pod_name.split("-")[1]
    if "v2" not in deployment:
        return False
    command1 = "kubectl delete deployment %s -n %s" % (deployment, ns)
    delete_result = os.popen(command1).read()
    logger.info(delete_result)
    origin_deployment =  pod_name.split("-")[0]
    replicas = 2
    command2 = "kubectl scale deployment/%s --replicas  %s -n %s" % (origin_deployment, replicas, ns)
    scale_result = os.popen(command2).read()
    if "frontend" in pod_name:
        command3 = "kubectl rollout restart deployment loadgenerator -n %s" % (ns)
        os.popen(command3).read()
        logger.info(command3)
    logger.info(scale_result)
    return True


def flow_control(pod_name):
    service = pod_name.split("-")[0]
    yaml = f"recovery/yaml/ratelimit_{service}.yaml"
    command = f"kubectl apply -f {yaml} -n {ns}"
    result = os.popen(command).read()
    logger.info(command)
    return True

def cancel_flow_control(pod_name):
    service = pod_name.split("-")[0]
    yaml = f"recovery/yaml/ratelimit_{service}.yaml"
    command = f"kubectl delete -f {yaml} -n {ns}"
    result = os.popen(command).read()
    return True

def restart_loadgenerator():
    pod = get_pod_name("load")
    command = f"kubectl delete pod {pod} -n {ns}"
    result = os.popen(command).read()
    return 
