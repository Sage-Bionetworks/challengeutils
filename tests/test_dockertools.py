"""Tests challengeutils.dockertool functions"""
# pylint: disable=line-too-long
from unittest.mock import Mock, patch
import uuid

import pytest
import requests
import synapseclient

from challengeutils import dockertools
from challengeutils.dockertools import (DockerRepository,
                                        ENDPOINT_MAPPING)

SYN = synapseclient.Synapse()


class TestDockerRepository:
    """Tests DockerRepository class"""

    def setup(self):
        """Setup test"""
        self.docker_cls = DockerRepository(
            docker_repo="testme",
            docker_digest="willthiswork",
            index_endpoint=ENDPOINT_MAPPING["synapse"]
        )
        self.username = "myuser"
        self.password = "mypassword"
        self.token = str(uuid.uuid1())
        self.auth_headers = {'Authorization': f'Bearer {self.token}'}
        self.request_url = "https://docker.synapse.org/v2/testme/manifests/willthiswork"  # noqa pylint: disable=line-too-long

    def test_string_representation(self):
        """Tests string representation of docker repo"""
        assert str(self.docker_cls) == "testme@willthiswork"

    def test_get_request_url(self):
        """Tests get request url"""
        url = self.docker_cls.get_request_url()
        assert url == self.request_url

    def test__get_bearer_token_url(self):
        """Tests getting bearer token url"""
        request_header = Mock()
        request_header.headers = {'Www-Authenticate': '"service"="foo","Bearer realm"="baz","scope"="bar"'}  # noqa pylint: disable=line-too-long
        with patch.object(requests, "get",
                          return_value=request_header) as patch_get:
            url = self.docker_cls._get_bearer_token_url()
            assert url == "baz?service=foo&scope=bar"
            patch_get.assert_called_once_with(self.request_url)

    def test__get_bearer_token_get_token(self):
        """Tests getting bearer token successfully"""
        request_header = Mock()
        request_header.status_code = 200
        with patch.object(self.docker_cls, "_get_bearer_token_url",
                          return_value="testing") as patch_get_url,\
             patch.object(requests, "get",
                          return_value=request_header) as patch_get,\
             patch.object(request_header, "json",
                          return_value={"token": self.token}) as patch_json:
            token = self.docker_cls._get_bearer_token(username=self.username,
                                                      password=self.password)
            assert token == self.token
            patch_get_url.assert_called_once()
            patch_get.assert_called_once_with(
                "testing",
                headers={'Authorization': 'Basic bXl1c2VyOm15cGFzc3dvcmQ='}
            )
            patch_json.assert_called_once()

    def test__get_bearer_token_raise_error(self):
        """Tests getting bearer token successfully"""
        request_header = Mock()
        request_header.status_code = 400

        with patch.object(self.docker_cls, "_get_bearer_token_url"),\
             patch.object(requests, "get", return_value=request_header),\
             patch.object(request_header, "json",
                          return_value={"details": "errorme"}),\
             pytest.raises(ValueError, match="errorme"):
            self.docker_cls._get_bearer_token(username=self.username,
                                              password=self.password)

    def test_get(self):
        """Testings getting docker repository"""
        request = Mock()
        with patch.object(self.docker_cls, "_get_bearer_token",
                          return_value=self.token) as patch_get_token,\
             patch.object(requests, "get", return_value=request) as patch_get:
            resp = self.docker_cls.get(username=self.username,
                                       password=self.password)
            assert resp == request
            patch_get_token.assert_called_once_with(username=self.username,
                                                    password=self.password)
            patch_get.assert_called_once_with(self.request_url,
                                              headers=self.auth_headers)

    def test_validate_docker(self):
        """Tests validate docker class"""
        response = Mock()
        with patch.object(dockertools, 'DockerRepository',
                          return_value=self.docker_cls) as patch_cls,\
             patch.object(self.docker_cls, "get",
                          return_value=response) as patch_resp,\
             patch.object(dockertools,
                          "check_docker_exists") as patch_exists,\
             patch.object(dockertools, "check_docker_size") as patch_size:
            valid = dockertools.validate_docker(
                docker_repo="testme",
                docker_digest="willthiswork",
                index_endpoint=ENDPOINT_MAPPING["synapse"],
                username=self.username,
                password=self.password
            )
            assert valid
            patch_cls.assert_called_once_with(
                docker_repo="testme",
                docker_digest="willthiswork",
                index_endpoint=ENDPOINT_MAPPING["synapse"]
            )
            patch_resp.assert_called_once_with(username=self.username,
                                               password=self.password)
            patch_exists.assert_called_once_with(response)
            patch_size.assert_called_once_with(response)


def test_check_docker_exists_noerror():
    """Checks that the docker image exists"""
    response = Mock()
    response.status_code = 200
    dockertools.check_docker_exists(response)


def test_check_docker_exists_error():
    """Checks that the docker image exists"""
    response = Mock()
    response.status_code = 300
    with pytest.raises(ValueError,
                       match="Docker image and sha digest must exist."):
        dockertools.check_docker_exists(response)


def test_check_docker_size_noerror():
    """Checks that the docker image size is less than 1TB"""
    response = Mock()
    layer_dict = [{'size': 10000}, {'size': 200000}]
    with patch.object(response, "json", return_value={'layers': layer_dict}):
        dockertools.check_docker_size(response)


def test_check_docker_size_toobig():
    """Checks that if docker image is more than 1TB an error is thrown"""
    response = Mock()
    layer_dict = [{'size': 1000000000*1000}, {'size': 1000000000}]
    with patch.object(response, "json", return_value={'layers': layer_dict}),\
         pytest.raises(ValueError,
                       match="Docker image must be less than a terabyte."):
        dockertools.check_docker_size(response)
