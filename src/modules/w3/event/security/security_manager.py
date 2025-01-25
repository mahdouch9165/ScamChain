from .security_checks import *

class SecurityManager:
    def __init__(self, event):
        self.event = event
        # make an automatic list of checks
        self.checks = Checks.__subclasses__()

    def check(self):
        flagged = False
        for check in self.checks:
            check_instance = check(self.event)
            flagged = check_instance.check()
            if flagged:
                flagged = True
                return flagged
        return flagged