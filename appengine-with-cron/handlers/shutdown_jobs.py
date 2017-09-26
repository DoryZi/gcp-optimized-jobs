import webapp2
import logging
from services.kubernetes_service import KubernetesService

kuberService = KubernetesService()


class ShutDownJobsHandler(webapp2.RequestHandler):
    def get(self):
        logging.info("checking if need to shutdown")
        kuberService.shutdown_cluster_on_jobs_complete()


    