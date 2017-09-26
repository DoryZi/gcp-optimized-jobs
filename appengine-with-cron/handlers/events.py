import webapp2
import logging
import os

from services.pubsub_service import publish_to_topic

EVENTS_PREFIX = "/events/"

class EventHandler(webapp2.RequestHandler):
    def get(self):
        logging.info(os.environ)
        topic_name = self.request.path.split(EVENTS_PREFIX)[-1]
        publish_to_topic(topic_name, msg='run-jobs')
        self.response.status = 204
