"""Validate Docker Repository"""
import base64
import urllib.parse

import requests
from requests import Response

ENDPOINT_MAPPING = {"dockerhub": "https://registry.hub.docker.com",
                    "synapse": "https://docker.synapse.org"}


class DockerRepository:
    """Forms request url and gets the docker respository
    with requests packages
    """
    def __init__(self, docker_repo: str, docker_digest: str,
                 index_endpoint: str):
        """
        Args:
            docker_repo: Docker repository without tags or sha
            docker_digest: Docker repository sha digest
            index_endpoint: Docker registry endpoint.
                            Dockerhub - https://registry.hub.docker.com
                            Synapse - https://docker.synapse.org

        """
        self.docker_repo = docker_repo
        self.docker_digest = docker_digest
        self.index_endpoint = index_endpoint

    def __str__(self):
        """str representation of docker repository"""
        return f"{self.docker_repo}@{self.docker_digest}"

    def get_request_url(self):
        """Gets request URL"""
        url = "/".join(['v2', self.docker_repo, 'manifests',
                        self.docker_digest])
        docker_request_url = urllib.parse.urljoin(self.index_endpoint, url)
        return docker_request_url

    def _get_bearer_token_url(self):
        """Gets bearer token URL"""
        initial_request = requests.get(self.get_request_url())
        www_auth = initial_request.headers['Www-Authenticate']
        auth_headers = www_auth.replace('"', '').split(",")
        # Creates a mapping of the authentication headers to its values
        auth_mapping = {head.split("=")[0]: head.split("=")[1]
                        for head in auth_headers}
        return "{0}?service={1}&scope={2}".format(auth_mapping['Bearer realm'],
                                                  auth_mapping['service'],
                                                  auth_mapping['scope'])

    def _get_bearer_token(self, username: str = None, password: str = None):
        """Gets Docker bearer token

        Args:
            user: Synapse username
            password: Synapse password

        Returns:
            Bearer token

        """
        bearer_token_url = self._get_bearer_token_url()
        auth_string = f'{username}:{password}'
        auth = base64.b64encode(auth_string.encode()).decode()
        headers = {'Authorization': f'Basic {auth}'}
        bearer_token_request = requests.get(bearer_token_url,
                                            headers=headers)
        if bearer_token_request.status_code != 200:
            raise ValueError(bearer_token_request.json().get('details'))
        return bearer_token_request.json()['token']

    def get(self, **kwargs):
        """Gets docker repository response

        Args:
            **kwargs: username: Docker registry username
                      password: Docker registry password

        Returns:
            Docker response
        """
        token = self._get_bearer_token(**kwargs)
        resp = requests.get(self.get_request_url(),
                            headers={'Authorization': 'Bearer %s' % token})
        return resp


def check_docker_exists(docker_resp: 'Response'):
    """Check if Docker image + sha exists

    Args:
        docker_resp: Docker response

    Raises:
        ValueError: If docker image and sha doesn't exist

    """
    if docker_resp.status_code != 200:
        raise ValueError("Docker image and sha digest must exist.")


def check_docker_size(docker_resp: Response, size: int = 1000):
    """Checks Docker container is less than specified size

    Args:
        docker_resp: Docker response
        size: Size in GB

    Raises:
        ValueError: Docker container is over specified size

    """
    docker_size = sum([layer['size']
                       for layer in docker_resp.json()['layers']])
    if docker_size/1000000000.0 >= size:
        raise ValueError("Docker image must be less than a terabyte.")


def validate_docker(docker_repo: str, docker_digest: str, index_endpoint: str,
                    username: str = None, password: str = None):
    """Validates a Docker Respository

    Args:
        docker_repo: Docker repository without tags or sha
        docker_digest: Docker repository sha digest
        index_endpoint: Docker registry endpoint.
                        Dockerhub - https://registry.hub.docker.com
                        Synapse - https://docker.synapse.org
        username: Docker registry username
        password: Docker registry password

    Returns:
        True if valid, False if not
    """
    docker_cls = DockerRepository(docker_repo=docker_repo,
                                  docker_digest=docker_digest,
                                  index_endpoint=index_endpoint)
    docker_resp = docker_cls.get(username=username,
                                 password=password)
    check_docker_exists(docker_resp)
    check_docker_size(docker_resp)
    return True
