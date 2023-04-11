# k8s Cleanup Script
## _Cleans up expired pods, deployments and namespaces_

k8s cleanup is a python script created which checks for pods expiry and depending upon that kills/delete pods.
It also cleanus up the deployments and namespaces.

## Features
- deletes pods
- deletes deployments
- delete namespaces 
- Deletes them on scheduled intervals with expiry

## How to deploy
Deploying k8s cleanup is simple, you only required Helm3
```sh
helm upgrade --install k8s-cleaner ./helm_chart
```

## Environment Variables
There are 3 important environment variables presnet
- EXCLUDE_NAMESPACES
- MAX_DAYS
- POD_STATUS

###### Exclude Namespaces: 
This will exclude the namespaces from filtering and deletion, you can provide a list here 
```sh
- name: EXCLUDE_NAMESPACES
  value: "demo, default, test"
```

###### Max_Days: 
This will only consider pods which are older than MAX_DAYS.
```sh
- name: MAX_DAYS
  value: "5"
```

###### POD_STATUS: 
This will only consider pods with following status.
```sh
- name: POD_STATUS
  value: "Running, Succeeded, Failed, ContainerCreating, Error, CrashLoopBackOff"
```

## Building Docker Image needed for this Cleanup
###### Steps
```
1. If you are building an Image, being in mac, use the following command
   1.1 Goto the Directory 'devsecops-utility/k8s-cleanup/'
   1.2 Build the Image. 
       * If you're in Mac and launching the container/pod in Linux machine. Use the following command
         Command: docker build . -t <image-name>:<image-version> --platform linux/amd64 
       * If you are using mac M1 then user below command
         Command: docker buildx build --platform linux/amd64 -t <image-name>:<image-version> .
       * If you're building in Linux and launching the container/pod in Linux, use the following command
         Command: docker build . -t <image-name>:<image-version>
```
