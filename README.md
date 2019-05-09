# DevOps-common-rancher-integration
python code to perform the following actions using the rancher API

  * Create a namespace  (**tenant-name**)
  * Create a persistent volume tied to the project/cluster (**chart**-pv)
  * create multiple Persistent Volume Claim (based on --charts option) and bind them to the previously created PV (**chart**-claim)
  * based on the --charts option, deploy the listed charts if there is a mapping in the catalog
  * based on the --params option, pass any chart parameters to the chart, they **MUST** be prefixed by the chart name so the NGINX parameter ***controller.stats.enabled*** must be prefixed with the NGINX chart name ***nginx.controller.stats.enabled***
  * If an ingress is specified in the chart configuration it will create a ingress for the jenkins, sonarIQ or Nexus subdomains

If any resources with the same name are detected or there is an API connection error the script will exit with a return code of 1, on successful completion the script will exit with a return code of 0

Changes can be made to the **alf_config.json** to change default parameters such as Rancher projectid, cluserid and bearer-token etc.

### basic usage:
```bash
$ cp ./alf-examples/alf_config_example.json ./alf_config.json  (adjust the values in this file accordingly)

$ ./setup-env.py  --platform=alf-on-azure --tenant=test3562 --charts nginx test --params nginx.controller.stats.enabled=false jenkins.test=/devops nginx.controller.readinessProbe.timeoutSeconds=5 --storage local
```

### example output
```bash
2019-05-07 16:39:36 INFO     platform:alf-on-azure charts:['nginx', 'test'] parameters:['nginx.controller.stats.enabled=false']
Running devops-common-env-create
2019-05-07 16:39:41 INFO     successfully created namespace:https://10.179.193.167/v3/cluster/c-qb62x/namespaces/test3562
2019-05-07 16:39:41 INFO     successfully run cmd:['kubectl', 'get', 'pv', '-n', u'test3562']
2019-05-07 16:39:42 INFO     successfully created volume:https://10.179.193.167/v3/cluster/c-qb62x/persistentVolumes/nginx-pv
2019-05-07 16:39:47 INFO     successfully created volume claim:https://10.179.193.167/v3/project/c-qb62x:p-nvlcn/persistentVolumeClaims/test3562:nginx-claim
2019-05-07 16:39:47 INFO     adding parameter:controller.stats.enabled value:false to chart:nginx
2019-05-07 16:40:07 INFO     using deployment url:https://10.179.193.167/v3/project/c-qb62x:p-nvlcn/workloads/deployment:test3562:test3562-test-nginx-test-chart
2019-05-07 16:40:07 INFO     successfully deployed app:https://10.179.193.167/v3/project/c-qb62x:p-nvlcn/apps/p-nvlcn:test3562-test-nginx
2019-05-07 16:40:07 INFO     successfully deployed workload:https://10.179.193.167/v3/project/c-qb62x:p-nvlcn/workloads/deployment:test3562:test3562-test-nginx-test-chart
2019-05-07 16:40:27 INFO     successfully created ingress:https://10.179.193.167/v3/project/c-qb62x:p-nvlcn/ingresses/test3562:test3562nginx
2019-05-07 16:40:28 INFO     successfully run cmd:['kubectl', 'get', 'pv', '-n', u'test3562']
2019-05-07 16:40:28 INFO     successfully created volume:https://10.179.193.167/v3/cluster/c-qb62x/persistentVolumes/test-pv
2019-05-07 16:40:33 INFO     successfully created volume claim:https://10.179.193.167/v3/project/c-qb62x:p-nvlcn/persistentVolumeClaims/test3562:test-claim
2019-05-07 16:40:43 INFO     using deployment url:https://10.179.193.167/v3/project/c-qb62x:p-nvlcn/workloads/deployment:test3562:test3562-test-test-chart
2019-05-07 16:40:43 INFO     successfully deployed app:https://10.179.193.167/v3/project/c-qb62x:p-nvlcn/apps/p-nvlcn:test3562-test
2019-05-07 16:40:43 INFO     successfully deployed workload:https://10.179.193.167/v3/project/c-qb62x:p-nvlcn/workloads/deployment:test3562:test3562-test-test-chart
2019-05-07 16:41:44 INFO     successfully created ingress:https://10.179.193.167/v3/project/c-qb62x:p-nvlcn/ingresses/test3562:test3562test

```


#### Flags
  **--platform** ,sets the configuration file to use for the base platform, ***alf-on-azure*** is the only supported value at present

  **--tenant** ,sets the prefix for all K8 resources for    example ***payroll123*** will create a ***payroll123-namespace*** namespace resource

  **--charts** , sets the helm charts to install, a general name such as ***nginx*** should be used which will translate to a rancher catalog link (specified in the config file), if a package is included that is unknown it will ignored and a WARNING message logged (as seen in the example output)

  **--params** , specifies the parameters that will be used to customise the chart, they *MUST* be prepended with a valid chart id for example the NGINX ***controller.stats.enabled=false*** must be prepended with the nginx. chart name so ***nginx.controller.stats.enabled=false*** otherwise it wont be used with the chart

  **--storage** , This is an **optional** switch which specifies the storage type ***local | glusterfs*** that corresponds to a specific configuration in the JSON configuration file. Only local and gluster based volume are supported today. Excluding this option will simply skip the PV/PVC creation

  ***Note*** HELM charts must be configured to use a PVC in the format **chart-claim** so for the nginx chart the PVC would be **nginx-claim**


#### Configuration file
Base configuration items are set in a configuration file that is selected based on the **--platform** flag. The current ALF on Azure platform configuration file is access [here](./alf-examples/alf_config_example.json)

### Resources created

<img src="assets/resources.png" alt="pipe" width="1500" height="400"/>

The following sections give examples of the Kubernetes resource cerated through Rancher

```json
namespace
{
    "apiVersion": "v1",
    "kind": "Namespace",
    "metadata": {
        "annotations": {
            "cattle.io/appIds": "test3562-test-nginx",
            "cattle.io/status": "{\"Conditions\":[{\"Type\":\"InitialRolesPopulated\",\"Status\":\"True\",\"Message\":\"\",\"LastUpdateTime\":\"2019-04-18T13:46:41Z\"},{\"Type\":\"ResourceQuotaInit\",\"Status\":\"True\",\"Message\":\"\",\"LastUpdateTime\":\"2019-04-18T13:46:40Z\"}]}",
            "field.cattle.io/containerDefaultResourceLimit": "{}",
            "field.cattle.io/creatorId": "user-xs5g5",
            "field.cattle.io/description": "default namespace for tenant",
            "field.cattle.io/projectId": "c-wdzkx:p-z7vs8",
            "lifecycle.cattle.io/create.namespace-auth": "true"
        },
        "creationTimestamp": "2019-04-18T13:46:39Z",
        "finalizers": [
            "controller.cattle.io/namespace-auth"
        ],
        "labels": {
            "cattle.io/creator": "norman",
            "field.cattle.io/projectId": "p-z7vs8"
        },
        "name": "test3562",
        "resourceVersion": "210134",
        "selfLink": "/api/v1/namespaces/test3562",
        "uid": "64961e1a-61e0-11e9-909d-0800276bc6a4"
    },
    "spec": {
        "finalizers": [
            "kubernetes"
        ]
    },
    "status": {
        "phase": "Active"
    }
}
```

```json
Persistent Volume
{
    "apiVersion": "v1",
    "kind": "PersistentVolume",
    "metadata": {
        "annotations": {
            "field.cattle.io/creatorId": "user-xs5g5",
            "field.cattle.io/description": "default volume for tenant"
        },
        "creationTimestamp": "2019-04-18T13:46:45Z",
        "finalizers": [
            "kubernetes.io/pv-protection"
        ],
        "labels": {
            "cattle.io/creator": "norman"
        },
        "name": "test3562-persistant-volume",
        "resourceVersion": "210091",
        "selfLink": "/api/v1/persistentvolumes/test3562-persistant-volume",
        "uid": "679e2e07-61e0-11e9-909d-0800276bc6a4"
    },
    "spec": {
        "accessModes": [
            "ReadWriteOnce"
        ],
        "capacity": {
            "storage": "4Gi"
        },
        "claimRef": {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "name": "test3562-volume-claim",
            "namespace": "test3562",
            "resourceVersion": "210088",
            "uid": "a0727f5e-61e0-11e9-909d-0800276bc6a4"
        },
        "local": {
            "path": "/Users/malorr/Downloads/rancher-vol2"
        },
        "nodeAffinity": {
            "required": {
                "nodeSelectorTerms": [
                    {
                        "matchExpressions": [
                            {
                                "key": "cluster",
                                "operator": "In",
                                "values": [
                                    "local"
                                ]
                            }
                        ]
                    }
                ]
            }
        },
        "persistentVolumeReclaimPolicy": "Retain",
        "volumeMode": "Filesystem"
    },
    "status": {
        "phase": "Bound"
    }
}
```

```json
Persistent Volume Claim
{
    "apiVersion": "v1",
    "kind": "PersistentVolumeClaim",
    "metadata": {
        "annotations": {
            "control-plane.alpha.kubernetes.io/leader": "{\"holderIdentity\":\"285ef4c6-61d8-11e9-a396-0800276bc6a4\",\"leaseDurationSeconds\":15,\"acquireTime\":\"2019-04-18T13:48:20Z\",\"renewTime\":\"2019-04-18T13:48:50Z\",\"leaderTransitions\":0}",
            "field.cattle.io/creatorId": "user-xs5g5",
            "pv.kubernetes.io/bind-completed": "yes",
            "pv.kubernetes.io/bound-by-controller": "yes"
        },
        "creationTimestamp": "2019-04-18T13:48:20Z",
        "finalizers": [
            "kubernetes.io/pvc-protection"
        ],
        "labels": {
            "cattle.io/creator": "norman"
        },
        "name": "test3562-volume-claim",
        "namespace": "test3562",
        "resourceVersion": "210198",
        "selfLink": "/api/v1/namespaces/test3562/persistentvolumeclaims/test3562-volume-claim",
        "uid": "a0727f5e-61e0-11e9-909d-0800276bc6a4"
    },
    "spec": {
        "accessModes": [
            "ReadWriteOnce"
        ],
        "resources": {
            "requests": {
                "storage": "4Gi"
            }
        },
        "storageClassName": "standard",
        "volumeMode": "Filesystem",
        "volumeName": "test3562-persistant-volume"
    },
    "status": {
        "accessModes": [
            "ReadWriteOnce"
        ],
        "capacity": {
            "storage": "4Gi"
        },
        "phase": "Bound"
    }
}
```

```json
nginx prod

{
    "apiVersion": "v1",
    "kind": "Pod",
    "metadata": {
        "creationTimestamp": "2019-04-18T13:48:28Z",
        "generateName": "test3562-test-nginx-test-chart-7c6c57d5b5-",
        "labels": {
            "app.kubernetes.io/instance": "test3562-test-nginx",
            "app.kubernetes.io/name": "test-chart",
            "pod-template-hash": "7c6c57d5b5",
            "workloadID_ingress-d73337797b0dbe4259c955dd6eae86e5": "true"
        },
        "name": "test3562-test-nginx-test-chart-7c6c57d5b5-bdqs8",
        "namespace": "test3562",
        "ownerReferences": [
            {
                "apiVersion": "apps/v1",
                "blockOwnerDeletion": true,
                "controller": true,
                "kind": "ReplicaSet",
                "name": "test3562-test-nginx-test-chart-7c6c57d5b5",
                "uid": "a50c00d3-61e0-11e9-909d-0800276bc6a4"
            }
        ],
        "resourceVersion": "210157",
        "selfLink": "/api/v1/namespaces/test3562/pods/test3562-test-nginx-test-chart-7c6c57d5b5-bdqs8",
        "uid": "a50dc7e4-61e0-11e9-909d-0800276bc6a4"
    },
    "spec": {
        "containers": [
            {
                "image": "nginx:stable",
                "imagePullPolicy": "IfNotPresent",
                "livenessProbe": {
                    "failureThreshold": 3,
                    "httpGet": {
                        "path": "/",
                        "port": "http",
                        "scheme": "HTTP"
                    },
                    "periodSeconds": 10,
                    "successThreshold": 1,
                    "timeoutSeconds": 1
                },
                "name": "test-chart",
                "ports": [
                    {
                        "containerPort": 80,
                        "name": "http",
                        "protocol": "TCP"
                    }
                ],
                "readinessProbe": {
                    "failureThreshold": 3,
                    "httpGet": {
                        "path": "/",
                        "port": "http",
                        "scheme": "HTTP"
                    },
                    "periodSeconds": 10,
                    "successThreshold": 1,
                    "timeoutSeconds": 1
                },
                "resources": {},
                "terminationMessagePath": "/dev/termination-log",
                "terminationMessagePolicy": "File",
                "volumeMounts": [
                    {
                        "mountPath": "/var/run/secrets/kubernetes.io/serviceaccount",
                        "name": "default-token-g78f5",
                        "readOnly": true
                    }
                ]
            }
        ],
        "dnsPolicy": "ClusterFirst",
        "enableServiceLinks": true,
        "nodeName": "minikube",
        "priority": 0,
        "restartPolicy": "Always",
        "schedulerName": "default-scheduler",
        "securityContext": {},
        "serviceAccount": "default",
        "serviceAccountName": "default",
        "terminationGracePeriodSeconds": 30,
        "tolerations": [
            {
                "effect": "NoExecute",
                "key": "node.kubernetes.io/not-ready",
                "operator": "Exists",
                "tolerationSeconds": 300
            },
            {
                "effect": "NoExecute",
                "key": "node.kubernetes.io/unreachable",
                "operator": "Exists",
                "tolerationSeconds": 300
            }
        ],
        "volumes": [
            {
                "name": "default-token-g78f5",
                "secret": {
                    "defaultMode": 420,
                    "secretName": "default-token-g78f5"
                }
            }
        ]
    },
    "status": {
        "conditions": [
            {
                "lastProbeTime": null,
                "lastTransitionTime": "2019-04-18T13:48:28Z",
                "status": "True",
                "type": "Initialized"
            },
            {
                "lastProbeTime": null,
                "lastTransitionTime": "2019-04-18T13:48:29Z",
                "status": "True",
                "type": "Ready"
            },
            {
                "lastProbeTime": null,
                "lastTransitionTime": "2019-04-18T13:48:29Z",
                "status": "True",
                "type": "ContainersReady"
            },
            {
                "lastProbeTime": null,
                "lastTransitionTime": "2019-04-18T13:48:28Z",
                "status": "True",
                "type": "PodScheduled"
            }
        ],
        "containerStatuses": [
            {
                "containerID": "docker://7c9c495c262bcd28fc91ecd67eda4b839d7662903726ae254d729642f70f34c4",
                "image": "nginx:stable",
                "imageID": "docker-pullable://nginx@sha256:f7988fb6c02e0ce69257d9bd9cf37ae20a60f1df7563c3a2a6abe24160306b8d",
                "lastState": {},
                "name": "test-chart",
                "ready": true,
                "restartCount": 0,
                "state": {
                    "running": {
                        "startedAt": "2019-04-18T13:48:29Z"
                    }
                }
            }
        ],
        "hostIP": "10.0.2.15",
        "phase": "Running",
        "podIP": "172.17.0.3",
        "qosClass": "BestEffort",
        "startTime": "2019-04-18T13:48:28Z"
    }
}
```

```json
deployment
{
    "apiVersion": "extensions/v1beta1",
    "kind": "Deployment",
    "metadata": {
        "annotations": {
            "deployment.kubernetes.io/revision": "1",
            "field.cattle.io/publicEndpoints": "[{\"addresses\":[\"10.0.2.15\"],\"port\":80,\"protocol\":\"HTTP\",\"serviceName\":\"test3562:ingress-d73337797b0dbe4259c955dd6eae86e5\",\"ingressName\":\"test3562:test3562nginx\",\"hostname\":\"nginx.devops-commons.ia.alf.uk\",\"path\":\"/test3562\",\"allNodes\":false}]"
        },
        "creationTimestamp": "2019-04-18T13:48:28Z",
        "generation": 2,
        "labels": {
            "app.kubernetes.io/instance": "test3562-test-nginx",
            "app.kubernetes.io/managed-by": "Tiller",
            "app.kubernetes.io/name": "test-chart",
            "helm.sh/chart": "test-chart-0.1.0",
            "io.cattle.field/appId": "test3562-test-nginx"
        },
        "name": "test3562-test-nginx-test-chart",
        "namespace": "test3562",
        "resourceVersion": "210236",
        "selfLink": "/apis/extensions/v1beta1/namespaces/test3562/deployments/test3562-test-nginx-test-chart",
        "uid": "a50b2bfd-61e0-11e9-909d-0800276bc6a4"
    },
    "spec": {
        "progressDeadlineSeconds": 600,
        "replicas": 1,
        "revisionHistoryLimit": 10,
        "selector": {
            "matchLabels": {
                "app.kubernetes.io/instance": "test3562-test-nginx",
                "app.kubernetes.io/name": "test-chart"
            }
        },
        "strategy": {
            "rollingUpdate": {
                "maxSurge": "25%",
                "maxUnavailable": "25%"
            },
            "type": "RollingUpdate"
        },
        "template": {
            "metadata": {
                "creationTimestamp": null,
                "labels": {
                    "app.kubernetes.io/instance": "test3562-test-nginx",
                    "app.kubernetes.io/name": "test-chart"
                }
            },
            "spec": {
                "containers": [
                    {
                        "image": "nginx:stable",
                        "imagePullPolicy": "IfNotPresent",
                        "livenessProbe": {
                            "failureThreshold": 3,
                            "httpGet": {
                                "path": "/",
                                "port": "http",
                                "scheme": "HTTP"
                            },
                            "periodSeconds": 10,
                            "successThreshold": 1,
                            "timeoutSeconds": 1
                        },
                        "name": "test-chart",
                        "ports": [
                            {
                                "containerPort": 80,
                                "name": "http",
                                "protocol": "TCP"
                            }
                        ],
                        "readinessProbe": {
                            "failureThreshold": 3,
                            "httpGet": {
                                "path": "/",
                                "port": "http",
                                "scheme": "HTTP"
                            },
                            "periodSeconds": 10,
                            "successThreshold": 1,
                            "timeoutSeconds": 1
                        },
                        "resources": {},
                        "terminationMessagePath": "/dev/termination-log",
                        "terminationMessagePolicy": "File"
                    }
                ],
                "dnsPolicy": "ClusterFirst",
                "restartPolicy": "Always",
                "schedulerName": "default-scheduler",
                "securityContext": {},
                "terminationGracePeriodSeconds": 30
            }
        }
    },
    "status": {
        "availableReplicas": 1,
        "conditions": [
            {
                "lastTransitionTime": "2019-04-18T13:48:29Z",
                "lastUpdateTime": "2019-04-18T13:48:29Z",
                "message": "Deployment has minimum availability.",
                "reason": "MinimumReplicasAvailable",
                "status": "True",
                "type": "Available"
            },
            {
                "lastTransitionTime": "2019-04-18T13:48:28Z",
                "lastUpdateTime": "2019-04-18T13:48:29Z",
                "message": "ReplicaSet \"test3562-test-nginx-test-chart-7c6c57d5b5\" has successfully progressed.",
                "reason": "NewReplicaSetAvailable",
                "status": "True",
                "type": "Progressing"
            }
        ],
        "observedGeneration": 2,
        "readyReplicas": 1,
        "replicas": 1,
        "updatedReplicas": 1
    }
}
```

```json
ingress
{
    "apiVersion": "extensions/v1beta1",
    "kind": "Ingress",
    "metadata": {
        "annotations": {
            "field.cattle.io/creatorId": "user-xs5g5",
            "field.cattle.io/description": "nginx-ingress",
            "field.cattle.io/ingressState": "{\"dGVzdDM1NjJuZ2lueC90ZXN0MzU2Mi9uZ2lueC5kZXZvcHMtY29tbW9ucy5pYS5hbGYudWsvL3Rlc3QzNTYyLzgwODA=\":\"deployment:test3562:test3562-test-nginx-test-chart\"}",
            "field.cattle.io/publicEndpoints": "[{\"addresses\":[\"10.0.2.15\"],\"port\":80,\"protocol\":\"HTTP\",\"serviceName\":\"test3562:ingress-d73337797b0dbe4259c955dd6eae86e5\",\"ingressName\":\"test3562:test3562nginx\",\"hostname\":\"nginx.devops-commons.ia.alf.uk\",\"path\":\"/test3562\",\"allNodes\":false}]"
        },
        "creationTimestamp": "2019-04-18T13:48:30Z",
        "generation": 1,
        "labels": {
            "cattle.io/creator": "norman"
        },
        "name": "test3562nginx",
        "namespace": "test3562",
        "resourceVersion": "210231",
        "selfLink": "/apis/extensions/v1beta1/namespaces/test3562/ingresses/test3562nginx",
        "uid": "a688dc95-61e0-11e9-909d-0800276bc6a4"
    },
    "spec": {
        "rules": [
            {
                "host": "nginx.devops-commons.ia.alf.uk",
                "http": {
                    "paths": [
                        {
                            "backend": {
                                "serviceName": "ingress-d73337797b0dbe4259c955dd6eae86e5",
                                "servicePort": 8080
                            },
                            "path": "/test3562"
                        }
                    ]
                }
            }
        ]
    },
    "status": {
        "loadBalancer": {
            "ingress": [
                {
                    "ip": "10.0.2.15"
                }
            ]
        }
    }
}
```
