import base64
import datetime
import json
import gzip
import httplib
import logging
import math
import socket
import StringIO
import sys
import time

# FIXME: we don't want this in the shipping code, but for now we are using
# a self-signed cert so allow that to go through.
import ssl
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except Exception:
    # if we're running less than 2.7.9, unfortunately we don't even verify certs by default,
    # so the 2.7.9 fixes we're using don't apply :(
    if sys.version_info < (2, 7, 9):
        pass
    else:
        raise

import cache
server_format_string = "%Y-%m-%dT%H:%M:%SZ"


def UTCTimeToLocal(d):
    # calculate time difference from utcnow and the local system time reported by OS
    offset = datetime.datetime.now() - datetime.datetime.utcnow()

    # Add offset to UTC time and return it
    return d + datetime.timedelta(offset.days, offset.seconds)


def LocalTimeToUTC(d):
    # calculate time difference from utcnow and the local system time reported by OS
    offset = datetime.datetime.now() - datetime.datetime.utcnow()

    # Add offset to UTC time and return it
    return d - datetime.timedelta(offset.days, offset.seconds)


class RESTError(Exception):
    def __init__(self, message, error_code, data=None):
        super(RESTError, self).__init__(message)

        self.http_code = error_code
        self.data = data

    def get_http_error_code(self):
        return self.http_code

    def get_error_html(self):
        return self.data


class BadRequestError(RESTError):
    pass


class AuthorizationError(Exception):
    pass


class ServerConnectionError(Exception):
    pass


class RESTClient(object):
    def __init__(self, domain):
        self.domain = domain
        self.data = cache.get_cache()

        self.client_id = None
        self.client_secret = None

        self.timeout = 20

    def set_domain(self, domain):
        self.domain = domain

    def set_timeout(self, timeout):
        self.timeout = timeout

    def get_auth_token(self):
        data = cache.get_cache()
        if "token" in data:
            return data["token"]
        return None

    def invalidate_token(self):
        data = cache.get_cache()
        if "token" in data:
            del data["token"]
            cache.save_cache()

    def sign_in(self, username, password):
        self.invalidate_token()  # don't pass a user token when we're trying to sign in
        result = self.make_api_call("/o/token/", data="grant_type=password&username=%s&password=%s" % (username, password), method="POST", data_type="application/x-www-form-urlencoded")

        if "access_token" in result:
            cache_data = cache.get_cache()
            cache_data["token"] = result["access_token"]
            cache_data["token_type"] = result["token_type"]
            cache.save_cache()
        return result

    def server_time_to_timestamp(self, time_string):
        time_string = time_string.split(".")[0]
        if not time_string.endswith("Z"):
            time_string += "Z"
        utc_time = datetime.datetime.strptime(time_string, server_format_string)
        local_time = UTCTimeToLocal(utc_time).timetuple()
        return time.mktime(local_time)

    def timestamp_to_server_time(self, timestamp):
        local_time = datetime.datetime.fromtimestamp(math.ceil(timestamp))
        utc_time = LocalTimeToUTC(local_time)
        return utc_time.strftime(server_format_string)

    def call_api(self, api, data=None, method="GET", last_checked=None, filter=None, data_type="application/json"):
        cache_data = cache.get_cache()
        if not "token" in cache_data:
            raise AuthorizationError("You are not signed in. Please sign in before making REST calls.")

        return self.make_api_call(api, data, method, last_checked, filter, data_type)

    def make_api_call(self, api, data=None, method="GET", last_checked=None, filter=None, data_type="application/json"):
        start = time.time()
        conn = httplib.HTTPSConnection(self.domain, timeout=self.timeout)
        if self.domain == "localhost:8000" or sys.platform.startswith("darwin"):  # FIXME: Find a way to get SSL working again on Mac...
            conn = httplib.HTTPConnection(self.domain, timeout=self.timeout)

        # conn.set_debuglevel(1)

        headers = {"Accept": "application/json", "X-Requested-With": "XMLHttpRequest"}
        cache_data = cache.get_cache()
        if "token" in cache_data:
            headers['Authorization'] = "%s %s" % (cache_data["token_type"], cache_data["token"])
        elif self.client_id is not None and self.client_secret is not None:
            userAndPass = base64.b64encode(b"%s:%s" % (self.client_id, self.client_secret)).decode("ascii")
            headers['Authorization'] = 'Basic %s' % userAndPass

        headers['X-HTTP-Method-Override'] = method
        if method == "GET":
            headers['Accept-encoding'] = 'gzip, deflate'
        if data is not None:
            if data_type is not None:
                headers['Content-Type'] = data_type
            headers['Content-Length'] = len(data)
        #then connect
        filter_string = ""
        if last_checked is not None:
            filter_string += "&last_modified__gte=" + LocalTimeToUTC(last_checked).strftime(server_format_string)

        if filter is not None:
            for field_name in filter:
                value = filter[field_name]
                if not isinstance(value, basestring):
                    value = ','.join(map(str, value))
                filter_string += "&%s=%s" % (field_name, str(value))

        if filter_string != "":
            filter_string = "?" + filter_string[1:]

        api += filter_string

        logging.debug("Headers: %r" % headers)
        logging.debug("Calling %s" % api)
        if data is not None:
            logging.debug("Sending data: %s" % data)

        try:
            conn.request(method, api, body=data, headers=headers)
            response = conn.getresponse()
            headers_list = response.getheaders()
            resp_headers = {}
            for header_name, header_value in headers_list:
                resp_headers[header_name] = header_value

            data = response.read()
            if 'content-encoding' in resp_headers:
                if resp_headers['content-encoding'] == 'gzip':
                    logging.debug("Decompressing gzip content")
                    compresseddata = StringIO.StringIO(data)
                    gzipper = gzip.GzipFile(fileobj=compresseddata)
                    data = gzipper.read()
                else:
                    logging.debug("Content-Encoding = %s" % resp_headers['Content-Encoding'])
            else:
                logging.debug("Response headers are: %r" % resp_headers)

            if response.status >= 300:
                logging.error("data:")
                logging.error("%r" % data)
                if response.status == 401:
                    self.invalidate_token()  # if we have a token, it's bad, so wipe it
                    raise AuthorizationError("Incorrect username or password")
                elif response.status == 400:
                    raise BadRequestError("The server found problems with the request.", response.status, json.loads(data))
                else:
                    raise RESTError(str(data), response.status)

            if data != '':
                data = json.loads(data)
            else:
                data = {}

            elapsed = time.time() - start
            logging.info("Call %s took %r seconds" % (api, elapsed))
            return data
        except httplib.BadStatusLine as e:
            logging.error("Got bad status line on line %s" % e.line)
            return {}
        except socket.timeout:
            raise ServerConnectionError("Server connection attempt timed out.")
        except AuthorizationError as e:
            # if we have a token, it is probably invalid, so we should try a full sign in.
            if "token" in cache_data:
                self.invalidate_token()
                return self.call_api(api, data, method, last_checked, filter, data_type)
        except Exception as e:
            if hasattr(e, "errno") and e.errno == 61:
                raise ServerConnectionError("Connection to server refused.")
            else:
                raise e
