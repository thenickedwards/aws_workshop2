"""
This program is used to autograde the DevOps workshop assignments
"""
import os
import http.client
import json
import uuid
import sys
import socket

from urllib.parse import urlparse

class Grader():
    """
    This class opens the correct transport for web communication based on selected protocol 
        and provides a GET and POST method to the tutorials endpoint
    """

    def __init__(self, protocol, host, port):
        if protocol == "https":
            self.conn = http.client.HTTPSConnection(f"{host}:{port}",timeout=3)
        else:
            self.conn = http.client.HTTPConnection(f"{host}:{port}",timeout=3)
        self.headers = {
            "Host": f"{host}:{port}",
            "Accept": "application/json",
            "Content-type": "application/json"
            }

    def get_tutorial(self,object_id):
        """
        This method does a GET request on the tutorials endpoint
        """
        self.conn.request("GET", f"/api/tutorials/{object_id}/", headers=self.headers)
        return self.conn.getresponse().read().decode()
    def post_tutorial(self,payload):
        """
        This method does a POST request on the tutorials endpoint
        """
        self.conn.request("POST", "/api/tutorials/", payload, headers=self.headers)
        return self.conn.getresponse()

if __name__ == '__main__':

    KEY = uuid.uuid4().hex
    ERROR = None
    STATUS_CODE = 0
    RESPONSE = None
    BODY = json.loads('{"POST": false}')
    TUTORIAL = json.loads('{"GET": false}')
    FILENAME = "results.json"
    USERNAME = os.getlogin()

    print("#" * 55)
    print("Welcome to the Nucamp auto-grader for DevOps!")
    print(" * User input required to continue")
    print(" * Default values are shown in brackets []")
    print("   ** Press 'enter' to accept default value **")
    print("#" * 55)
    print("")
    selected_name = input(f"Enter your name [{USERNAME}]: ") or USERNAME
    if not selected_name:
        print("\nPlease provide a valid name!")
        sys.exit(1)
    selected_workshop = input("Enter workshop week [1]: ") or "1"
    if selected_workshop not in ("1","2","3","4"):
        print("\nPlease select a valid workshop!  1, 2, 3, or 4")
        sys.exit(1)
    selected_protocol = (input("Enter transport [http]: ") or "http").lower()
    if selected_protocol not in ("http", "https"):
        print("\nPlease select a valid protocol!  http or https")
        sys.exit(1)
    raw_host = (input("Enter host [127.0.0.1]: ") or "127.0.0.1").lower()
    parsed_host = urlparse(raw_host)
    if not parsed_host.netloc:
        parsed_host = urlparse(f"{selected_protocol}://{raw_host}")
    selected_host = parsed_host.hostname if parsed_host.netloc else None
    if not selected_host:
        print(f"\nPlease enter a valid host address! Unable to resolve '{raw_host}'")
        sys.exit(1)
    selected_port = (input("Enter port [8000]: ") or "8000").lower()
    if not selected_port.isdigit():
        print("\nPlease enter a valid port in numeric range 0-65535!")
        sys.exit(1)
    print("")

    title = f"Workshop autograded by {selected_name}"
    autograder = Grader(selected_protocol, selected_host, selected_port)
    autogenerated_payload = {
        "title": title,
        "tutorial_url" : f"http://www.{KEY}.com",
        "image_path": f"{KEY}.PNG",
        "description": f"A tutorial about {KEY}",
        "published": True
    }

    try:
        RESPONSE = autograder.post_tutorial(json.dumps(autogenerated_payload))
    except ConnectionRefusedError as e:
        ERROR = str(e)
    except TimeoutError as e:
        ERROR = str(e)
    except socket.gaierror as e:
        ERROR = str(e)
    if RESPONSE:
        STATUS_CODE = RESPONSE.status
        if STATUS_CODE in (200,201):
            BODY = json.loads(RESPONSE.read().decode())
            TUTORIAL = json.loads(autograder.get_tutorial(BODY.get("id")))
        else:
            ERROR = f"Invalid HTTP status code returned: {STATUS_CODE}"

    grading_object = {
        "STUDENT": selected_name,
        "KEY": KEY,
        "HOST": f"{selected_protocol}://{selected_host}:{selected_port}",
        "WORKSHOP": selected_workshop,
        "POST_PAYLOAD": BODY,
        "POST_HASH": hash(tuple(BODY)),
        "GET_PAYLOAD": TUTORIAL,
        "GET_HASH": hash(tuple(TUTORIAL)),
        "RESPONSE_CODE": STATUS_CODE,
        "ERROR": ERROR
    }

    with open(FILENAME,"w+", encoding="utf-8") as fh:
        fh.write(json.dumps(grading_object))
    print("#" * 55)
    print("The autograder has completed grading your assignment!")
    print(f" * Outfile location: {os.path.join(os.getcwd(),FILENAME)}" )
    if ERROR:
        print(" ** Issue detected **")
        print(f"    - {ERROR}")
        print(" * Your grade could be impacted if error is not corrected.")
    else:
        print(" ** No issue detected **")
    print("#" * 55)
    print("")
