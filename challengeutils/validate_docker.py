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
    auth_headers = initial_request.headers['Www-Authenticate'].replace('"', '').split(",")
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


def validate_docker(syn, docker_repository, docker_digest,
                    index_endpoint="https://docker.synapse.org"):
    """Validates docker repository + sha digest
    This function requires users to have a synapse config file using
    synapse username and password

    Args:
        syn: Synapse connection
        docker_repository: Docker repository
        docker_digest: Docker sha digest
        index_endpoint: Synapse docker registry / docker hub

    Returns:
        True if valid, False if not
    """
    config = syn.getConfigFile(syn.configPath)
    authen = dict(config.items("authentication"))
    if authen.get("username") is None and authen.get("password") is None:
        raise Exception('Config file must have username and password')
    docker_repo = docker_repository.replace("docker.synapse.org/", "")
    docker_request_url = '{0}/v2/{1}/manifests/{2}'.format(index_endpoint,
                                                           docker_repo,
                                                           docker_digest)
    token = _get_bearer_token(docker_request_url, authen['username'],
                              authen['password'])
    resp = requests.get(docker_request_url,
                        headers={'Authorization': 'Bearer %s' % token})

    if resp.status_code != 200:
        print("Docker image + sha digest must exist.  You submitted "
              f"{docker_repository}@{docker_digest}")
        return False
    # Must check docker image size
    docker_size = sum([layer['size'] for layer in resp.json()['layers']])
    if docker_size/1000000000.0 >= 1000:
        print("Docker container must be less than a teribyte")
        return False
    return True
