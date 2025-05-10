from query.metric_query import MonitorPod
from query.log_query import get_trace_ids
from query.trace_query import query_trace_total
from sh.action import *
from sh.mab import *
from rca.detector import *
from rca.preprocess import *
from rca.pagerank import *
from rca.sbfl import *
from injector.log import Logger

import os
import csv
import random
import time
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pickle
import logging
import warnings

warnings.filterwarnings('ignore')

METRIC_ENDPOINT = "http://x.x.x.x:xxxx/"
TRACE_ENDPOINT = "http://x.x.x.x:xxxx/"
LOG_ENDPOINT = "http://x.x.x.x:xxxx/"

log_path = './log/' + str(datetime.now().strftime(
    '%Y-%m-%d')) + '-experiment.log'
logger = Logger(log_path, logging.DEBUG, __name__).getlog()

pod_detector = MonitorPod(endpoint = METRIC_ENDPOINT)
pods = get_total_pod_name()
service_list = [
            "adservice", "cartservice", "checkoutservice", "currencyservice",
            "emailservice", "paymentservice", "productcatalogservice", 
            "recommendationservice",  "frontend", "shippingservice"
]



def create_directory_if_not_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"file '{directory}' created successfully.")
    else:
        logger.info(f"file '{directory}' exists.")



def create_file():
    current_time = datetime.now()
    for service in service_list:
        history_file = f'./data/recovery-history/{service}.csv'
        if not os.path.exists(history_file):
            with open(history_file, 'w', newline='') as file:
                writer = csv.writer(file)     
                writer.writerow([
                    "time", "pod_name", "cpu", "memory", "syscall_read", 
                    "syscall_write", "net_receive", "net_send", 
                    "net_latency", "run_time", "action", "success"
                ])

    create_directory_if_not_exists(f'./data/{datetime.strftime(current_time, "%Y-%m-%d")}/metric')
    for pod_name in pods:
        metric_file = f'./data/{datetime.strftime(current_time, "%Y-%m-%d")}/metric/{pod_name}.csv'
        if not os.path.exists(metric_file):
            with open(metric_file, 'w', newline='') as file:
                writer = csv.writer(file)    
                writer.writerow([
                    "time", "pod_name", "cpu", "memory", "syscall_read", 
                    "syscall_write", "net_receive", "net_send", 
                    "net_latency", "run_time"
                ])
    create_directory_if_not_exists(f'./data/{datetime.strftime(current_time, "%Y-%m-%d")}/trace')

def monitor(pod_name, metric_name, ago_time, current_time):
    if metric_name == "cpu":
        result = pod_detector.get_cpu_use_rate(ago_time, current_time,
                                               pod_name)
    elif metric_name == "memory":
        result = pod_detector.get_memory_usage(ago_time, current_time,
                                               pod_name)
    elif metric_name == "io":
        result = pod_detector.get_IO_throughput(ago_time, current_time,
                                                pod_name)
    elif metric_name == "net_receive":
        result = pod_detector.get_network_received_packets(
            ago_time, current_time, pod_name)
    elif metric_name == "net_send":
        result = pod_detector.get_network_transmitted_packets(
            ago_time, current_time, pod_name)
    elif metric_name == "net_latency":       
        result = pod_detector.get_latency(
            ago_time, current_time, pod_name)
    elif metric_name == "syscall_read":       
        result = pod_detector.get_syscall_read(
            ago_time, current_time, pod_name)    
    elif metric_name == "syscall_write":       
        result = pod_detector.get_syscall_write(
            ago_time, current_time, pod_name)   
    elif metric_name == "run_time":
        try:
            result = pod_detector.get_update_time(ago_time, current_time, pod_name)
            data_origin = np.array(result[0]['values'])[:,1].reshape(-1,1).astype(float)
            current_state = round(data_origin[-1][0], 4)
        except:
            return 0
        return current_state
    if result == []:
        return  0
    data_origin = np.array(result[0]['values'])[:, 1].reshape(-1, 1).astype(float)
    current_state = round(data_origin[-1][0], 4)
    return current_state

def query_metric(current_time):
    sorted_metric = [
        "cpu", "memory", "syscall_read",  "syscall_write",  "net_receive", "net_send", 'net_latency', "run_time"
    ]
    for pod_name in pods:
        metric_file = f'./data/{datetime.strftime(current_time, "%Y-%m-%d")}/metric/{pod_name}.csv'
        current_timestamp = int(current_time.timestamp())
        ago_time = current_timestamp - 60
        state_vector = []
        state_vector.append(datetime.strftime(current_time, "%Y-%m-%d %H:%M:%S"))
        for metric in sorted_metric:
            state = monitor(pod_name, metric, ago_time, current_timestamp)
            state_vector.append(state)
        with open(metric_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(state_vector)

def get_pod_state_vector(pod_name, current_time):
    sorted_metric = [
        "cpu", "memory", "syscall_read",  "syscall_write",  "net_receive", "net_send", 'net_latency', "run_time"
    ]
    current_timestamp = int(current_time.timestamp())
    ago_time = current_timestamp - 60
    state_vector = []
    for metric in sorted_metric:
        state = monitor(pod_name, metric, ago_time, current_timestamp)
        state_vector.append(state)
    return state_vector



def query_trace(start, end, limit = 800):
    file_name = f'./data/{datetime.strftime(end, "%Y-%m-%d")}/trace/{datetime.strftime(end, "%H_%M")}_trace.csv'
    traceids = get_trace_ids(
        endpoint=LOG_ENDPOINT, namespace="hipster", start=start, end=end, limit = limit
    )
    logger.info(f"Trace number: {len(traceids)}")
    query_trace_total(
        endpoint=TRACE_ENDPOINT, traceids=traceids, file_name=file_name
    )
    logger.info(f"Query time: {datetime.now() - end}")

def get_system_slo():
    start = datetime(2025, 2, 17, 10, 42, 0)
    end = datetime(2025, 2, 17, 11, 11, 0)
    span_list = get_span_list(start_time = start, end_time = end)
    operation_list = get_service_operation_list(span_list)
    slo = get_operation_slo(service_operation_list=operation_list, span_list=span_list)
    return slo, operation_list

def rca(slo, rca_time, operation_feedback, pagerank_flag=True, spectrum_method="dstar2"):
    span_list_suffering = pd.concat(
        [
            get_span_list(detect_time=rca_time)
        ],
        axis=0,
    )

    service_operation_list = get_service_operation_list(span_list_suffering)
    operation_dict = get_operation_duration_data(
        service_operation_list, span_list_suffering
    )

    abnormal_trace_list, normal_trace_list = trace_list_partition(
        operation_dict, slo
    )

    (
        abnormal_operation_operation,
        abnormal_operation_trace,
        abnormal_trace_operation,
        abnormal_pr_trace,
    ) = get_pagerank_graph(abnormal_trace_list, span_list_suffering)

    abnormal_operation_name, abnormal_call_graph = get_call_graph(abnormal_operation_operation)
    abnormal_num_list = get_trace_num_list(abnormal_trace_operation)
    num = len(abnormal_operation_name)
    R = np.array([1 for i in range(num)])
    T = np.array([1 for i in range(num)])
    
    for service in operation_feedback:
        i = 0
        for name in abnormal_operation_name:
            if service in name :
                R[i] = operation_feedback[service][0]
                T[i] = operation_feedback[service][1]
            i += 1

    abnormal_trace_result = pagerank(
        abnormal_operation_name,
        abnormal_call_graph,
        R,
        T
    )

    (
        normal_operation_operation,
        normal_operation_trace,
        normal_trace_operation,
        normal_pr_trace,
    ) = get_pagerank_graph(normal_trace_list, span_list_suffering)

    normal_operation_name, normal_call_graph = get_call_graph(normal_operation_operation)
    normal_num_list = get_trace_num_list(normal_trace_operation)
    num = len(normal_operation_name)
    
    R = np.array([1 for i in range(num)])
    T = np.array([1 for i in range(num)])

    for service in operation_feedback:
        i = 0
        for name in normal_operation_name:
            if service in name :
                R[i] = operation_feedback[service][0]
                T[i] = operation_feedback[service][1]
            i += 1

    normal_trace_result = pagerank(
        normal_operation_name,
        normal_call_graph,
        R,
        T
    )
    top_list, score_list = calculate_spectrum(
        anomaly_result=abnormal_trace_result,
        normal_result=normal_trace_result,
        anomaly_list_len=len(abnormal_trace_list),
        normal_list_len=len(normal_trace_list),
        top_max=50,
        anomaly_num_list=abnormal_num_list,
        normal_num_list=normal_num_list,
        spectrum_method = spectrum_method,
        delay_list = None,
        pagerank = pagerank_flag
    )
    return top_list, score_list

if __name__ == "__main__":
    with open("slo.pkl", "rb") as f:
      slo, operation_list = pickle.load(f)
    create_file()
    logger.info("Online Self-healing Experiment Start!")
    if os.path.exists("rca.pkl"):
        logger.info("load model")
        with open("rca.pkl", "rb") as f:
            operation_feedback = pickle.load(f)
    else:
        operation_feedback = {}
        for service in service_list:
            operation_feedback[service] = [1, 1, init_time]
    test = False
    init_time = datetime.now()
    # test = True
    if test:
        current_time = datetime(2025,2,21,21,31,0)
        span_list_current = get_span_list(detect_time=current_time)
        detect_result = system_anomaly_detect(span_list=span_list_current, slo=slo)
        if detect_result:
            # print(detect_result)
            top_list, score_list = rca(
                slo=slo,
                rca_time=current_time,
                operation_feedback=operation_feedback,
                pagerank_flag=True,
                spectrum_method="dstar2",
            )
            rca_result = []
            rca_score = []
            i = 0
            for operation in top_list:
                pod = operation.split("_")[0]
                if pod not in rca_result:
                    rca_result.append(pod)
                    rca_score.append(score_list[i])
                i+=1
            for i in range(len(rca_result)):
                logger.info('%-50s: %.8f' % (rca_result[i], rca_score[i])) 
    j = 10
    while(j > 0): 
        j -= 1
        current_time = datetime.now()

        s_time = time.time()
        start = current_time - timedelta(minutes=1)
        end = current_time
        query_trace(start, end)
        span_list_current = get_span_list(detect_time=current_time)
        detect_result = system_anomaly_detect(span_list=span_list_current, slo=slo)
        query_metric(current_time)
   
        operation_feedback = {}
        for service in service_list:
                operation_feedback[service] = [1, 1, init_time]
            
        if  detect_result:
            logger.error("System occurs errors!")
            top_list, score_list = rca(
                slo=slo,
                rca_time=current_time,
                operation_feedback=operation_feedback,
                pagerank_flag=True,
                spectrum_method="ochiai",
            )
            rca_result = []
            rca_score = []
            i = 0
            for operation in top_list:
                pod = operation.split("_")[0]
                if pod not in rca_result:
                    rca_result.append(pod)
                    rca_score.append(score_list[i])
                i+=1
            for i in range(len(rca_result)):
                logger.info('%-50s: %.8f' % (rca_result[i], rca_score[i])) 
                
        else:
            logger.info("System is healthy.")
        e_time = time.time()
        sleep_time = 60-int(e_time-s_time)
        if sleep_time > 0:
             time.sleep(sleep_time)
        
            
s = set()
s.       
random.randint()