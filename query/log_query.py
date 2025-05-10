import csv
import json
import math
import os
import re
import sys
import threading
import time
import traceback
from datetime import datetime, timedelta
from typing import List

import requests
import logging

logging.basicConfig(filename='log/log.log', level=logging.DEBUG)
logger = logging.getLogger(__name__)

endpoint = "http://10.10.2.217:30001"
namespace = "hipster"

class LogStruct:
    def __init__(self):
        self.Status = ""
        self.Data = {"Result": []}

def query_logs(endpoint: str, query: str, start: datetime, end: datetime, limit: int) -> LogStruct:
    client = requests.Session()
    params = {
        "query": query,
        "limit": limit,
        "start": format(start.timestamp() * 1e9, ".0f"),
        "end": format(end.timestamp() * 1e9, ".0f"),
    }
    response = client.get(f"{endpoint}/loki/api/v1/query_range", params=params)
    jsondata = response.json()
    logs = LogStruct()
    logs.Status = jsondata.get("status", "")
    logs.Data["Result"] = jsondata.get("data", {}).get("result", [])
    return logs


def write_logs(logs: LogStruct, log_file: str):
    with open(log_file, "a") as log_file:
        log_writer = csv.writer(log_file)

        for result in logs.Data["Result"]:
            for values in result["values"]:
                timestamp = values[0]
                trace_id_match = re.search(r"TraceID: (\w+)", values[1])
                span_id_match = re.search(r"SpanID: (\w+)", values[1])

                if trace_id_match and span_id_match:
                    trace_id = trace_id_match.group(1)
                    span_id = span_id_match.group(1)
                    log_info = [
                        timestamp,
                        result["stream"]["node_name"],
                        result["stream"]["pod"],
                        result["stream"]["container"],
                        trace_id,
                        span_id,
                        values[1],
                    ]
                    log_writer.writerow(log_info)

def query_trace_id_by_log(
    endpoint: str, namespace: str,  start: datetime, end: datetime, limit: int
):
    query = f'{{namespace="{namespace}"}}'
    interval = math.ceil((end - start).total_seconds() / 5)
    trace_regexp = re.compile(r"TraceID: (\w+)")
    complete_trace_id_list = []

    for i in range(interval):
        begin = start + timedelta(seconds=i * 5)
        stop = start + timedelta(seconds=(i + 1) * 5)
        logs = query_logs(endpoint, query, begin, stop, limit)

        for result in logs.Data["Result"]:
            for log in result["values"]:
                match = trace_regexp.search(log[1])
                if match:
                    complete_trace_id_list.append(match.group(1))

    trace_id_list = list(set(complete_trace_id_list))
    # with open("traceid.csv", "a") as trace_file:
    #     trace_writer = csv.writer(trace_file)
    #     trace_writer.writerow(["TraceID"])
    #     for trace_id in trace_id_list:
    #         trace_writer.writerow([trace_id])

    return trace_id_list

def query_trace_id_by_log_small_first(
    endpoint: str, namespace: str,  start: datetime, end: datetime, original_trace_list
):
    query = f'{{namespace="{namespace}"}}'
    interval = math.ceil((end - start).total_seconds() / 5)
    trace_regexp = re.compile(r'ayment|email')
    trace_regexp2 = re.compile(r"TraceID: (\w+)")
    complete_trace_id_list = []

    for i in range(interval):
        begin = start + timedelta(seconds=i * 5)
        stop = start + timedelta(seconds=(i + 1) * 5)
        logs = query_logs(endpoint, query, begin, stop, 5000)

        for result in logs.Data["Result"]:
            for log in result["values"]:
                match = trace_regexp.search(log[1])
                match2 = trace_regexp2.search(log[1])
                if match and match2:
                    complete_trace_id_list.append(match2.group(1))

    # with open("traceid.csv", "r") as trace_file:
    #     trace_reader = csv.reader(trace_file)
    #     original_trace_list = list(trace_reader)[1:]

    trace_id_list = list(set(set(original_trace_list)|set(complete_trace_id_list)))
    # with open("traceid.csv", "a") as trace_file:
    #     trace_writer = csv.writer(trace_file)
    #     for trace_id in trace_id_list:
    #         if [trace_id] not in original_trace_list:
    #             trace_writer.writerow([trace_id])

    return trace_id_list

def get_trace_ids(
    endpoint: str, namespace: str,  start: datetime, end: datetime, limit = 1600
):
    original_trace_list = query_trace_id_by_log(endpoint, namespace, start, end, limit)
    trace_id_list = query_trace_id_by_log_small_first(endpoint, namespace, start, end, original_trace_list)
    return trace_id_list


if __name__ == "__main__":
    start = datetime.now() - timedelta(minutes = 1)
    end = datetime.now()
    get_trace_ids(
        endpoint = endpoint,
        namespace = namespace,
        start = start,
        end = end
    )
    
    print(datetime.now()-end)

