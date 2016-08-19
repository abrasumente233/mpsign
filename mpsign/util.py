import http.server
import threading

# Make a decision between several packages
# Which priority is up to the sort of the given packages
def select_package(packages):
    for package in packages:
        try:
            __import__(package)
            return package
        except:
            # No matter whatever the error is
            pass

    return None  # No avilable package detected

# Single file server

def log_message(self, log_format, *args):
    """Do not log any message to the console"""
    pass

def get(filename):
    def do_GET(self):
        """Serve a GET request."""
        f = open(filename, 'rb')
        self.send_response(200)
        self.send_header("Content-type", 'image/gif')
        fs = os.fstat(f.fileno())
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        self.copyfile(f, self.wfile)
        f.close()
    return do_GET

def single_file_server(filename):
    return type('SingleFileServer', (http.server.SimpleHTTPRequestHandler,),
                dict(log_message=log_message, do_GET=get(filename)))

class SingleFileHTTPThread(threading.Thread):
    def __init__(self, port, file_path):
        super().__init__()
        self.file_path = file_path
        self.port = port
        self.httpd = None

    def run(self):
        self.httpd = http.server.HTTPServer(('', self.port), single_file_server(self.file_path))
        self.httpd.serve_forever()

# Single file server
