import numpy as np
import pandas as pd
import os
from copy import deepcopy
from datetime import datetime,timedelta
root_index = "root"


def get_service_operation_name(span):
    service_name = span["PodName"].split("-")[0]
    operation_name = span["OperationName"].split("/")[-1]
    return service_name + "_" + operation_name


def get_service_operation_name2(span):
    service_name = span["PodName"]
    operation_name = span["OperationName"].split("/")[-1]
    return service_name + "_" + operation_name


def init_operation_dict(operation_list, operation_dict, trace_id):
    if trace_id not in operation_dict:
        operation_dict[trace_id] = {}
        for operation in operation_list:
            operation_dict[trace_id][operation] = 0
        operation_dict[trace_id]["duration"] = 0


def get_span_list(start_time=None, end_time=None, detect_time=None):
    if detect_time == None:
        temp = []
        while(start_time <= end_time):
            trace_file = "../data/" + datetime.strftime(start_time, "%Y-%m-%d/trace/%H_%M") + "_trace.csv"
            if not os.path.exists(trace_file):
                start_time = start_time + timedelta(minutes=1)
                # print("not exits")
                continue
            start_time = start_time + timedelta(minutes=1)
            temp.append(pd.read_csv(trace_file))         
        span_list = pd.concat(temp, axis=0)
    else:
        
        trace_file = "../data/" + datetime.strftime(detect_time, "%Y-%m-%d/trace/%H_%M") + "_trace.csv"
        if os.path.exists(trace_file):
            span_list = pd.read_csv(trace_file)
        else:
            span_list = pd.DataFrame()
    return span_list



def get_service_operation_list(span_list):
    service_operation_list = []
    for index, row in span_list.iterrows():
        service_operation = get_service_operation_name(row)
        if service_operation not in service_operation_list:
            service_operation_list.append(service_operation)

    return service_operation_list


def get_operation_slo(service_operation_list, span_list):
    traces = {}
    duration_dict = {}
    for operation in service_operation_list:
        duration_dict[operation] = []

    for trace_id, trace in span_list.groupby("TraceID", sort=False):
        if trace.iloc[0]["Duration"] > 100000000:
            continue
        traces[trace_id] = trace
        for index, span in trace.iterrows():
            service_operation = get_service_operation_name(span)
            duration_dict[service_operation].append(span["Duration"])

    operation_slo = {}
    for operation in service_operation_list:
        operation_slo[operation] = []

    for operation in service_operation_list:
        # 均值与方差
        operation_slo[operation].append(
            round(np.mean(duration_dict[operation]) / 1000.0, 4)
        )
        operation_slo[operation].append(
            round(np.std(duration_dict[operation]) / 1000.0, 4)
        )

    return operation_slo


def get_operation_duration_data(service_operation_list, span_list):
    operation_dict = {}
    for trace_id, trace in span_list.groupby("TraceID", sort=False):
        init_operation_dict(service_operation_list, operation_dict, trace_id)
        for index, span in trace.iterrows():
            operation_name = get_service_operation_name(span)
            operation_dict[trace_id][operation_name] += 1
            operation_dict[trace_id]["duration"] += span["Duration"]

    return operation_dict


def get_pagerank_graph(trace_list, span_list):
    operation_operation = {}
    operation_trace = {}
    trace_operation = {}
    pr_trace = {}

    for index, span in span_list.iterrows():
        operation_name = get_service_operation_name2(span)
        if span["TraceID"] in trace_list:
            if operation_name not in operation_operation:
                operation_operation[operation_name] = []
                trace_operation[operation_name] = []
            if span["TraceID"] not in operation_trace:
                operation_trace[span["TraceID"]] = []
                pr_trace[span["TraceID"]] = []

            pr_trace[span["TraceID"]].append(operation_name)

            if operation_name not in operation_trace[span["TraceID"]]:
                operation_trace[span["TraceID"]].append(operation_name)
            if span["TraceID"] not in trace_operation[operation_name]:
                trace_operation[operation_name].append(span["TraceID"])

    for trace_id, trace in span_list.groupby("TraceID", sort=False):
        if trace_id in trace_list:
            span_dict = {}
            for index, span in trace.iterrows():
                span_dict[str(span["SpanID"])] = span
            for span_id, span in span_dict.items():
                parent_id = span["ParentID"]
                if parent_id == "" or parent_id not in span_dict:
                    continue
                operation_name = get_service_operation_name2(span)
                parent_name = get_service_operation_name2(span_dict[parent_id])
                if operation_name not in operation_operation[parent_name]:
                    operation_operation[parent_name].append(operation_name)
    return operation_operation, operation_trace, trace_operation, pr_trace


if __name__ == "__main__":
    span_list = pd.concat(
        [
            get_span_list(start_time=datetime(2024,5,25,12,32,0), end_time=datetime(2024,5,25,12, 46,0)),
        ],
        axis=0,
    )
    print(span_list.shape)
