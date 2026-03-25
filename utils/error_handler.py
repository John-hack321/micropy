from dataclasses import dataclass, field
from typing import List

#  our error class
@dataclass
class CompileError:
    phase:   str   # tracks which phase of the compilation phases the error was caught at , eg lexer phase
    message: str   # tracks what went wrong
    line:    int   # trachs which line in the source code the error occured at


# The error handler
class ErrorHandler:
    def __init__(self):
        self.errors: List[CompileError] = []

    def report(self, phase: str, message: str, line: int):
        """
        records an error and still allows execution of the code to continue
        """
        error = CompileError(phase=phase, message=message, line=line)
        self.errors.append(error)
        # in our compiler we print the error immediately so that it is seen as it happens
        print(f"  [{phase} Error] Line {line}: {message}")

    def has_errors(self) -> bool:
        # checks if any errors were recorded and returns true is so
        return len(self.errors) > 0

    def summary(self):
        """Print a final summary of all errors found"""
        if not self.errors:
            print("\n success . No errors found.")
        else:
            print(f"\n {len(self.errors)} error(s) found:")
            for err in self.errors:
                print(f"  Line {err.line} [{err.phase}]: {err.message}")