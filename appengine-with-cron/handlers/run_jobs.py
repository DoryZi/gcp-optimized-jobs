#!/usr/bin/env python
#
# Copyright 2015 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import cloudstorage as gcs
import logging
import os
import webapp2
from apiclient.discovery import build
from settings import Settings
from services.kubernetes_service import KubernetesService


EVENTS_PREFIX = "/events/"

kuberService = KubernetesService()

class RunJobsHandler(webapp2.RequestHandler):
    ''' runs all jobs in jobs.txt in default bucket by calling pubsub method
    this jobs kicks off all the list of jobs via a cloud function'''
    def get(self):
        try:
            logging.info("running jobs")
            jobs_list = Settings.get("JOBS_LIST").split()
            for job_name in jobs_list:
                job_name = job_name.replace("_", "-")
                logging.info('about to publish job {}'.format(job_name))

                containers_info = [
                    {
                        "image": Settings.get("IMAGE_NAME"),
                        "name": job_name,
                        "env_vars": [
                            { "name": "ENV_VAR1", "value": "some value"}
                        ]
                    }
                ]

                job_container_env_vars = Settings.get('CONTAINER_ENV_VARS').split()
                for env_var in job_container_env_vars:
                    logging.info('adding container var {}'.format(env_var))
                    containers_info[0]['env_vars'].append({
                        "name": env_var,
                        "value": Settings.get(env_var)
                    })
                kuberService.kubernetes_job(containers_info, job_name, False)
            self.response.status = 204
        except Exception, e:
            logging.exception(e)
            self.response.status = 500
            self.response.write("error running jobs, check logs for more details.")
        else:
            self.response.write("jobs published successfully")
