import base64
import csv
import json
import requests
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import logging


logger = logging.getLogger(__name__)
log_path = 'log/trace.log'
file_handler = logging.FileHandler(log_path)
formatter = logging.Formatter("%(asctime)s\t%(levelname)s\t%(message)s",
                              datefmt="%Y-%m-%d %H:%M:%S")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)


class SpanStruct:
    def __init__(self):
        self.PodName = ""
        self.OperationName = ""
        self.TraceID = ""
        self.SpanID = ""
        self.ParentID = ""
        self.Start = ""
        self.End = ""
        self.Duration = ""


class Jsondata:
    def __init__(self):
        self.Batches = []


def query_trace_total(endpoint, traceids, file_name):
    headers = [
        "TraceID",
        "SpanID",
        "ParentID",
        "PodName",
        "OperationName",
        "StartTimeUnixNano",
        "EndTimeUnixNano",
        "Duration",
    ]

    with open(file_name, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(headers)

    parallel = 20
    step = len(traceids) // parallel

    with ThreadPoolExecutor(max_workers=parallel) as executor:
        for i in range(step):
            for j in range(parallel):
                index = i * parallel + j
                executor.submit(query_trace, endpoint, traceids[index], file_name)



def query_trace(endpoint, traceid, file_name):
    span_list, err = query_by_trace_id(endpoint, traceid)
    if err:
        logger.error("Query trace failed: {}".format(err))
        raise Exception("Query trace failed: {}".format(err))

    with open(file_name, "a") as trace_file:
        trace_writer = csv.writer(trace_file)
        for span_info in span_list:
            span = [
                span_info.TraceID,
                span_info.SpanID,
                span_info.ParentID,
                span_info.PodName,
                span_info.OperationName,
                span_info.Start,
                span_info.End,
                span_info.Duration,
            ]
            trace_writer.writerow(span)


def query_action(req):
    try:
        resp = requests.get(req)
        # resp.raise_for_status()
        jsondata = json.loads(resp.text)
        return jsondata
    except Exception as e:
        logger.error("Error querying action: {}".format(e))
        return None


def query_by_trace_id(endpoint, traceid):
    history_span = []
    span_list = []
    url = endpoint + "/api/traces/" + traceid

    for _ in range(10):
        jsondata = query_action(url)
        # print(f"query result: {jsondata}")
        if not jsondata or len(jsondata["batches"]) == 0:
            logger.error("Query trace failed: {}".format(url))
            time.sleep(0.01)
        else:
            # logger.info(f"Query: {url}")
            break
    else:
        logger.error("Query trace failed ten times.")
        return span_list, Exception("Query trace failed ten times.")

    for batch in jsondata["batches"]:
        for instrumentation_library_span in batch["instrumentationLibrarySpans"]:
            for span in instrumentation_library_span["spans"]:
                span_id_bytes = base64.b64decode(span["spanId"])
                span_id = span_id_bytes.hex()

                if span_id not in history_span:
                    history_span.append(span_id)
                    trace_span = SpanStruct()
                    for attribute in batch["resource"]["attributes"]:
                        if (
                            attribute["key"] == "PodName"
                            or attribute["key"] == "host.name"
                        ):
                            trace_span.PodName = attribute["value"]["stringValue"]
                    if "attributes" in span.keys():
                        for attributes in span["attributes"]:
                            if attributes["key"] == "PodName":
                                trace_span.PodName = attributes["value"]["stringValue"]
                    trace_span.OperationName = span["name"]
                    trace_span.TraceID = base64.b64decode(span["traceId"]).hex()
                    trace_span.SpanID = span_id
                    if "parentSpanId" not in span.keys():
                        parent_span_id_bytes = None
                    else:
                        parent_span_id_bytes = base64.b64decode(span["parentSpanId"])
                    trace_span.ParentID = (
                        parent_span_id_bytes.hex() if parent_span_id_bytes else "root"
                    )
                    trace_span.Start = span["startTimeUnixNano"]
                    trace_span.End = span["endTimeUnixNano"]
                    end = int(span["endTimeUnixNano"])
                    start = int(span["startTimeUnixNano"])
                    trace_span.Duration = str((end - start) / 1000)
                    span_list.append(trace_span)

    return span_list, None



