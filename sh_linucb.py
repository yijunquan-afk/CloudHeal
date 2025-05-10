# -*- coding: utf-8 -*-
#!/usr/bin/env python

from sqlite3 import Timestamp
from injector.inject_fault import *
from injector.log import Logger
from utils import *
import json
import yaml
import random
import time

warnings.filterwarnings('ignore')
log_path = './log/' + str(datetime.now().strftime(
    '%Y-%m-%d')) + '-online-linucb.log'
logger = Logger(log_path, logging.DEBUG, __name__).getlog()

pods = get_total_pod_name()
service_list = [
            "adservice", "cartservice", "checkoutservice", "currencyservice",
            "emailservice", "paymentservice", "productcatalogservice", 
            "recommendationservice",  "frontend", "shippingservice"
]


def get_fault_degree(fault_config, inject_service, inject_fault):
    if inject_service in fault_config:
        if inject_fault in fault_config[inject_service]:
            fault_degree = str(random.randint(
                fault_config[inject_service][inject_fault]["min"], fault_config[inject_service][inject_fault]["max"]))
            return fault_degree
        else:
            return 0
    else:
        return 0


if __name__ == '__main__':
    # 60 fault in total
    fault_list = {
                "adservice": ["deploy","network_delay", "cpu_contention", "io_contention", "network_delay", "load"], 
                "currencyservice": ["deploy", "network_delay", "cpu_contention", "io_contention", "load"] ,
                "checkoutservice": ["deploy", "load", "network_delay", "cpu_contention", "io_contention"],
                "recommendationservice": ["deploy","network_delay", "cpu_contention",  "network_delay",  "network_delay","deploy", "load"] ,
                "productcatalogservice": ["deploy", "network_delay", "cpu_contention", "load", "io_contention", "network_delay",  "cpu_contention",
                                            "io_contention", "network_delay", "deploy"] ,
                "frontend": ["deploy","network_delay", "cpu_contention", "io_contention", "network_delay"] ,
                "cartservice": ["deploy", "network_delay", "cpu_contention", "io_contention", "load"] ,
                "emailservice": ["deploy", "network_delay", "network_delay", "io_contention", "cpu_contention", "load"], 
                "paymentservice": ["deploy", "network_delay",  "io_contention", "network_delay", "load", "network_delay"] ,
                "shippingservice": ["deploy","network_delay",  "io_contention", "network_delay", "load"] ,
                }
    costs = [0, 0.1, 0.15, 0.2, 0.05]

    inject_dic = {}  # recode inject history
    fault_number = 0
    duration = 420 
    alpha = 24
    with(open('injector/fault_config.yaml')) as config_file:
        fault_config = yaml.load(config_file.read(), Loader=yaml.FullLoader)

    logger.info("Starting injection on online learning experiment......")
    with open("slo.pkl", "rb") as f:
        slo, operation_list = pickle.load(f)
    
    init_time = datetime.now()
    if os.path.exists("rca.pkl"):
        logger.info("load model")
        with open("rca.pkl", "rb") as f:
            operation_feedback = pickle.load(f)
    else:
        operation_feedback = {}
        for service in service_list:
            operation_feedback[service] = [1, 1, init_time]

    create_file()
    new_day = False
    action = 0
    for i in range(1):
        logger.info(f"===================================Stage: {i+1}==================================")
        for inject_service in fault_list:
            for inject_fault in fault_list[inject_service]:
                logger.info("=======================================================================")
                if not new_day and str(datetime.now().strftime('%H')) == "00":
                    create_file()
                    new_day == True
                date = str(datetime.now().strftime('%Y-%m-%d'))
                hour = str(datetime.now().strftime('%H'))
                inject_timestamp = str(int(time.time()))
                inject_time = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

                if date not in inject_dic:
                    inject_dic[date] = {}

                if hour not in inject_dic[date]:
                    inject_dic[date][hour] = []

                fault_degree = get_fault_degree(
                    fault_config, inject_service, inject_fault)

                if inject_fault == "load" and inject_service == "adservice":
                    command = f"kubectl rollout restart deployment {inject_service} -n hipster"
                    logger.info(command)
                    os.popen(command)
                    time.sleep(180)
                if inject_service == "adservice":
                    pod_name, fault, inject_result = inject_adservice_fault(
                        fault_degree=fault_degree, fault=inject_fault, duration=duration)
                elif inject_service == "cartservice":
                    pod_name, fault, inject_result = inject_cartservice_fault(
                        fault_degree=fault_degree,  fault=inject_fault, duration=duration)
                elif inject_service == "checkoutservice":
                    pod_name, fault, inject_result = inject_checkoutservice_fault(
                        fault_degree=fault_degree,  fault=inject_fault, duration=duration)
                elif inject_service == "currencyservice":
                    pod_name, fault, inject_result = inject_currencyservice_fault(
                        fault_degree=fault_degree,  fault=inject_fault, duration=duration)
                elif inject_service == "emailservice":
                    pod_name, fault, inject_result = inject_emailservice_fault(
                        fault_degree=fault_degree,  fault=inject_fault, duration=duration)
                elif inject_service == "frontend":
                    pod_name, fault, inject_result = inject_frontend_fault(
                        fault_degree=fault_degree,  fault=inject_fault, duration=duration)
                elif inject_service == "paymentservice":
                    pod_name, fault, inject_result = inject_paymentservice_fault(
                        fault_degree=fault_degree,  fault=inject_fault, duration=duration)
                elif inject_service == "productcatalogservice":
                    pod_name, fault, inject_result = inject_productcatalogservice_fault(
                        fault_degree=fault_degree,  fault=inject_fault, duration=duration)
                elif inject_service == "recommendationservice":
                    pod_name, fault, inject_result = inject_recommendationservice_fault(
                        fault_degree=fault_degree,  fault=inject_fault, duration=duration)
                elif inject_service == "shippingservice":
                    pod_name, fault, inject_result = inject_shippingservice_fault(
                        fault_degree=fault_degree,  fault=inject_fault, duration=duration)
                else:
                    inject_result = False
                    logger.fatal("Unknown service %s" % (inject_service))

                if inject_result:
                    inject_info = {
                        "inject_time": inject_time,
                        "inject_timestamp": inject_timestamp,
                        "inject_pod": pod_name,
                        "inject_type": fault
                    }
                    fault_number += 1
                    inject_dic[date][hour].append(inject_info)
                    pathname = str(datetime.now().strftime(
                        '%Y-%m-%d')) + '-fault_list.json'
                    js = open('./log/' + pathname, 'w+', encoding='utf-8')
                    json.dump(inject_dic[date], js, ensure_ascii=False, indent=4)

                    logger.info(f"Fault injection for {pod_name} is successful.")

                    time.sleep(60)

                    current_time = datetime.now()
                    start = current_time - timedelta(minutes=1)
                    end = current_time

                    s_time = time.time()
                    query_trace(start, end)
                    sleep_time = 60-int(time.time()-s_time)
                    time.sleep(sleep_time)

                    if not new_day and str(datetime.now().strftime('%H')) == "00":
                        create_file()
                        new_day == True

                    s_time = time.time()    
                    query_trace(end, end + timedelta(minutes=1))
                    sleep_time = 60-int(time.time()-s_time)
                    time.sleep(sleep_time)

                    current_time = end + timedelta(minutes=1)

                    span_list_current = get_span_list(detect_time=current_time)
                    detect_result = system_anomaly_detect(span_list=span_list_current, slo=slo)

                    query_metric(current_time)
                    sh_history = []
                    sh_history.append(datetime.strftime(current_time, "%Y-%m-%d %H:%M:%S"))
                    if inject_fault == "deploy":
                        d_time = current_time + timedelta(minutes=1)
                        new_name = get_pod_name_v2(inject_service)
                        try:
                            state_vector = get_pod_state_vector(new_name, d_time)
                        except:
                            state_vector = []
                    else:
                        try:
                            state_vector = get_pod_state_vector(pod_name, current_time)
                            state_vector[-1] = state_vector[-1] + random.random() + 0.1
                        except:
                            state_vector = []
                    
                    sh_history = sh_history + state_vector
                    service = pod_name.split("-")[0]
                    history_file = f'./data/recovery-history/{service}.csv'
                    linucb_file = f'./data/linucb.csv'
                    if  detect_result:
                        logger.error("System occurs errors!")
                        logger.info(f"The true fault is {pod_name}")
                        top_list, score_list = rca(
                            slo=slo,
                            rca_time=current_time,
                            operation_feedback=operation_feedback,
                            pagerank_flag=True,
                            spectrum_method="dstar2",
                        )
                        for service in service_list:
                            if inject_service == service:
                                operation_feedback[service][0] += 1
                                operation_feedback[service][1] = 1
                                operation_feedback[service][2] = current_time
                            else:
                                time_delta = (current_time - operation_feedback[service][2]).total_seconds()/3600
                                if time_delta < 1:
                                    operation_feedback[service][1] = 1
                                else:
                                    operation_feedback[service][1] = 1 + time_delta/alpha
                        rca_result = top_list[0].split("_")[0]
                        logger.info(f"The root cause is {rca_result}")

                        model_service = rca_result.split("-")[0]
                        with open(f"recovery/model/{model_service}_LinUCB_model.pkl", "rb") as f:
                            model = pickle.load(f)
                        context = np.array(state_vector[0:1]+state_vector[2:]).reshape(-1,1)
                        logger.info(state_vector[0:1]+state_vector[2:])
                        action = model.select_arm(context)
                        if action == 0:
                            sh_history.append("NoOps")
                        elif action == 1:
                            sh_history.append("Restart")  
                            new_pod = restart(rca_result)
                            logger.info("Restart to mitigate the failure.")      
                        elif action == 2:
                            sh_history.append("Migrate")  
                            new_pod = migrate(rca_result)
                            logger.info("Migrate to mitigate the failure.")                                        
                        elif action == 3:
                            sh_history.append("Rollback")  
                            rollback(rca_result)  
                            logger.info("Rollback to mitigate the failure.")  
                        elif action == 4:
                            sh_history.append("Flow-Control")  
                            flow_control(rca_result)  
                            logger.info("Flow Control to mitigate the failure.") 
                        elif action == 0:
                            sh_history.append("NoOps")  
                            logger.info("NoOps to mitigate the failure.") 

                        if (inject_fault== "deploy") or (inject_fault== "load") :
                            time.sleep(180)
                        elif "adservice" in inject_service:
                            time.sleep(280)
                        else:
                            time.sleep(120)

                        # detect again
                        start = datetime.now() - timedelta(minutes=1)
                        end = datetime.now()
                        if not new_day and str(datetime.now().strftime('%H')) == "00":
                            create_file()
                            new_day == True
                        query_trace(start, end)
                        cur = datetime.strftime(end, "%Y-%m-%d:%H_%M")
                        span_list_current = get_span_list(detect_time=end)
                        detect_result_again = system_anomaly_detect(span_list=span_list_current, slo=slo)
                        
                        if not detect_result_again:
                            sh_history.append(1)
                            reward = 1 - costs[action]
                            model.update(action, reward, context)
                            with open(f"recovery/model/{model_service}_LinUCB_model.pkl", "wb") as f:
                                pickle.dump(model, f)
                            logger.info("Self-healing has succeeded!")
                        else:
                            sh_history.append(0)
                            reward = 0 - costs[action]
                            model.update(action, reward, context)
                            with open(f"recovery/model/{model_service}_LinUCB_model.pkl", "wb") as f:
                                pickle.dump(model, f)                            
                            logger.error("Self-healing has failed!")
                    else:
                        logger.info("System is healthy.")
                        sh_history.append("NoOps")
                        sh_history.append(1)      
                    with open(history_file, 'a', newline='') as file:
                        writer = csv.writer(file)
                        writer.writerow(sh_history)
                    with open(linucb_file, 'a', newline='') as file:
                        writer = csv.writer(file)
                        linucb_result = sh_history
                        linucb_result.append(inject_service)
                        writer.writerow(linucb_result)
                # time.sleep(duration)
                with open("rca.pkl", "wb") as f:
                    pickle.dump(operation_feedback, f) 
                if  action == 4: 
                    try:
                        cancel_flow_control(pod_name)
                    except:
                        logger.info("ignore")
                if inject_fault == "deploy":
                    temp = inject_service+"-v2"
                    rollback(temp)
                restart_loadgenerator()
                time.sleep(random.randint(180, 200))

    
    logger.info("injection end......")
