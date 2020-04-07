'''
Test challengeutils.discussion functions
'''
import uuid

from mock import Mock, patch
import pytest
import requests
import synapseclient

from challengeutils.dockertools import (DockerRepository,
                                        ENDPOINT_MAPPING)


class TestDockerRepository:

    def setup(self):
        self.DOCKER_CLS = DockerRepository(docker_repo="testme",
                                           docker_digest="willthiswork",
                                           index_endpoint=ENDPOINT_MAPPING["synapse"])
        self.username = "myuser"
        self.password = "mypassword"

    def test_string_representation(self):
        """Tests string representation of docker repo"""
        assert str(self.DOCKER_CLS) == "testme@willthiswork"

    def test_get_request_url(self):
        url = self.DOCKER_CLS.get_request_url()
        assert url == "https://docker.synapse.org/v2/testme/manifests/willthiswork"
    
    def test__get_bearer_token_url(self):
        """Tests getting bearer token url"""
        request_header = Mock()
        request_header.headers = {'Www-Authenticate': '"service"="foo","Bearer realm"="baz","scope"="bar"'}
        with patch.object(self.DOCKER_CLS, "get_request_url",
                          return_value="funfunfun"),\
             patch.object(requests, "get",
                          return_value=request_header) as patch_get:
            url = self.DOCKER_CLS._get_bearer_token_url()
            assert url == "baz?service=foo&scope=bar"
            patch_get.assert_called_once_with("funfunfun")

    def test__get_bearer_token_get_token(self):
        """Tests getting bearer token successfully"""
        request_header = Mock()
        request_header.status_code = 200
        expect_token = str(uuid.uuid1())
        with patch.object(self.DOCKER_CLS, "_get_bearer_token_url",
                          return_value="testing") as patch_get_url,\
             patch.object(requests, "get",
                          return_value=request_header) as patch_get,\
             patch.object(request_header, "json",
                          return_value={"token": expect_token}) as patch_json:
            token = self.DOCKER_CLS._get_bearer_token(username=self.username,
                                                      password=self.password)
            assert token == expect_token
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

        with patch.object(self.DOCKER_CLS, "_get_bearer_token_url"),\
             patch.object(requests, "get",
                          return_value=request_header) as patch_get,\
             patch.object(request_header, "json",
                          return_value={"details": "errorme"}) as patch_json,\
             pytest.raises(ValueError, match="errorme"):
            self.DOCKER_CLS._get_bearer_token(username=self.username,
                                              password=self.password)
