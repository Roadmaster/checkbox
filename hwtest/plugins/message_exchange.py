import time
import logging
import pprint
import StringIO
import bz2

from socket import gethostname

from hwtest.plugin import Plugin
from hwtest.transport import HTTPTransport
from hwtest.log import format_delta


class MessageExchange(Plugin):

    transport_factory = HTTPTransport
    transport_url = "https://launchpad.net/hwdb/+submit"

    persist_name = "message-exchange"

    def __init__(self):
        self._transport = self.transport_factory(self.transport_url)

    def exchange(self):
        report = self._manager.report

        # 'field.date_created':    u'2007-08-01',
        # 'field.private':         u'',
        # 'field.contactable':     u'',
        # 'field.livecd':          u'',
        # 'field.submission_id':   u'unique ID 1',
        # 'field.emailaddress':    u'test@canonical.com',
        # 'field.distribution':    u'ubuntu',
        # 'field.distrorelease':   u'5.04',
        # 'field.architecture':    u'i386',
        # 'field.system':          u'HP 6543',
        # 'field.submission_data': data,
        # 'field.actions.upload':  u'Upload'}

        report.finalise()

        form = []
        for k, v in report.info.items():
            form.append(('field.%s' % k, str(v).encode("utf-8")))

 
        form.append(('field.format', u'VERSION_1'))
        form.append(('field.emailaddress', report.email))
        form.append(('field.actions.upload', u'Upload'))


        # Set the filename based on the hostname
        filename = '%s.xml.bz2' % str(gethostname())
        
        # bzip2 compress the payload and attach it to the form
        payload = report.toxml()
        cpayload = bz2.compress(payload)
        f = StringIO.StringIO(cpayload)
        f.name = filename
        f.size = len(cpayload)
        form.append(('field.submission_data', f))

        logging.info("System ID: %s", report.info['system'])
        logging.info("Submission ID: %s", report.info['submission_key'])

        if logging.getLogger().getEffectiveLevel() <= logging.DEBUG:
            logging.debug("Sending payload:\n%s", pprint.pformat(payload))

        start_time = time.time()

        ret = self._transport.exchange(form)

        if not ret:
            # HACK: this should return a useful error message
            self._manager.set_error("Communication failure")
            return

        if logging.getLogger().getEffectiveLevel() <= logging.DEBUG:
            logging.debug("Response headers:\n%s",
                          pprint.pformat(ret.headers.items()))

        headers = ret.headers.getheaders("x-launchpad-hwdb-submission")
        for header in headers:
            if "Error" in header:
                # HACK: this should return a useful error message
                self._manager.set_error("Submission failure")
                logging.error(header)
                return

        response = ret.read()
        logging.info("Sent %d bytes and received %d bytes in %s.",
                     len(form), len(response),
                     format_delta(time.time() - start_time))


factory = MessageExchange
