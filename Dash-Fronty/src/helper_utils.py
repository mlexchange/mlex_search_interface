import requests

def get_job(user, mlex_app):
    url = 'http://job-service:8080/api/v0/jobs?'
    if user:
        url += ('&user=' + user)
    if mlex_app:
        url += ('&mlex_app=' + mlex_app)
    
    response = requests.get(url).json()
    return response

def init_counters(user, job_type):
    job_list = get_job(user, 'seg-demo')
    if job_list is not None:
        for job in reversed(job_list):
            last_job = job['job_kwargs']['kwargs']['job_type'].split()
            value = int(last_job[-1])
            last_job = ' '.join(last_job[0:-1])
            if last_job == job_type:
                return value + 1
    return 0