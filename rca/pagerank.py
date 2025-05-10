from rca.preprocess import *
from rca.detector import *


def get_call_graph(operation_operation):
    num = len(operation_operation)
    call_graph = np.zeros([num, num], dtype=int)
    operation_index = {}
    i = 0
    for operation in operation_operation.keys():
        operation_index[operation] = i
        i += 1
    for operation, ops in operation_operation.items():
        for temp in ops:
            call_graph[operation_index[operation]][operation_index[temp]] = 1
    return list(operation_index.keys()), call_graph

def get_trace_num_list(trace_operation):
    trace_num_list = {}
    for operation in trace_operation:
        trace_num_list[operation] = len(trace_operation[operation])
    return trace_num_list

def pagerank(operation_name, G, R, T, d=0.85, epsilon=1.0e-8, w = 0.3):
    n = len(G)
    P = np.zeros((n, n))
    for i in range(n):
        
        if np.sum(G[i]) == 0:
            P[i] = np.ones(n) / n
        else:
            P[i] = G[i] / np.sum(G[i])
    P = np.nan_to_num(P) 
    v = np.ones(n) / n
    last_v = np.ones(n)

    i = 0
    while (np.linalg.norm(v - last_v, 2) > epsilon) and (i < 1000):
        last_v = v
        v = (d * np.matmul(P.T, v) + (1 - d) / n) * ((w * (np.log10(R + 1)) + 1) / T)
        i += 1
        # print(i)
    v = v / float(sum(v))
    pagerank_score = {}
    for i in range(len(v)):
        pagerank_score[operation_name[i]] = v[i]
    
    # for score in sorted(pagerank_score.items(), key=lambda x: x[1], reverse=True):
    #     print('%-50s: %.5f' % (score[0], score[1]))
    return pagerank_score

if __name__ == "__main__":
    operation_slo = get_slo(test_time="2024-04-25:03_03")

    # for operation,slo in operation_slo.items():
    #     if 'adservice' in operation:
    #         print(operation, slo)
    # print(operation_slo)
    span_list_suffering = get_span_list(test_time="2024-04-24:17_57")
    service_operation_list = get_service_operation_list(span_list_suffering)
    operation_dict = get_operation_duration_data(
        service_operation_list, span_list_suffering
    )
    system_anomaly_detect(span_list=span_list_suffering, slo=operation_slo)
    abnormal_trace_list, normal_trace_list = trace_list_partition(
        operation_dict, operation_slo
    )
    print(f"abnormal trace number: {len(abnormal_trace_list)}")
    print(f"normal trace number: {len(normal_trace_list)}")

    operation_operation, operation_trace, trace_operation, pr_trace = (
        get_pagerank_graph(abnormal_trace_list, span_list_suffering)
    )
    operation_index, call_graph = get_call_graph(operation_operation)
    num = len(operation_index)
    R = np.array([1 for i in range(num)])
    T = np.array([1 for i in range(num)])

    result = pagerank(operation_index, call_graph, R, T)
    for score in sorted(result.items(), key=lambda x: x[1], reverse=True):
        print('%-50s: %.5f' % (score[0], score[1]))
