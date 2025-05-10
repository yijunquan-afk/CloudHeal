import requests

ns = "hipster"

class MonitorPod:

    def __init__(self, endpoint):
        self.usr = endpoint

    def timeQuery(self, start_time, end_time):
        step = 30
        return (
            "&start=" + str(start_time) + "&end=" + str(end_time) + "&step=" + str(step)
        )

    def getQueryRange(self, query, time_range):
        base_url = self.usr + "api/v1/query_range?query="
        inquire = base_url + query + time_range
        response = requests.request("GET", inquire)
        if response.status_code == 200:
            result = response.json()["data"]["result"]
            return result
        else:
            return None

    def get_cpu_use_rate(self, start_time, end_time, pod_name, container="server"):
        query = (
            '(sum(rate(container_cpu_usage_seconds_total{container="%s",pod="%s"}[60s])) by(container,pod))/ \
        (sum(container_spec_cpu_quota{container="%s",pod="%s"})by(container,pod) /100000)*100'
            % (container, pod_name, container, pod_name)
        )
        time_range = self.timeQuery(start_time, end_time)
        result = self.getQueryRange(query, time_range)
        return result

    def get_memory_usage(self, start_time, end_time, pod_name, container="server"):
        query = (
            '(sum(container_memory_rss{container="%s",pod="%s"}) by(container,pod)) / \
            (sum(container_spec_memory_limit_bytes{container="%s",pod="%s"}) by(container,pod)) * 100'
            % (container, pod_name, container, pod_name)
        )
        time_range = self.timeQuery(start_time, end_time)
        result = self.getQueryRange(query, time_range)
        return result

    def get_IO_read(self, start_time, end_time, pod_name, container_name="server"):
        query = (
            'ceil(sum by(pod) (rate(container_fs_reads_total{cluster="",namespace= "hipster", pod = "%s", container="%s"\
                }[5m])))'
            % (pod_name, container_name)
        )
        time_range = self.timeQuery(start_time, end_time)
        result = self.getQueryRange(query, time_range)
        return result

    def get_IO_written(self, start_time, end_time, pod_name, container_name="server"):
        query = (
            'ceil(sum by(pod) (rate(container_fs_writes_total{cluster="",namespace= "hipster", pod = "%s", container="%s"\
                }[5m])))'
            % (pod_name, container_name)
        )
        time_range = self.timeQuery(start_time, end_time)
        result = self.getQueryRange(query, time_range)
        return result

    def get_IO_throughput(self, start_time, end_time, pod_name):
        query = (
            'sum by(pod) (rate(container_fs_reads_bytes_total{container!="", cluster="",namespace="hipster", pod="%s"}[5m]) %%2B \
             rate(container_fs_writes_bytes_total{container!="", cluster="",namespace="hipster", pod="%s"}[5m]))/1024/1024'
            % (pod_name, pod_name)
        )
        time_range = self.timeQuery(start_time, end_time)
        result = self.getQueryRange(query, time_range)
        return result

    def get_network_received_packets(self, start_time, end_time, pod_name):
        query = (
            'sum(irate(container_network_receive_packets_total{cluster="",pod="%s",\
                 namespace="hipster"}[4h:30s])) by (pod)'
            % (pod_name)
        )
        time_range = self.timeQuery(start_time, end_time)
        result = self.getQueryRange(query, time_range)
        return result

    def get_network_transmitted_packets(self, start_time, end_time, pod_name):
        query = (
            'sum(irate(container_network_transmit_packets_total{cluster="",pod="%s",\
                  namespace=~"hipster"}[4h:30s])) by (pod)'
            % (pod_name)
        )
        time_range = self.timeQuery(start_time, end_time)
        result = self.getQueryRange(query, time_range)
        return result

    def get_network_packets_dropped_rate(self, start_time, end_time, pod_name):
        query = (
            'sum(irate(container_network_receive_packets_dropped_total{cluster="",pod="%s", namespace="hipster"}[4h:30s]))\
                by (pod) %%2B sum(irate(container_network_transmit_packets_dropped_total{cluster="",pod="%s", namespace="hipster"}\
                [4h:30s])) by (pod)'
            % (pod_name, pod_name)
        )
        time_range = self.timeQuery(start_time, end_time)
        result = self.getQueryRange(query, time_range)
        return result


    def get_update_time(self, start_time, end_time, pod_name, container="server"):
        query = (
            '(time() - container_start_time_seconds{namespace="hipster", pod = "%s", container="%s"})/86400'
            % (pod_name, container)
        )
        time_range = self.timeQuery(start_time, end_time)
        result = self.getQueryRange(query, time_range)
        return result

    def get_latency(self, start_time, end_time, pod_name):
        # service = pod_name.split("-")[0]
        # if service == "frontend":
        #     service = "frontend-external"
        query = (
             '(histogram_quantile(0.90, sum(irate(istio_request_duration_milliseconds_bucket{reporter=~"(destination|source)",kubernetes_pod_name=~"%s"}[1m])) by (le)) / 1000)\
            or histogram_quantile(0.90, sum(irate(istio_request_duration_seconds_bucket{reporter=~"(destination|source)",kubernetes_pod_name=~"%s"}[1m])) by (le))'
            %(pod_name, pod_name)
        )
        time_range = self.timeQuery(start_time, end_time)
        result = self.getQueryRange(query, time_range)
        return result

    def get_syscall_read(self, start_time, end_time, pod_name):
        service = pod_name.split("-")[0]
        query = (
            'increase(monitor_agent_io_read_syscall_total{pod="%s"}[2m])' %(pod_name)
        )
        time_range = self.timeQuery(start_time, end_time)
        result = self.getQueryRange(query, time_range)
        return result

    def get_syscall_write(self, start_time, end_time, pod_name):
        service = pod_name.split("-")[0]
        query = (
            'increase(monitor_agent_io_write_syscall_total{pod="%s"}[2m])' %(pod_name)
        )
        time_range = self.timeQuery(start_time, end_time)
        result = self.getQueryRange(query, time_range)
        return result
