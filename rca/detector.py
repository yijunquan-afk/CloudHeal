from rca.preprocess import get_span_list
from rca.preprocess import get_service_operation_list
from rca.preprocess import get_operation_duration_data
from rca.preprocess import get_operation_slo
from rca.preprocess import get_pagerank_graph
from datetime import datetime
from injector.log import Logger
import logging

log_path = './log/' + str(datetime.now().strftime(
    '%Y-%m-%d')) + '-experiment.log'
logger = Logger(log_path, logging.DEBUG, __name__).getlog()

def get_slo(start_time=None, end_time=None, test_time=None):
    span_list = get_span_list(test_time=test_time)
    operation_list = get_service_operation_list(span_list)
    slo = get_operation_slo(service_operation_list=operation_list, span_list=span_list)
    return slo


def system_anomaly_detect(span_list, slo):
    if len(span_list) == 0:
        # print("Error: Current span list is empty ")
        return False
    operation_list = get_service_operation_list(span_list)
    operation_count = get_operation_duration_data(operation_list, span_list)

    anomaly_trace = 0
    total_trace = 0
    duration_dict = {}
    for trace_id in operation_count:
        total_trace += 1
        single_result = trace_anomaly_detect(operation_count[trace_id], slo)
        if single_result:
            anomaly_trace+=1
    
    anomaly_rate = float(anomaly_trace) / total_trace
    logger.info(f"anomaly_rate: {anomaly_rate}")
    if anomaly_rate > 0.03:
        # print("System occurs errors!")
        return True

    else:
        return False


def trace_anomaly_detect(single_trace_operations, slo):
    expect_duration = 0.0
    real_duration = float(single_trace_operations["duration"]) / 1000.0
    for operation in single_trace_operations:
        if operation == "duration":
            continue
        expect_duration += single_trace_operations[operation] * (
            slo[operation][0] + 2 *  slo[operation][1]
        )

    if real_duration > expect_duration:

        return True
    else:
        return False


def trace_list_partition(operation_count, slo):
    normal_list = []  # normal traceid list
    abnormal_list = []  # abnormal traceid list
    for traceid in operation_count:
        normal = trace_anomaly_detect(
            single_trace_operations=operation_count[traceid], slo=slo
        )
        if normal:
            abnormal_list.append(traceid)
        else:
            normal_list.append(traceid)

    return abnormal_list, normal_list


if __name__ == "__main__":
    operation_slo = get_slo(test_time="2024-05-25:09_59")

    print(operation_slo)



