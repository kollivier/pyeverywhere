import os
import sys

import requests


def download_file(url, output_file, max_tries=5):
    # based on http://stackoverflow.com/questions/22894211/how-to-resume-file-download-in-python
    current_try = 1
    headers = {}

    toolbar_width = 50
    current_percent = 0
    bytes = 0

    print("Downloading %s" % url)

    while current_try <= max_tries:
        if os.path.exists(output_file):
            bytes = os.path.getsize(output_file)
            headers['Range'] = 'bytes=%d' % bytes

        r = requests.get(url, stream=True, headers=headers, verify=False, allow_redirects=True)
        if r.status_code != 200:
            raise Exception("Download failed for %s. Error code: %d" % (url, r.status_code))

        CHUNK_SIZE = 8192
        total_size = "unknown"

        if 'Content-Length' in r.headers:
            total_size = int(r.headers['Content-Length'])

        if total_size is not None:
            if current_try == 1:
                # setup toolbar
                sys.stdout.write("[%s]" % (" " * toolbar_width))
                sys.stdout.flush()
                sys.stdout.write("\b" * (toolbar_width+1))  # return to start of line, after '['

        try:
            with open(output_file, 'wb') as f:
                for chunk in r.iter_content(CHUNK_SIZE):
                    f.write(chunk)
                    bytes += len(chunk)

                    if total_size is not None:
                        percent = 100 * float(bytes)/float(total_size)
                        if percent > current_percent + 1:
                            current_percent = percent
                            sys.stdout.write("=")
                            sys.stdout.flush()
                    else:
                        sys.stdout.write("\rDownloaded %d of %s bytes" % (bytes, str(total_size)))
            current_try = 6
        except Exception as e:
            import traceback
            traceback.print_exc()
            current_try += 1
        finally:
            r.close()
