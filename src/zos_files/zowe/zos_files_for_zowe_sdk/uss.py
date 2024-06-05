"""Zowe Python Client SDK.

This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at

https://www.eclipse.org/legal/epl-v20.html

SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zowe Project.
"""

import os

from zowe.core_for_zowe_sdk import SdkApi
from zowe.core_for_zowe_sdk.exceptions import FileNotFound

_ZOWE_FILES_DEFAULT_ENCODING = "utf-8"

class USSFiles(SdkApi):
    """
    Class used to represent the base z/OSMF USSFiles API
    which includes all operations related to USS files.

    ...

    Attributes
    ----------
    connection
        connection object
    """

    def __init__(self, connection):
        """
        Construct a USSFiles object.

        Parameters
        ----------
        connection
            The z/OSMF connection object (generated by the ZoweSDK object)

        Also update header to accept gzip encoded responses
        """
        super().__init__(connection, "/zosmf/restfiles/", logger_name=__name__)
        self.default_headers["Accept-Encoding"] = "gzip"
    
    def list(self, path):
        """Retrieve a list of USS files based on a given pattern.

        Returns
        -------
        json
            A JSON with a list of dataset names matching the given pattern
        """
        custom_args = self._create_custom_request_arguments()
        custom_args["params"] = {"path": path}
        custom_args["url"] = "{}fs".format(self.request_endpoint)
        response_json = self.request_handler.perform_request("GET", custom_args)
        return response_json

    def delete(self, filepath_name, recursive=False):
        """
        Delete a file or directory

        Parameters
        ----------
        filepath of the file to be deleted

        recursive
            If specified as True, all the files and sub-directories will be deleted.

        Returns
        -------
        204
            HTTP Response for No Content
        """
        custom_args = self._create_custom_request_arguments()
        custom_args["url"] = "{}fs/{}".format(self.request_endpoint, filepath_name.lstrip("/"))
        if recursive:
            custom_args["headers"]["X-IBM-Option"] = "recursive"

        response_json = self.request_handler.perform_request("DELETE", custom_args, expected_code=[204])
        return response_json
    
    def create(self, file_path, type, mode=None):
        """
        Add a file or directory
        Parameters
        ----------
        file_path of the file to add
        type = "file" or "dir"
        mode Ex:- rwxr-xr-x

        """

        data = {"type": type, "mode": mode}

        custom_args = self._create_custom_request_arguments()
        custom_args["json"] = data
        custom_args["url"] = "{}fs/{}".format(self.request_endpoint, file_path.lstrip("/"))
        response_json = self.request_handler.perform_request("POST", custom_args, expected_code=[201])
        return response_json

    def write(self, filepath_name, data, encoding=_ZOWE_FILES_DEFAULT_ENCODING):
        """Write content to an existing UNIX file.
        Returns
        -------
        json
            A JSON containing the result of the operation
        """
        custom_args = self._create_custom_request_arguments()
        custom_args["url"] = "{}fs/{}".format(self.request_endpoint, filepath_name.lstrip("/"))
        custom_args["data"] = data
        custom_args["headers"]["Content-Type"] = "text/plain; charset={}".format(encoding)
        response_json = self.request_handler.perform_request("PUT", custom_args, expected_code=[204, 201])
        return response_json
    
    def get_content(self, filepath_name):
        """Retrieve the content of a filename. The complete path must be specified.

        Returns
        -------
        json
            A JSON with the contents of the specified USS file
        """
        custom_args = self._create_custom_request_arguments()
        # custom_args["params"] = {"filepath-name": filepath_name}
        custom_args["url"] = "{}fs{}".format(self.request_endpoint, filepath_name)
        response_json = self.request_handler.perform_request("GET", custom_args)
        return response_json
    
    def get_content_streamed(self, file_path, binary=False):
        """Retrieve the contents of a given USS file streamed.

        Returns
        -------
        response
            A response object from the requests library
        """
        custom_args = self._create_custom_request_arguments()
        custom_args["url"] = "{}fs/{}".format(self.request_endpoint, self._encode_uri_component(file_path.lstrip("/")))
        if binary:
            custom_args["headers"]["X-IBM-Data-Type"] = "binary"
        response = self.request_handler.perform_request("GET", custom_args, stream=True)
        return response

    def download(self, file_path, output_file, binary=False):
        """Retrieve the contents of a USS file and saves it to a local file."""
        response = self.get_content_streamed(file_path, binary)
        with open(output_file, "wb" if binary else "w", encoding="utf-8") as f:
            for chunk in response.iter_content(chunk_size=4096, decode_unicode=not binary):
                f.write(chunk)

    def upload(self, input_file, filepath_name, encoding=_ZOWE_FILES_DEFAULT_ENCODING):
        """Upload contents of a given file and uploads it to UNIX file"""
        if os.path.isfile(input_file):
            with open(input_file, "r", encoding="utf-8") as in_file:
                response_json = self.write(filepath_name, in_file.read())
        else:
            self.logger.error(f"File {input_file} not found.")
            raise FileNotFound(input_file)