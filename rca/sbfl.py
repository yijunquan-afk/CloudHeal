import math 
import numpy as np

def calculate_spectrum(anomaly_result, normal_result, anomaly_list_len, normal_list_len,
                       top_max, normal_num_list, anomaly_num_list, spectrum_method, pagerank = True):
    spectrum = {}
    if pagerank:
        for operation in anomaly_result:
            spectrum[operation] = {}
            spectrum[operation]['CF'] = anomaly_result[operation] * anomaly_num_list[operation]
            spectrum[operation]['UF'] = anomaly_result[operation] * (anomaly_list_len - anomaly_num_list[operation])
            if operation in normal_result: 
                spectrum[operation]['CT'] = normal_result[operation] * normal_num_list[operation]
                spectrum[operation]['UT'] = normal_result[operation] * (normal_list_len - normal_num_list[operation])
            else:
                spectrum[operation]['CT'] = 0.001
                spectrum[operation]['UT'] = 0.001

        for operation in normal_result:
            if operation not in spectrum:
                spectrum[operation] = {}
                spectrum[operation]['CT'] = (1 + normal_result[operation]) * normal_num_list[operation]
                spectrum[operation]['UT'] = normal_list_len - normal_num_list[operation]
                if operation not in anomaly_result:
                    spectrum[operation]['CF'] = 0.001
                    spectrum[operation]['UF'] = 0.001      
    else:
        for node in anomaly_num_list:
            spectrum[node] = {}
            spectrum[node]['CF'] = anomaly_num_list[node]
            spectrum[node]['UF'] = anomaly_list_len - anomaly_num_list[node]
            if node in normal_num_list:
                spectrum[node]['CT'] = normal_num_list[node]
                spectrum[node]['UT'] = normal_list_len - normal_num_list[node]
            else:
                spectrum[node]['CT'] = 0.001
                spectrum[node]['UT'] = 0.001

        for node in normal_num_list:
            if node not in spectrum:
                spectrum[node] = {}
                spectrum[node]['CT'] = normal_num_list[node]
                spectrum[node]['UT'] = normal_list_len - normal_num_list[node]
                if node not in anomaly_num_list:
                    spectrum[node]['CF'] = 0.001
                    spectrum[node]['UF'] = 0.001


    result = {}
    for node in spectrum:
        if spectrum_method == "dstar2":
            result[node] = spectrum[node]['CF'] * spectrum[node]['CF'] / \
                (spectrum[node]['CT'] + spectrum[node]['UF'])
        elif spectrum_method == "ochiai":
            result[node] = spectrum[node]['CF'] / \
                math.sqrt((spectrum[node]['CT'] + spectrum[node]['CF']) * (
                    spectrum[node]['CF'] + spectrum[node]['UF']))

        elif spectrum_method == "jaccard":
            result[node] = spectrum[node]['CF'] / (spectrum[node]['CF'] + spectrum[node]['CT']
                                                   + spectrum[node]['UF'])
        elif spectrum_method == "dice":
            result[node] = 2 * spectrum[node]['CF'] / \
                (spectrum[node]['CF'] + spectrum[node]
                 ['UF'] + spectrum[node]['CT'])



    top_list = []
    score_list = []
    # print("\n %s Spectrum Result:" % spectrum_method)
    # # print(result)
    for index, score in enumerate(sorted(result.items(), key=lambda x: x[1], reverse=True)):
        if index < top_max :
            top_list.append(score[0])
            score_list.append(score[1])
            # print('%-50s: %.8f' % (score[0], score[1]))       

    return top_list, score_list
         