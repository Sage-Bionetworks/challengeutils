"""Validate Docker Repository"""
import base64
import requests


def _get_bearer_token_url(docker_request_url):
    """Gets bearer token URL

    Args:
        docker_request_url: Full Docker request URL

    Returns:
        Docker bearer token URL
    """
    initial_request = requests.get(docker_request_url)
    www_auth = initial_request.headers['Www-Authenticate']
    auth_headers = www_auth.replace('"', '').split(",")
    for head in auth_headers:
        if head.startswith("Bearer realm="):
            bearer_realm = head.split('Bearer realm=')[1]
        elif head.startswith('service='):
            service = head.split('service=')[1]
        elif head.startswith('scope='):
            scope = head.split('scope=')[1]
    return "{0}?service={1}&scope={2}".format(bearer_realm, service, scope)


def _get_bearer_token(docker_request_url, user, password):
    """Gets Docker bearer token

    Args:
        docker_request_url: Full Docker request URL
        user: Synapse username
        password: Synapse password

    Returns:
        Bearer token
    """
    bearer_token_url = _get_bearer_token_url(docker_request_url)
    auth_string = user + ":" + password
    auth = base64.b64encode(auth_string.encode()).decode()
    headers = {'Authorization': 'Basic %s' % auth}
    bearer_token_request = requests.get(bearer_token_url,
                                        headers=headers)
    return bearer_token_request.json()['token']


def _validate(docker_repo, docker_digest, index_endpoint,
              user, password):
    """Validates existence of docker repository + sha digest
    and max size

    Args:
        docker_repo: Docker repository
        docker_digest: Docker sha digest
        index_endpoint: Synapse docker registry / docker hub
        user: Docker registry username
        password: Docker registry password

    Returns:
        True if valid, False if not
    """
    docker_request_url = '{0}/v2/{1}/manifests/{2}'.format(index_endpoint,
                                                           docker_repo,
                                                           docker_digest)
    token = _get_bearer_token(docker_request_url, user, password)
    resp = requests.get(docker_request_url,
                        headers={'Authorization': 'Bearer %s' % token})

    if resp.status_code != 200:
        print("Docker image + sha digest must exist.  You submitted "
              f"{docker_repo}@{docker_digest}")
        return False
    # Must check docker image size
    docker_size = sum([layer['size'] for layer in resp.json()['layers']])
    if docker_size/1000000000.0 >= 1000:
        print("Docker container must be less than a teribyte")
        return False
    return True


def validate_docker_submission(syn, submissionid):
    """Validates Synapse docker repository + sha digest submission
    This function requires users to have a synapse config file using
    synapse username and password

    Args:
        syn: Synapse connection
        submissionid: Submission id

    Returns:
        True if valid, False if not
    """
    config = syn.getConfigFile(syn.configPath)
    authen = dict(config.items("authentication"))
    if authen.get("username") is None and authen.get("password") is None:
        raise Exception('Config file must have username and password')

    docker_sub = syn.getSubmission(submissionid)
    docker_repository = docker_sub.dockerRepositoryName
    docker_repo = docker_repository.replace("docker.synapse.org/", "")
    docker_digest = docker_sub.dockerDigest
    index_endpoint = "https://docker.synapse.org"

    valid = _validate(docker_repo, docker_digest, index_endpoint,
                      authen['username'], authen['password'])
    return valid
