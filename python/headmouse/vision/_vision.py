

class Vision(object):
    def __init__(self, camera, config):
        self.config = config
        self.camera = camera
        self.frame = None
        self.x = None
        self.y = None
        self.z = None
        self.visualization_data = None

    def __enter__(self):
        self.camera.__enter__()
        return self

    def __exit__(self, *args):
        self.camera.__exit__(*args)

    def get_image(self):
        self.frame = self.camera.get_image()
        return self.frame

    def display_image(self):
        raise NotImplementedError

    def process(self):
        raise NotImplementedError