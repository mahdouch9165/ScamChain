import logging

class Checks:
    def __init__(self, event):
        raise NotImplementedError
    
    def check(self):
        raise NotImplementedError

class SecurityFunctionPresence(Checks):
    def __init__(self, event):
        self.event = event
        # Get contract code
        self.contract_code = event.token.code
        self.functions = event.token.functions
        self.bad_functions = []
        self.warning_functions = []
        self.function_combos = []
    def check(self):
        for warning_function in self.warning_functions:
            if warning_function in self.functions:
                self.event.logger.warning(
                    f"{warning_function} found in contract ({self.event.token.address})"
                )
                self.event.bad_functions.append(warning_function)

        for bad_function in self.bad_functions:
            if bad_function in self.functions:
                self.event.logger.warning(
                    f"{bad_function} found in contract ({self.event.token.address})"
                )
                self.event.bad_functions.append(bad_function)
                return True
            
        for combo in self.function_combos:
            if all([f in self.functions for f in combo]):
                self.event.logger.error(
                    f"Function combination {combo} found in contract ({self.event.token.address})"
                )
                self.event.bad_functions += combo
                return True
        return False

class SecurityBadLines(Checks):
    def __init__(self, event):
        self.event = event
        # Get contract code
        self.contract_code = event.token.code
        self.warning_lines = []
        self.bad_lines = []

    def check(self):
        for line in self.warning_lines:
            if line in self.contract_code:
                self.event.logger.warning(
                    f"{line} found in contract ({self.event.token.address})"
                )
                self.event.bad_lines.append(line)
        
        for line in self.bad_lines:
            if line in self.contract_code:
                self.event.logger.error(
                    f"{line} found in contract ({self.event.token.address})"
                )
                self.event.bad_lines.append(line)
                return True
        return False
