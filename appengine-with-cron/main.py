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


import os
import logging
import webapp2

from urllib3.connection import UnverifiedHTTPSConnection
from urllib3.connectionpool import HTTPSConnectionPool

# Override the default Connection class for the HTTPSConnectionPool.
HTTPSConnectionPool.ConnectionCls = UnverifiedHTTPSConnection

from handlers.run_jobs import RunJobsHandler

from handlers.shutdown_jobs import ShutDownJobsHandler
from handlers.events import  EventHandler
from settings import Settings

app = webapp2.WSGIApplication([('/events/shutdown-jobs', ShutDownJobsHandler),
                               ('/events/run-jobs', RunJobsHandler),
                               ('/events/.*', EventHandler), ],
                              debug=True)