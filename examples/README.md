# ALF Platform Configuration File

Specify the verson of rancher you are using as there are some API differences
```json
"rancherVersion": "2.2.1"
```

Specify the ID of the Kubernetes cluster found in Rancher that will be used for all provisioning activities
```json
"clusterid": "c-gnq7l"
```

Specify the ID of the project found in Rancher, that will host the tenant namespaces
```json
	"projectid": "c-gnq7l:p-lj7tk"
```

Specify the the chart mapping data, in this example we include a mapping for the NGINX chart, providing the rancher catalogue id, a name and description and customise it using the ***answers*** key.

You can also optionally provide an ingress key that will create an ingress for the chart.

```json
"charts": {
  "nginx": {
    "catalog": "catalog://?catalog=shared-git&template=test-chart&version=0.1.0",
    "name": "test-nginx",
    "description": "test nginx deployment",
    "answers": {"controller.stats.enabled": "true"},
		"ingress": {"hostname": "nginx.devops-commons.ia.alf.uk","targetPort": 8080}
  }
}
```

Specify the Rancher API bearer token to be used for all API requests
```json
"bearer": "token-5:37837832773279327979"
```

Specify the Rancher Hostname or IP address to be used for all API requests
```json
"host": "https://101.179.205.252"
```

Specify RAM or CPU limits to be applied to the namespace when it is created

```json
	"containerLimits": {}
```

Specify the Physical Volume size when it is created

```json
  "volumeStorage": "4Gi",
```

Specify the size of the volume claim when its created, in most cases this will be the same as PV volume size and will be used for all Pods.

```json
	"claimStorage": "4Gi"
```

For Gluster, the configuration shown below can be used unmodified, BUT a **rancher-gluster.yml** file must exist for the cluster as the ***kubectl apply -f ./rancher-gluster.yml -n namespace*** will be run to alllow the PV and PVC to bind.

```json
"glusterfs": {
	"endpoints": "gluster",
	"path": "V2",
	"readOnly": false,
	"type": "/v3/cluster/schemas/glusterfsVolumeSource"
}
```

For local storage the local mount point must exist and

```json
"local": {
	"path": "/Users/malorr/Downloads/rancher-vol2",
	"type": "/v3/cluster/schemas/localVolumeSource"
}
```

as well as the nodeAffinity keys, these will be specific to the cluster

```json
"nodeAffinity": {
	"required": {
		"nodeSelectorTerms": [{
			"matchExpressions": [{
				"key": "cluster",
				"operator": "In",
				"type": "/v3/cluster/schemas/nodeSelectorRequirement",
				"values": ["local"]
			}],
			"type": "/v3/cluster/schemas/nodeSelectorTerm"
		}],
		"type": "/v3/cluster/schemas/nodeSelector"
	},
	"type": "/v3/cluster/schemas/volumeNodeAffinity"
}
```
