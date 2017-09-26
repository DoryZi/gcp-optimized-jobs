import os
import logging
import datetime
import kubernetes.client
from kubernetes.client.rest import ApiException

import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

from apiclient.discovery import build

from settings import Settings



# Google Application Credentials
PROJECT_ID = Settings.get("CLOUDENGINE_PROJECT_ID")
ZONE = Settings.get("CLOUDENGINE_ZONE")
CLUSTER_ID = Settings.get("CLOUDENGINE_CLUSTER_ID")
NODE_POOL_ID = Settings.get("CLOUDENGINE_POOL_ID")
KUBERNETES_ENDPOINT = Settings.get("KUBERNETES_ENDPOINT")
KUBERNETES_TOKEN = Settings.get("KUBERNETES_TOKEN")
GOOGLE_APPLICATION_CREDENTIALS="../google_computer_engine.json"

# Get this with APISERVER=$(kubectl config view | grep server | cut -f 2- -d ":" | tr -d " ")
#endpoint = "https://104.197.67.212"
# After creating your cluster and authing with gcloud get the value of token with.
# TOKEN=$(kubectl describe secret $(kubectl get secrets | grep default | cut -f1 -d ' ') | grep -E '^token' | cut -f2 -d':' | tr -d '\t')

# Kubernetes API authentication
kubernetes.client.configuration.host = KUBERNETES_ENDPOINT
kubernetes.client.configuration.api_key['authorization'] = KUBERNETES_TOKEN
kubernetes.client.configuration.api_key_prefix['authorization'] = 'Bearer'
kubernetes.client.configuration.verify_ssl = False
kubernetes.client.configuration.assert_hostname = False

class KubernetesService():

    def __init__(self, namespace='default'):
        self.api_instance = kubernetes.client.BatchV1Api()
        service = build('container', 'v1')
        self.nodes = service.projects().zones().clusters().nodePools()
        self.namespace = namespace

    def shutdown_cluster_on_jobs_complete(self):
        api_response = self.api_instance.list_namespaced_job(self.namespace)
        if next((item for item in api_response.items if item.status.succeeded != 1), None) is None:
            logging.info("no running jobs found, shutting down cluster")
            self.setClusterSize(0)
        else:
            logging.info("found running jobs, keeping cluster up")

    def kubernetes_job(self, containers_info,  job_name='default_job', shutdown_on_finish=True):

        # Scale the Kubernetes to 3 nodes
        self.setClusterSize(3)
        timestampped_job_name = "{}-{:%Y-%m-%d-%H-%M-%S}".format(job_name, datetime.datetime.now())
        # Adding the container to a pod definition
        pod = kubernetes.client.V1PodSpec()
        pod.containers = self.create_containers(containers_info)
        pod.name = "p-{}".format(timestampped_job_name)
        pod.restart_policy = 'OnFailure'
        # Adding the pod to a Job template
        template = kubernetes.client.V1PodTemplateSpec()
        template_metadata = kubernetes.client.V1ObjectMeta()
        template_metadata.name = "tpl-{}".format(timestampped_job_name)
        template.metadata = template_metadata
        template.spec = pod
        # Adding the Job Template to the Job spec
        spec = kubernetes.client.V1JobSpec()
        spec.template = template
        # Adding the final job spec to the top level Job object
        body = kubernetes.client.V1Job()
        body.api_version = "batch/v1"
        body.kind = "Job"
        metadata = kubernetes.client.V1ObjectMeta()
        metadata.name = timestampped_job_name
        body.metadata = metadata
        body.spec = spec
        try:
            # Creating the job
            api_response = self.api_instance.create_namespaced_job(self.namespace, body)
            logging.info('job creations result'.format(api_response))
        except ApiException as e:
            print("Exception when calling BatchV1Api->create_namespaced_job: %s\n" % e)

        if shutdown_on_finish:
            self.shutdown_on_finish(metadata.name)

    def shutdown_on_finish(self,jobname):
        # Listing all jobs in the namespace
        name = jobname
        # Waiting for the job succeeded status to be one
        check = True
        while check:
            api_response = self.api_instance.list_namespaced_job(self.namespace)
            for item in api_response.items:
                if item.metadata.labels['job-name']==name:
                    if item.status.succeeded==1:
                        check = False
        # Delete the job once it's complete
        delete = kubernetes.client.V1DeleteOptions()
        try:
            api_response = self.api_instance.delete_namespaced_job(name, self.namespace, delete)
            logging.info(api_response)
        except ApiException as e:
            print("Exception when calling BatchV1Api->delete_namespaced_job: %s\n" % e)
        self.setClusterSize(0)

    def setClusterSize(self, newSize):
        logging.info("resizing cluster {} to {}".format(CLUSTER_ID, newSize))
        self.nodes.setSize(projectId=PROJECT_ID, zone=ZONE,
                           clusterId=CLUSTER_ID, nodePoolId=NODE_POOL_ID,
                           body={"nodeCount": newSize}).execute()

    def create_containers(self, containers_info):
        k_env_vars = []
        containers = []
        for container_info in containers_info:
            for env_var in container_info['env_vars']:
                # Defining an env var
                k_env_var = kubernetes.client.V1EnvVar()
                k_env_var.name = env_var['name']
                k_env_var.value = env_var['value']
                k_env_vars.append(k_env_var)
            # Defining the container
            container = kubernetes.client.V1Container()
            container.image = container_info['image']
            if container_info.get('command') is not None:
                container.command = container_info['command']
            container.name = container_info['name']

            # Adding the env to the container definition
            container.env = k_env_vars
            containers.append(container)
        return containers