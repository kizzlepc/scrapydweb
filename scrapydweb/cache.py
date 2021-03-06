# coding: utf8
import os
import sys
import time
import json
# import traceback

import requests


ignore_finished = True
dict_finished = {}


def refresh_cache(timeout=60):
    for node, SCRAPYD_SERVER in enumerate(SCRAPYD_SERVERS, 1):
        auth = SCRAPYD_SERVERS_AUTHS[node-1]
        auth = tuple(auth) if auth else auth  # TypeError: 'list' object is not callable
        try:
            r_projects = session.get('http://%s/listprojects.json' % SCRAPYD_SERVER, timeout=timeout, auth=auth)
            projects = r_projects.json()['projects']
        except Exception as err:
            # print(traceback.format_exc())
            print("!!! Cache projects fail: %s %s" % (err.__class__.__name__, err))
            continue

        for project in projects:
            try:
                r_jobs = session.get('http://%s/listjobs.json?project=%s' % (SCRAPYD_SERVER, project), timeout=timeout, auth=auth)
                jobs = r_jobs.json()
            except Exception as err:
                print("!!! Cache jobs fail: %s %s" % (err.__class__.__name__, err))
                continue

            running_jobs = jobs['running']
            finished_jobs = []
            for job_ in jobs['finished']:
                key = '%s/%s/%s/%s' % (node, project, job_['spider'], job_['id'])
                if ignore_finished:
                    dict_finished[key] = ''
                elif key not in dict_finished:
                    dict_finished[key] = ''
                    finished_jobs.append(job_)
                else:
                    pass


            for job_ in running_jobs + finished_jobs:
                try:
                    spider = job_['spider']
                    job = job_['id']
                    # http://127.0.0.1:5000/log/utf8/proxy/test/55f1f388a7ae11e8b9b114dda9e91c2f/
                    url = ('http://{scrapydweb_host}:{scrapydweb_port}/'
                           '{node}/log/{opt}/{project}/{spider}/{job}/').format(
                        scrapydweb_host=scrapydweb_host, scrapydweb_port=scrapydweb_port,
                        node=node, opt='utf8', project=project, spider=spider, job=job)
                    # 'POST' to avoid using cache, see log.py
                    r = session.post(url, timeout=timeout)
                    print(">>> Cache %s %s Bytes %s" % (r.status_code, len(r.content), url))
                    time.sleep(cache_request_interval)
                except Exception as err:
                    print("!!! Cache html fail: %s %s" % (err.__class__.__name__, err))


def main():
    global ignore_finished
    while True:
        start_time = time.time()
        try:
            if ignore_finished:
                time.sleep(10)
            refresh_cache()
            print(">>> Cache cost %s seconds" % int(time.time() - start_time))
            print(">>> Cache wait %s seconds" % cache_round_interval)
            time.sleep(cache_round_interval)
        except KeyboardInterrupt:
            sys.exit("!!! Cache cancelled by KeyboardInterrupt")
        except Exception as err:
            print("!!! Cache fail: %s %s" % (err.__class__.__name__, err))
        else:
            print(">>> Cache done at %s" % time.ctime())


        if ignore_finished:
            ignore_finished = False
        if len(dict_finished) > 10000:
            dict_finished.clear()
            ignore_finished = True


if __name__ == '__main__':
    (scrapydweb_host, scrapydweb_port, username, password,
    SCRAPYD_SERVERS, SCRAPYD_SERVERS_AUTHS,
    cache_round_interval, cache_request_interval) = sys.argv[1:]

    SCRAPYD_SERVERS = json.loads(SCRAPYD_SERVERS)
    SCRAPYD_SERVERS_AUTHS = json.loads(SCRAPYD_SERVERS_AUTHS)
    cache_round_interval = int(cache_round_interval)
    cache_request_interval = int(cache_request_interval)

    session = requests.Session()
    if username and password:
        session.auth = (username, password)

    main()
