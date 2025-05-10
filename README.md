# CloudHeal: A Lightweight Online Learning Based Self-Healing Framework for Cloud-Native Systems

With the increasing  scale and complexity of cloud-native systems, faults have become common and impact the end-user experience. Therefore,  it is necessary to propose  efficient self-healing mechanisms to ensure reliability and reduce service disruptions. However, traditional self-healing approaches, including rule-based and offline machine learning methods, suffer from inefficiency and limited adaptability. In this paper, we propose **CloudHeal**, a lightweight online learning-based self-healing framework that dynamically optimizes fault mitigation strategies for cloud-native environments. CloudHeal leverages Spectrum-Based Fault Localization (SBFL) and feedback-enhanced PageRank for root cause identification, significantly reducing unnecessary self-healing actions. To support adaptive decision-making, CloudHeal employs a context-aware online learning algorithm that continuously refines fault recovery strategies based on real-time system feedback. Experimental evaluations on microservice benchmarks demonstrate that CloudHeal achieves a 94.8% fault recovery rate, outperforming existing fault self-healing methods. Additionally, the Root Cause Analyzer in CloudHeal improves fault localization accuracy by 16.9% compared to state-of-the-art approaches, further enhancing self-healing effectiveness. These results highlight CloudHeal’s potential in advancing self-healing capabilities for large-scale cloud-native systems.

<img src="https://note-image-1307786938.cos.ap-beijing.myqcloud.com/img/cloudsh.jpg" alt="cloudsh" style="zoom: 15%;" />

<center>Figure 1.  Overview of CloudHeal.</center>

## Quickly Start

:one: Deployment of [Online Boutique](https://github.com/GoogleCloudPlatform/microservices-demo).

:two: Replace the configurations in `sh/action.py`.

```
deploy_nodes = [
    "x.x.x.x",
]
```

:three: Deployment of tempo, Prometheus and Loki.

:four: Replace the configurations in `utils.py`.

```python
METRIC_ENDPOINT = "http://x.x.x.x:xxxx/"
TRACE_ENDPOINT = "http://x.x.x.x:xxxx/"
LOG_ENDPOINT = "http://x.x.x.x:xxxx/"
```

:five: Run the code

```shell
python sh_linucb.py
```



## File Content

```shell
.
├── data # Some experimental data
├── log
├── query # Get traces and metrics of Online Boutique
│   ├── log
│   ├── log_query.py
│   ├── metric_query.py
│   └── trace_query.py
├── rca  # Root Cause Analyzer
│   ├── detector.py # Anomaly Detector
│   ├── pagerank.py	# Feedback-driven PageRank
│   ├── preprocess.py
│   └── sbfl.py			# Spectrum-Based Fault Localization
├── sh	# Self-Healing Engine
│   ├── action.py		
│   ├── mab.py
│   ├── model
│   └── yaml
├── sh_linucb.py # Main code
└── utils.py    
```

