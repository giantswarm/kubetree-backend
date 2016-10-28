[![](https://img.shields.io/docker/pulls/giantswarm/kubetree-backend.svg)](http://hub.docker.com/giantswarm/kubetree-backend)

# Kubetree

A little tool to visualize the RAM usage of all containers running on a Kubernetes cluster in form of a treemap. Containers are grouped by namespace.

![Example Screenshot](https://cloud.githubusercontent.com/assets/273727/19822994/97a88bf2-9d66-11e6-9e9f-0ed2361fecc9.png)

The frontend code resides in a separate repository: [kubetree-frontend](https://github.com/giantswarm/kubetree-frontend).

## Installation

To deploy Kubetree on your Kubernetes cluster:

```nohighlight
kubectl create namespace kubetree
kubectl apply -f https://raw.githubusercontent.com/giantswarm/kubetree-backend/master/kubernetes/deployment.yml
kubectl apply -f https://github.com/giantswarm/kubetree-backend/blob/master/kubernetes/service.yml
```

Access Kubetree for example via the API proxy at

```nohighlight
https://<api-endpoint>/api/v1/proxy/namespaces/kubetree/services/kubetree/
```

or add Ingress for this service.
