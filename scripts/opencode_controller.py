#!/usr/bin/env python3
"""
OpenCode Controller - HTTP Server API Client

Provides programmatic control of OpenCode via its HTTP Server API.
"""

import requests
import time
import subprocess
import os
import sys
import signal
from typing import Optional, Dict, List, Any
from urllib.parse import urljoin


class OpenCodeError(Exception):
    """Base exception for OpenCode controller errors."""
    pass


class ServerNotRunningError(OpenCodeError):
    """Raised when OpenCode server is not running and auto-start fails."""
    pass


class OpenCodeAPIError(OpenCodeError):
    """Raised when OpenCode API returns an error."""
    def __init__(self, message: str, status_code: int = None, response: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class OpenCodeController:
    """
    Controller for OpenCode HTTP Server API.
    
    Automatically manages server lifecycle and provides simple interface
    for creating sessions, sending messages, and retrieving results.
    """
    
    def __init__(
        self,
        port: int = 4096,
        host: str = "127.0.0.1",
        working_dir: str = r"D:\mojing",
        auto_start: bool = True,
        server_timeout: int = 30
    ):
        """
        Initialize OpenCode controller.
        
        Args:
            port: Server port (default: 4096)
            host: Server host (default: 127.0.0.1)
            working_dir: Default working directory for sessions
            auto_start: Automatically start server if not running
            server_timeout: Seconds to wait for server startup
        """
        self.port = port
        self.host = host
        self.working_dir = working_dir
        self.auto_start = auto_start
        self.server_timeout = server_timeout
        self.base_url = f"http://{host}:{port}"
        self._server_process: Optional[subprocess.Popen] = None
        
        # Ensure working directory exists
        os.makedirs(working_dir, exist_ok=True)
        
        # Auto-start server if needed
        if auto_start and not self.is_server_running():
            self.start_server()
    
    def _api_url(self, path: str) -> str:
        """Build full API URL."""
        return urljoin(self.base_url + "/", path.lstrip("/"))
    
    def is_server_running(self) -> bool:
        """Check if OpenCode server is running."""
        try:
            response = requests.get(
                self._api_url("/global/health"),
                timeout=2
            )
            return response.status_code == 200
        except requests.exceptions.ConnectionError:
            return False
        except requests.exceptions.Timeout:
            return False
    
    def start_server(self) -> bool:
        """
        Start OpenCode server.
        
        Returns:
            True if server started successfully
            
        Raises:
            ServerNotRunningError: If server fails to start
        """
        if self.is_server_running():
            print("OpenCode server is already running")
            return True
        
        print(f"Starting OpenCode server on {self.host}:{self.port}...")
        
        try:
            # Start opencode serve in background
            # Using CREATE_NEW_PROCESS_GROUP on Windows for clean termination
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
            
            self._server_process = subprocess.Popen(
                ["opencode", "serve", "--port", str(self.port), "--hostname", self.host],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creationflags,
                cwd=self.working_dir
            )
            
            # Wait for server to be ready
            start_time = time.time()
            while time.time() - start_time < self.server_timeout:
                if self.is_server_running():
                    print(f"✓ OpenCode server started at {self.base_url}")
                    return True
                time.sleep(0.5)
            
            # Timeout - check if process is still running
            if self._server_process.poll() is not None:
                stdout, stderr = self._server_process.communicate()
                raise ServerNotRunningError(
                    f"Server process exited early.\nstdout: {stdout.decode()}\nstderr: {stderr.decode()}"
                )
            else:
                raise ServerNotRunningError("Server failed to respond within timeout period")
                
        except FileNotFoundError:
            raise ServerNotRunningError(
                "OpenCode not found. Please install OpenCode: npm install -g opencode-ai"
            )
        except Exception as e:
            raise ServerNotRunningError(f"Failed to start server: {e}")
    
    def stop_server(self) -> bool:
        """Stop the OpenCode server if we started it."""
        if self._server_process and self._server_process.poll() is None:
            if sys.platform == 'win32':
                # On Windows, send CTRL_BREAK_EVENT to process group
                self._server_process.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                self._server_process.terminate()
            
            try:
                self._server_process.wait(timeout=5)
                return True
            except subprocess.TimeoutExpired:
                self._server_process.kill()
                return True
        return False
    
    def _request(
        self,
        method: str,
        path: str,
        json_data: Dict = None,
        params: Dict = None,
        timeout: int = 30
    ) -> Any:
        """Make HTTP request to OpenCode API."""
        url = self._api_url(path)
        
        try:
            response = requests.request(
                method=method,
                url=url,
                json=json_data,
                params=params,
                timeout=timeout
            )
            
            if response.status_code == 204:
                return None
            
            if not response.ok:
                raise OpenCodeAPIError(
                    f"API error: {response.status_code} - {response.text}",
                    status_code=response.status_code,
                    response=response.text
                )
            
            return response.json() if response.text else None
            
        except requests.exceptions.ConnectionError:
            if self.auto_start and not self.is_server_running():
                self.start_server()
                # Retry once
                return self._request(method, path, json_data, params, timeout)
            raise OpenCodeError("Cannot connect to OpenCode server")
    
    def create_session(
        self,
        title: Optional[str] = None,
        parent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new OpenCode session.
        
        Args:
            title: Session title
            parent_id: Parent session ID for forked sessions
            
        Returns:
            Session info dict with 'id' key
        """
        data = {}
        if title:
            data["title"] = title
        if parent_id:
            data["parentID"] = parent_id
            
        return self._request("POST", "/session", json_data=data)
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions."""
        return self._request("GET", "/session") or []
    
    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session details."""
        return self._request("GET", f"/session/{session_id}")
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        result = self._request("DELETE", f"/session/{session_id}")
        return result if isinstance(result, bool) else True
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get session status."""
        all_status = self._request("GET", "/session/status") or {}
        return all_status.get(session_id, {"status": "unknown"})
    
    def abort_session(self, session_id: str) -> bool:
        """Abort a running session."""
        result = self._request("POST", f"/session/{session_id}/abort")
        return result if isinstance(result, bool) else True
    
    def send_message(
        self,
        session_id: str,
        message: str,
        agent: Optional[str] = None,
        model: Optional[str] = None,
        no_reply: bool = False
    ) -> Dict[str, Any]:
        """
        Send a message to a session and wait for response.
        
        Args:
            session_id: Target session ID
            message: Message content
            agent: Agent to use (e.g., 'build', 'plan')
            model: Model to use (e.g., 'kimi-for-coding/k2p5')
            no_reply: If True, don't wait for response
            
        Returns:
            Message response info
        """
        data = {
            "parts": [{"type": "text", "text": message}]
        }
        if agent:
            data["agent"] = agent
        if model:
            data["model"] = model
        if no_reply:
            data["noReply"] = True
            
        return self._request(
            "POST",
            f"/session/{session_id}/message",
            json_data=data,
            timeout=120  # Longer timeout for actual work
        )
    
    def send_async(self, session_id: str, message: str) -> None:
        """
        Send a message asynchronously (fire and forget).
        
        Args:
            session_id: Target session ID
            message: Message content
        """
        data = {
            "parts": [{"type": "text", "text": message}]
        }
        self._request(
            "POST",
            f"/session/{session_id}/prompt_async",
            json_data=data,
            timeout=5
        )
    
    def get_messages(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get messages from a session.
        
        Args:
            session_id: Session ID
            limit: Maximum number of messages
            
        Returns:
            List of message dicts
        """
        result = self._request(
            "GET",
            f"/session/{session_id}/message",
            params={"limit": limit}
        )
        return result if isinstance(result, list) else []
    
    def is_session_idle(self, session_id: str) -> bool:
        """Check if session is idle (not processing)."""
        status = self.get_session_status(session_id)
        return status.get("status") == "idle"
    
    def wait_for_completion(
        self,
        session_id: str,
        timeout: int = 300,
        poll_interval: float = 2.0
    ) -> str:
        """
        Wait for session to complete and return final output.
        
        Args:
            session_id: Session to monitor
            timeout: Maximum seconds to wait
            poll_interval: Seconds between status checks
            
        Returns:
            Final message content as string
            
        Raises:
            TimeoutError: If timeout is reached before completion
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_session_status(session_id)
            
            if status.get("status") == "idle":
                # Session completed, get last assistant message
                messages = self.get_messages(session_id, limit=10)
                for msg in reversed(messages):
                    if msg.get("role") == "assistant":
                        parts = msg.get("parts", [])
                        texts = [p.get("text", "") for p in parts if p.get("type") == "text"]
                        return "\n".join(texts)
                return ""
            
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Session {session_id} did not complete within {timeout} seconds")
    
    def get_diff(self, session_id: str, message_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get file diff for a session or specific message."""
        params = {}
        if message_id:
            params["messageID"] = message_id
        return self._request("GET", f"/session/{session_id}/diff", params=params) or []
    
    def share_session(self, session_id: str) -> Dict[str, Any]:
        """Share a session (creates shareable link)."""
        return self._request("POST", f"/session/{session_id}/share")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup server if we started it."""
        self.stop_server()


# Convenience functions for quick usage

def quick_task(
    message: str,
    working_dir: str = r"D:\mojing",
    timeout: int = 300,
    port: int = 4096
) -> str:
    """
    Quick one-liner to run a task through OpenCode.
    
    Args:
        message: The task description
        working_dir: Working directory
        timeout: Maximum wait time
        port: Server port
        
    Returns:
        Task result as string
    """
    with OpenCodeController(port=port, working_dir=working_dir) as ctrl:
        session = ctrl.create_session(title=message[:50])
        ctrl.send_async(session["id"], message)
        return ctrl.wait_for_completion(session["id"], timeout=timeout)


if __name__ == "__main__":
    # Example usage
    print("OpenCode Controller - Example Usage")
    print("=" * 50)
    
    # Initialize controller
    ctrl = OpenCodeController()
    
    # Create a session
    session = ctrl.create_session(title="Test task")
    print(f"Created session: {session['id']}")
    
    # Send a simple message
    print("Sending task...")
    ctrl.send_async(session["id"], "List all files in the current directory")
    
    # Wait for result
    print("Waiting for completion...")
    result = ctrl.wait_for_completion(session["id"], timeout=60)
    print(f"Result:\n{result}")
    
    # Cleanup
    ctrl.delete_session(session["id"])
    print("Session deleted")
