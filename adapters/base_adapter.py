from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict

class SecurityToolAdapter(ABC):
    name = "base"

    @abstractmethod
    def scan_input(self, payload: Dict[str, Any]) -> Dict[str, Any]: ...

    @abstractmethod
    def scan_output(self, payload: Dict[str, Any]) -> Dict[str, Any]: ...

    @abstractmethod
    def validate_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]: ...

    def run_benchmark_case(self, case: Dict[str, Any]) -> Dict[str, Any]:
        return self.validate_tool_call({"case": case})
