#!/usr/bin/env python3
"""
Example usage of OpenCode Controller
"""

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from opencode_controller import OpenCodeController, quick_task


def example_basic_usage():
    """Example 1: Basic usage with automatic cleanup"""
    print("Example 1: Basic Usage")
    print("-" * 40)
    
    with OpenCodeController(working_dir=r"D:\mojing") as ctrl:
        # Create session
        session = ctrl.create_session(title="Fix authentication bug")
        print(f"Session created: {session['id']}")
        
        # Send task
        ctrl.send_async(
            session["id"],
            "Check the auth.ts file for JWT validation issues and fix them"
        )
        
        # Wait for result
        result = ctrl.wait_for_completion(session["id"], timeout=300)
        print(f"Result:\n{result}")
        
        # Cleanup
        ctrl.delete_session(session["id"])


def example_quick_task():
    """Example 2: Quick one-liner"""
    print("\nExample 2: Quick Task")
    print("-" * 40)
    
    result = quick_task(
        message="Generate a README.md for a Python project",
        working_dir=r"D:\mojing",
        timeout=120
    )
    print(f"Result:\n{result}")


def example_batch_tasks():
    """Example 3: Batch multiple tasks"""
    print("\nExample 3: Batch Tasks")
    print("-" * 40)
    
    tasks = [
        "Add type hints to utils.py",
        "Write docstrings for main functions",
        "Refactor error handling"
    ]
    
    with OpenCodeController(working_dir=r"D:\mojing") as ctrl:
        sessions = []
        
        # Launch all tasks
        for task in tasks:
            session = ctrl.create_session(title=task[:30])
            ctrl.send_async(session["id"], task)
            sessions.append((task, session["id"]))
            print(f"Launched: {task[:40]}... (session: {session['id'][:8]}...)")
        
        # Wait for all to complete
        print("\nWaiting for completion...")
        for task, session_id in sessions:
            try:
                result = ctrl.wait_for_completion(session_id, timeout=300)
                print(f"✓ {task[:40]}... completed")
            except TimeoutError:
                print(f"✗ {task[:40]}... timed out")
            finally:
                ctrl.delete_session(session_id)


def example_monitor_progress():
    """Example 4: Monitor progress interactively"""
    print("\nExample 4: Monitor Progress")
    print("-" * 40)
    
    import time
    
    with OpenCodeController(working_dir=r"D:\mojing") as ctrl:
        session = ctrl.create_session(title="Build new feature")
        ctrl.send_message(
            session["id"],
            "Create a simple REST API with Flask that has /health and /users endpoints"
        )
        
        # Monitor progress
        while True:
            status = ctrl.get_session_status(session["id"])
            messages = ctrl.get_messages(session["id"], limit=3)
            
            # Show latest activity
            if messages:
                latest = messages[-1]
                role = latest.get("role", "unknown")
                content = latest.get("parts", [{}])[0].get("text", "")[:80]
                print(f"[{status['status']}] {role}: {content}...")
            
            if status["status"] == "idle":
                print("\nTask completed!")
                break
                
            time.sleep(3)
        
        # Show final diff
        diffs = ctrl.get_diff(session["id"])
        if diffs:
            print(f"\nFiles modified: {len(diffs)}")
            for diff in diffs:
                print(f"  - {diff.get('path', 'unknown')}")
        
        ctrl.delete_session(session["id"])


def example_with_agent():
    """Example 5: Use specific agent (Plan mode)"""
    print("\nExample 5: Plan Mode")
    print("-" * 40)
    
    with OpenCodeController(working_dir=r"D:\mojing") as ctrl:
        session = ctrl.create_session(title="Architecture review")
        
        # Use 'plan' agent for read-only analysis
        result = ctrl.send_message(
            session["id"],
            "Analyze the current codebase architecture and suggest improvements",
            agent="plan"
        )
        
        print(f"Analysis:\n{result}")
        ctrl.delete_session(session["id"])


if __name__ == "__main__":
    import os
    
    print("OpenCode Controller Examples")
    print("=" * 50)
    
    # Run examples (comment out ones you don't want to run)
    try:
        # example_basic_usage()
        # example_quick_task()
        # example_batch_tasks()
        # example_monitor_progress()
        # example_with_agent()
        
        print("\nUncomment the example functions you want to run")
        print("Make sure OpenCode is installed: npm install -g opencode-ai")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
