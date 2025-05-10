# CloudSH: Online Learning Based Self-Healing for Cloud-Native Systems

We propose **CloudSH**, a lightweight online learning-based self-healing framework that dynamically optimizes fault mitigation strategies for cloud-native environments. CloudSH leverages Spectrum-Based Fault Localization (SBFL) and feedback-enhanced PageRank for root cause identification, significantly reducing unnecessary self-healing actions. Furthermore, a Contextual Multi-Armed Bandit (CMAB) algorithm, LinUCB, is employed to continuously learn from real-time system feedback, improving decision-making efficiency. 

<img src="https://note-image-1307786938.cos.ap-beijing.myqcloud.com/img/cloudsh.jpg" alt="cloudsh" style="zoom: 15%;" />

<center>Figure 1.  Overview of CloudSH.</center>

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

