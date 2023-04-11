## k8s Cleanup Job
# Author: Abhijeet Kamble

# Purpose
# To cleanup the k8s pods, deployments, services if they are older than specific days.

from kubernetes import client, config
from datetime import timedelta, datetime
import pytz
import logging
import os

##### Environment Variables #########
# Only pods below status are going to get deleted
# STATUS:  "Pending, Running, Succeeded, Failed, Unknown"
podStatus = os.environ["POD_STATUS"].replace(' ', '').split(",")
maxDays = int(os.environ["EXPIRY_DAYS"])
namespace_exclusions = os.environ["EXCLUDE_NAMESPACES"]
##### Environment Variables End #########
# load config from cluster

logging.basicConfig(level=logging.INFO)

# Configs can be set in Configuration class directly or using helper utility
# config.load_kube_config()
config.load_incluster_config()

v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()

ret = v1.list_pod_for_all_namespaces()

# Get Current Date.
today = datetime.now(tz=pytz.UTC)

# Metrics for Pods
totalPods = 0
expiredPods = 0
notExpiredPods = 0
ignoredPods = 0

namespace_exclusions = list(namespace_exclusions.split(","))
namespace_to_ignore = ['kube-system', 'cert-manager', 'ingress-nginx', 'newreclic', 'kube-public', 'kube-node-lease']
namespace_to_ignore = namespace_to_ignore + namespace_exclusions


def kill_resources(metadata, pod_name, pod_namespace):
    # give here condition that if owner_refrence present and it has replica set then move ahead or else delete the pod itself
    replicaset_name = metadata.owner_references[0].name
    replicaset_data = apps_v1.read_namespaced_replica_set(name=replicaset_name, namespace=pod_namespace)
    deployment_name = replicaset_data.metadata.owner_references[0].name
    logging.info("Contenders for Deletion..")
    logging.info("Replica Set: %s", replicaset_name)
    logging.info("Deployment: %s", deployment_name)
    logging.info("Pod Name: %s", pod_name)
    delete_deployment(deployment_name, pod_namespace)


def delete_pod(pod_name, pod_namespace):
    try:
        status = v1.delete_namespaced_pod(name=pod_name, namespace=pod_namespace)
        print(status)
    except BaseException as exe:
        logging.error(exe)


def check_namespaces_resources():
    try:
        ns_list = v1.list_namespace()
        for ns in ns_list.items:
            if ns.metadata.name not in namespace_to_ignore:
                logging.info("%s namespace is getting checked for resources from check_namespaces_resources", ns.metadata.name)
                check_namespace_resources(ns.metadata.name)
    except BaseException as exe:
        logging.error(exe)


def delete_namespace(namespace):
    try:
        v1.delete_namespace(name=namespace)
    except BaseException as exe:
        logging.error(exe)


def check_namespace_resources(namespace):
    try:
        pods = v1.list_namespaced_pod(namespace=namespace)
        logging.info("%s namespace is getting checked for resources", namespace)
        if len(pods.items) == 0:
            logging.info("%s namespace is getting deleted", namespace)
            delete_namespace(namespace)
    except BaseException as exe:
        logging.error(exe)


def delete_deployment(deployment_name, pod_namespace):
    try:
        apps_v1.delete_namespaced_deployment(name=deployment_name, namespace=pod_namespace)
        logging.info("Deployment Deleted: %s from %s namespace", deployment_name, pod_namespace)
    except BaseException as exe:
        logging.error(exe)


def debug_log():
    logging.info("Currently deleting pods for following status: %s", podStatus)
    logging.warning("Bypassing Namespaces: %s", namespace_to_ignore)


def reset_summary():
    global totalPods, expiredPods, notExpiredPods, ignoredPods
    totalPods = 0
    expiredPods = 0
    notExpiredPods = 0
    ignoredPods = 0


def print_summary():
    logging.info("---summary---")
    logging.info("Total Pods: %s", totalPods)
    logging.info("Expired Pods: %s", expiredPods)
    logging.info("Not Expired Pods: %s", notExpiredPods)
    logging.info("Ignored Pods: %s", ignoredPods)


def evaluate_pods():
    global totalPods, expiredPods, notExpiredPods, ignoredPods, maxDays
    for i in ret.items:
        totalPods = totalPods + 1;
        count = namespace_to_ignore.count(i.metadata.namespace)
        if count == 0:
            logging.info("Checking pod for expiry: %s", i.metadata.name)
            pod_current_status = i.status.phase
            if podStatus.count(pod_current_status) > 0:
                podStartTime = i.status.start_time
                deadlineTime = podStartTime + timedelta(days=maxDays)
                if deadlineTime < today:
                    expiredPods = expiredPods + 1
                    logging.info("pod is expired and ready for deletion..")
                    logging.info("%s\t%s\t%s\t%s\t%s" % (
                        i.status.pod_ip, i.metadata.namespace, i.metadata.name, i.status.start_time, deadlineTime))
                else:
                    notExpiredPods = notExpiredPods + 1
                    logging.info("Pod is not expired")
            else:
                ignoredPods = ignoredPods + 1
                logging.info("Skipping pod as pod is in : %s", pod_current_status)
        else:
            ignoredPods = ignoredPods + 1
            logging.info("Skipping as namespace is present in exclude list: %s", i.metadata.namespace)


def kill_pods():
    global totalPods, expiredPods, notExpiredPods, ignoredPods, maxDays
    for i in ret.items:
        totalPods = totalPods + 1;
        count = namespace_to_ignore.count(i.metadata.namespace)
        if count == 0:
            logging.info("Checking pod for expiry: %s", i.metadata.name)
            pod_current_status = i.status.phase
            if podStatus.count(pod_current_status) > 0:
                podStartTime = i.status.start_time
                deadlineTime = podStartTime + timedelta(days=maxDays)
                if deadlineTime < today:
                    expiredPods = expiredPods + 1
                    logging.info("pod is expired and ready for deletion..")
                    logging.info("%s\t%s\t%s\t%s\t%s" % (
                        i.status.pod_ip, i.metadata.namespace, i.metadata.name, i.status.start_time, deadlineTime))
                    kill_resources(i.metadata, i.metadata.name, i.metadata.namespace)
                    check_namespace_resources(i.metadata.namespace)
                else:
                    notExpiredPods = notExpiredPods + 1
                    logging.info("Pod is not expired")
            else:
                ignoredPods = ignoredPods + 1
                logging.info("Skipping pod as pod is in : %s", pod_current_status)
        else:
            ignoredPods = ignoredPods + 1
            logging.info("Skipping as namespace is present in exclude list: %s", i.metadata.namespace)


def main():
    logging.info("========================Starting pods Cleanup Program =======================")
    debug_log()
    reset_summary()
    evaluate_pods()
    print_summary()
    logging.info("========================Starting Cleanup=======================")
    reset_summary()
    kill_pods()
    check_namespaces_resources()
    logging.info("========================Post Cleanup===========================")
    print_summary()
    logging.info("========================Starting pods Cleanup Program END =======================")


# Checks to execute ###

#### Here we go ###
main()
