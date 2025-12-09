"""
RF Spectrum Automation Rule Intent Classification System
Multi-agent workflow with ChatOllama for intelligent intent routing
Handles: CREATE, UPDATE, INFO, and GENERIC RF queries
"""

from langgraph.graph import StateGraph, END
#from langchain_community.chat_models import ChatOllama
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
import operator
import json
from typing import TypedDict, Annotated, Literal, List, Dict, Any, Optional
import uuid
from datetime import datetime
import re
# ============================================================================
# MOCK TOOL IMPLEMENTATIONS (Replace with actual database queries)
# ============================================================================

# Mock database
MOCK_DATABASE = {
    "rules": [
        {
            "id": "rule-001",
            "name": "5G Monitor",
            "description": "Monitors 5G signals in mid-band",
            "isEnabled": True,
            "createdAt": "2024-01-15T10:30:00Z"
        },
        {
            "id": "rule-002",
            "name": "LTE Detector",
            "description": "Detects LTE signals",
            "isEnabled": True,
            "createdAt": "2024-01-20T14:00:00Z"
        },
        {
            "id": "rule-003",
            "name": "Energy Threshold Alert",
            "description": "Alerts when energy exceeds threshold",
            "isEnabled": False,
            "createdAt": "2024-02-01T09:00:00Z"
        }
    ],
    "conditions": {
        "rule-001": [
            {
                "id": "cond-001",
                "rule_id": "rule-001",
                "conditionType": "signalDetection",
                "parameters": {
                    "minFrequencyMHz": 3400,
                    "maxFrequencyMHz": 3600,
                    "signalType": "5G"
                }
            }
        ],
        "rule-002": [
            {
                "id": "cond-002",
                "rule_id": "rule-002",
                "conditionType": "signalDetection",
                "parameters": {
                    "minFrequencyMHz": 1800,
                    "maxFrequencyMHz": 2100,
                    "signalType": "LTE"
                }
            }
        ],
        "rule-003": [
            {
                "id": "cond-003",
                "rule_id": "rule-003",
                "conditionType": "spectralEnergy",
                "parameters": {
                    "minFrequencyMHz": 2400,
                    "maxFrequencyMHz": 2500,
                    "threshold_dBm": -70
                }
            }
        ]
    },
    "actions": {
        "rule-001": [
            {
                "id": "act-001",
                "rule_id": "rule-001",
                "actionType": "userNotification",
                "parameters": {
                    "message": "5G signal detected in mid-band"
                }
            }
        ],
        "rule-002": [
            {
                "id": "act-002",
                "rule_id": "rule-002",
                "actionType": "frequencyScanRequest",
                "parameters": {
                    "sensorIds": ["sensor-01", "sensor-02"]
                }
            }
        ],
        "rule-003": [
            {
                "id": "act-003",
                "rule_id": "rule-003",
                "actionType": "geolocationRequest",
                "parameters": {
                    "algorithm": "TDOA",
                    "sensorIds": ["sensor-01", "sensor-02", "sensor-03"]
                }
            }
        ]
    }
}

def list_automation_rules() -> List[Dict[str, Any]]:
    """Tool: List all automation rules"""
    print("  🔧 Tool Called: list_automation_rules()")
    return MOCK_DATABASE["rules"]

def get_automation_rule(rule_id: str) -> Dict[str, Any]:
    """Tool: Get specific rule by ID"""
    print(f"  🔧 Tool Called: get_automation_rule(rule_id='{rule_id}')")
    for rule in MOCK_DATABASE["rules"]:
        if rule["id"] == rule_id:
            return rule
    return {"error": f"Rule with id '{rule_id}' not found"}

def list_conditions_for_rule(rule_id: str) -> List[Dict[str, Any]]:
    """Tool: List conditions for a specific rule"""
    print(f"  🔧 Tool Called: list_conditions_for_rule(rule_id='{rule_id}')")
    return MOCK_DATABASE["conditions"].get(rule_id, [])

def list_actions_for_rule(rule_id: str) -> List[Dict[str, Any]]:
    """Tool: List actions for a specific rule"""
    print(f"  🔧 Tool Called: list_actions_for_rule(rule_id='{rule_id}')")
    return MOCK_DATABASE["actions"].get(rule_id, [])


def create_automation_rule(
    name: str,
    description: str,
    is_enabled: bool = False,
    max_executions: Optional[int] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> dict:
    """
    Create a new EMS automation rule. Call this function to only create a new rule
    DO NOT call when create conditions
    DO NOT call when create actions
    DO NOT call when delete or deactivate automation rule
    IMPORTANT: Create rules with is_enabled=False initially.

    Args:
        name: Clear, descriptive name for the rule (e.g., "High Power Alert")
        description: Detailed explanation of what the rule does and why
        is_enabled: Whether rule is active immediately (default: False, recommended)
        max_executions: Optional limit on how many times rule can trigger
        start_time: ISO format datetime when rule becomes active
        end_time: ISO format datetime when rule becomes inactive

    Returns:
        The created automation rule with assigned ID
    """
    print(f"  🔧 Tool Called: create_automation_rule(name='{name}')")

    # Validate inputs
    if not name or not name.strip():
        return {"error": "Rule name cannot be empty"}

    if start_time and end_time:
        try:
            start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            if start >= end:
                return {"error": "start_time must be before end_time"}
        except ValueError as e:
            return {"error": f"Invalid datetime format: {str(e)}"}

    # Create the rule
    new_rule = {
        "id": str(uuid.uuid4()),
        "name": name,
        "description": description,
        "isEnabled": is_enabled,
        "createdAt": datetime.utcnow().isoformat() + "Z",
        "updatedAt": datetime.utcnow().isoformat() + "Z"
    }

    if max_executions is not None:
        new_rule["maxExecutions"] = max_executions
        new_rule["executionsRemaining"] = max_executions

    if start_time:
        new_rule["startTime"] = start_time

    if end_time:
        new_rule["endTime"] = end_time

    # Add to mock database
    MOCK_DATABASE["rules"].append(new_rule)

    print(f"  ✓ Created rule with ID: {new_rule['id']}")
    return new_rule


def create_condition(
    rule_id: str,
    condition_type: str,
    parameters: dict,
    description: Optional[str] = None
) -> dict:
    """
    This is a tool to create a new condition for a rule.

    Args:
        rule_id: UUID of the rule this condition belongs to
        condition_type: "signalDetection" or "spectralEnergy"
        parameters: Dictionary with condition-specific parameters
        description: Optional human-readable explanation

    Returns:
        Confirmation with created condition ID
    """
    print(f"  🔧 Tool Called: create_condition(rule_id='{rule_id}', type='{condition_type}')")

    # Validate rule exists
    rule_exists = any(r["id"] == rule_id for r in MOCK_DATABASE["rules"])
    if not rule_exists:
        return {"error": f"Rule with ID '{rule_id}' not found. Create the rule first."}

    # Validate condition type
    valid_types = ["signalDetection", "spectralEnergy"]
    if condition_type not in valid_types:
        return {"error": f"Invalid condition_type. Must be one of: {valid_types}"}

    # Validate parameters based on condition type
    if condition_type == "signalDetection":
        required_params = ["minFrequencyMHz", "maxFrequencyMHz", "signalType"]
        for param in required_params:
            if param not in parameters:
                return {"error": f"Missing required parameter: {param}"}

        # Validate frequency range
        min_freq = parameters.get("minFrequencyMHz")
        max_freq = parameters.get("maxFrequencyMHz")
        if not (10 <= min_freq <= 6000 and 10 <= max_freq <= 6000):
            return {"error": "Frequencies must be between 10 and 6000 MHz"}
        if min_freq >= max_freq:
            return {"error": "minFrequencyMHz must be less than maxFrequencyMHz"}

        # Validate signal type
        valid_signals = ["Energy", "5G", "LTE", "QPSK", "CW", "PCMPM", "CPM", "CPMFM", "BPSK", "SOQPSK"]
        if parameters.get("signalType") not in valid_signals:
            return {"error": f"Invalid signalType. Must be one of: {valid_signals}"}

    elif condition_type == "spectralEnergy":
        required_params = ["minFrequencyMHz", "maxFrequencyMHz", "threshold_dBm"]
        for param in required_params:
            if param not in parameters:
                return {"error": f"Missing required parameter: {param}"}

        # Validate frequency range
        min_freq = parameters.get("minFrequencyMHz")
        max_freq = parameters.get("maxFrequencyMHz")
        if not (10 <= min_freq <= 6000 and 10 <= max_freq <= 6000):
            return {"error": "Frequencies must be between 10 and 6000 MHz"}
        if min_freq >= max_freq:
            return {"error": "minFrequencyMHz must be less than maxFrequencyMHz"}

        # Validate threshold
        threshold = parameters.get("threshold_dBm")
        if not (-150 <= threshold <= 150):
            return {"error": "threshold_dBm must be between -150 and 150"}

    # Create the condition
    new_condition = {
        "id": str(uuid.uuid4()),
        "rule_id": rule_id,
        "conditionType": condition_type,
        "parameters": parameters,
        "description": description,
        "isSatisfied": False,
        "createdAt": datetime.utcnow().timestamp(),
        "updatedAt": datetime.utcnow().timestamp()
    }

    # Add to mock database
    MOCK_DATABASE["conditions"].append(new_condition)

    print(f"  ✓ Created condition with ID: {new_condition['id']}")
    return new_condition


def create_action(
    rule_id: str,
    action_type: str,
    parameters: dict,
    description: Optional[str] = None
) -> dict:
    """
    Create a new action for an automation rule.
    Actions define what happens when ALL conditions are satisfied.

    Args:
        rule_id: UUID of the rule this action belongs to
        action_type: "frequencyScanRequest", "geolocationRequest", or "userNotification"
        parameters: JSON object with action-specific parameters
        description: Optional human-readable explanation

    Returns:
        Confirmation with created action ID
    """
    print(f"  🔧 Tool Called: create_action(rule_id='{rule_id}', type='{action_type}')")

    # Validate rule exists
    rule_exists = any(r["id"] == rule_id for r in MOCK_DATABASE["rules"])
    if not rule_exists:
        return {"error": f"Rule with ID '{rule_id}' not found. Create the rule first."}

    # Validate action type
    valid_types = ["frequencyScanRequest", "geolocationRequest", "userNotification"]
    if action_type not in valid_types:
        return {"error": f"Invalid action_type. Must be one of: {valid_types}"}

    # Validate parameters based on action type
    if action_type == "frequencyScanRequest":
        if "sensorIds" not in parameters:
            return {"error": "frequencyScanRequest requires 'sensorIds' parameter"}
        if not isinstance(parameters["sensorIds"], list) or len(parameters["sensorIds"]) == 0:
            return {"error": "sensorIds must be a non-empty list"}

    elif action_type == "geolocationRequest":
        required_params = ["algorithm", "sensorIds"]
        for param in required_params:
            if param not in parameters:
                return {"error": f"Missing required parameter: {param}"}

        valid_algorithms = ["TDOA", "PDOA"]
        if parameters.get("algorithm") not in valid_algorithms:
            return {"error": f"Invalid algorithm. Must be one of: {valid_algorithms}"}

        if not isinstance(parameters["sensorIds"], list) or len(parameters["sensorIds"]) < 2:
            return {"error": "geolocationRequest requires at least 2 sensors"}

    elif action_type == "userNotification":
        if "message" not in parameters:
            return {"error": "userNotification requires 'message' parameter"}
        if not parameters["message"].strip():
            return {"error": "Notification message cannot be empty"}

    # Create the action
    new_action = {
        "id": str(uuid.uuid4()),
        "rule_id": rule_id,
        "actionType": action_type,
        "parameters": parameters,
        "description": description,
        "createdAt": datetime.utcnow().timestamp(),
        "updatedAt": datetime.utcnow().timestamp()
    }

    # Add to mock database
    MOCK_DATABASE["actions"].append(new_action)

    print(f"  ✓ Created action with ID: {new_action['id']}")
    return new_action


def activate_automation_rule(rule_id: str) -> dict:
    """
    Activate (enable) an automation rule to start monitoring and executing.
    DO NOT CALL create_automation_rule.
    
    When activated, the rule will:
    - Begin monitoring for conditions
    - Reset all condition satisfaction states
    - Execute actions when ALL conditions are met
    - Respect maxExecutions and time window limits
    
    Args:
        rule_id: The UUID of the automation rule to activate
        
    Returns:
        Confirmation with rule ID
        
    Example:
        activate_automation_rule("550e8400-e29b-41d4-a716-446655440000")
    """
    print(f"  🔧 Tool Called: activate_automation_rule(rule_id='{rule_id}')")
    
    # Find and update the rule
    for rule in MOCK_DATABASE["rules"]:
        if rule["id"] == rule_id:
            if rule["isEnabled"]:
                return {
                    "success": True,
                    "rule_id": rule_id,
                    "rule_name": rule["name"],
                    "status": "already_active",
                    "message": f"Rule '{rule['name']}' (ID: {rule_id}) is already activated."
                }
            
            rule["isEnabled"] = True
            rule["updatedAt"] = datetime.utcnow().isoformat() + "Z"
            
            # Reset condition satisfaction states
            if rule_id in MOCK_DATABASE["conditions"]:
                for condition in MOCK_DATABASE["conditions"][rule_id]:
                    condition["isSatisfied"] = False
                    condition["satisfiedAt"] = None
            
            print(f"  ✓ Activated rule: {rule['name']}")
            return {
                "success": True,
                "rule_id": rule_id,
                "rule_name": rule["name"],
                "status": "activated",
                "message": f"Rule '{rule['name']}' (ID: {rule_id}) has been activated successfully. "
                          f"The rule is now monitoring for conditions and will execute actions when all conditions are met."
            }
    
    return {"error": f"Rule with ID '{rule_id}' not found"}


def deactivate_automation_rule(rule_id: str) -> dict:
    """
    Deactivate (disable) an automation rule to stop monitoring and execution.
    
    Use this to:
    - Deactivate an automation rule. DO NOT CALL to create automation rule. 
      DO NOT CALL to delete automation rule.
    - Temporarily pause a rule without deleting it
    - Stop a misbehaving rule
    - Disable seasonal or time-limited automation
    
    The rule and its conditions/actions remain configured and can be reactivated later.
    
    Args:
        rule_id: The UUID of the automation rule to deactivate
        
    Returns:
        Confirmation with rule ID
    """
    print(f"  🔧 Tool Called: deactivate_automation_rule(rule_id='{rule_id}')")
    
    # Find and update the rule
    for rule in MOCK_DATABASE["rules"]:
        if rule["id"] == rule_id:
            if not rule["isEnabled"]:
                return {
                    "success": True,
                    "rule_id": rule_id,
                    "rule_name": rule["name"],
                    "status": "already_inactive",
                    "message": f"Rule '{rule['name']}' (ID: {rule_id}) is already deactivated."
                }
            
            rule["isEnabled"] = False
            rule["updatedAt"] = datetime.utcnow().isoformat() + "Z"
            
            print(f"  ✓ Deactivated rule: {rule['name']}")
            return {
                "success": True,
                "rule_id": rule_id,
                "rule_name": rule["name"],
                "status": "deactivated",
                "message": f"Rule '{rule['name']}' (ID: {rule_id}) has been deactivated successfully. "
                          f"The rule configuration is preserved and can be reactivated later."
            }
    
    return {"error": f"Rule with ID '{rule_id}' not found"}


def update_condition(
    rule_id: str,
    condition_id: Optional[str] = None,
    condition_type: Optional[str] = None,
    parameters: Optional[dict] = None,
    description: Optional[str] = None
) -> dict:
    """
    Update an existing condition for an automation rule.
    Only rule_id is required, all other parameters are optional.

    Args:
        rule_id: UUID of the rule this condition belongs to (required)
        condition_id: UUID of specific condition to update. If not provided, updates first condition.
        condition_type: Optional new type - "signalDetection" or "spectralEnergy"
        parameters: Optional dict with condition-specific parameters to update (partial updates allowed)
        description: Optional human-readable explanation

    Returns:
        Confirmation with updated condition details
    """
    print(f"  🔧 Tool Called: update_condition(rule_id='{rule_id}', condition_id='{condition_id}')")

    # Check if rule exists
    rule_exists = any(r["id"] == rule_id for r in MOCK_DATABASE["rules"])
    if not rule_exists:
        return {"error": f"Rule with ID '{rule_id}' not found"}

    # Get conditions for the rule
    conditions = MOCK_DATABASE["conditions"].get(rule_id, [])
    if not conditions:
        return {"error": f"No conditions found for rule '{rule_id}'"}

    # Find the specific condition to update
    target_condition = None
    if condition_id:
        for cond in conditions:
            if cond["id"] == condition_id:
                target_condition = cond
                break
        if not target_condition:
            return {"error": f"Condition with ID '{condition_id}' not found for rule '{rule_id}'"}
    else:
        # Update the first condition if no specific ID provided
        target_condition = conditions[0]
        print(f"  ℹ️ No condition_id provided, updating first condition: {target_condition['id']}")

    # Track what was updated
    updates_made = []

    # Update condition type if provided
    if condition_type:
        valid_types = ["signalDetection", "spectralEnergy"]
        if condition_type not in valid_types:
            return {"error": f"Invalid condition_type. Must be one of: {valid_types}"}
        target_condition["conditionType"] = condition_type
        updates_made.append(f"conditionType -> {condition_type}")

    # Update parameters if provided (merge with existing)
    if parameters:
        if "parameters" not in target_condition:
            target_condition["parameters"] = {}

        # Validate parameters based on condition type
        current_type = target_condition.get("conditionType", "signalDetection")

        if "minFrequencyMHz" in parameters:
            min_freq = parameters["minFrequencyMHz"]
            if not (10 <= min_freq <= 6000):
                return {"error": "minFrequencyMHz must be between 10 and 6000"}
            target_condition["parameters"]["minFrequencyMHz"] = min_freq
            updates_made.append(f"minFrequencyMHz -> {min_freq}")

        if "maxFrequencyMHz" in parameters:
            max_freq = parameters["maxFrequencyMHz"]
            if not (10 <= max_freq <= 6000):
                return {"error": "maxFrequencyMHz must be between 10 and 6000"}
            target_condition["parameters"]["maxFrequencyMHz"] = max_freq
            updates_made.append(f"maxFrequencyMHz -> {max_freq}")

        if "signalType" in parameters:
            valid_signals = ["Energy", "5G", "LTE", "QPSK", "CW", "PCMPM", "CPM", "CPMFM", "BPSK", "SOQPSK"]
            if parameters["signalType"] not in valid_signals:
                return {"error": f"Invalid signalType. Must be one of: {valid_signals}"}
            target_condition["parameters"]["signalType"] = parameters["signalType"]
            updates_made.append(f"signalType -> {parameters['signalType']}")

        if "threshold_dBm" in parameters:
            threshold = parameters["threshold_dBm"]
            if not (-150 <= threshold <= 150):
                return {"error": "threshold_dBm must be between -150 and 150"}
            target_condition["parameters"]["threshold_dBm"] = threshold
            updates_made.append(f"threshold_dBm -> {threshold}")

    # Update description if provided
    if description:
        target_condition["description"] = description
        updates_made.append(f"description updated")

    # Update timestamp
    target_condition["updatedAt"] = datetime.utcnow().timestamp()

    if not updates_made:
        return {
            "success": True,
            "condition_id": target_condition["id"],
            "rule_id": rule_id,
            "message": "No changes were made. Provide parameters to update.",
            "current_condition": target_condition
        }

    print(f"  ✓ Updated condition: {', '.join(updates_made)}")
    return {
        "success": True,
        "condition_id": target_condition["id"],
        "rule_id": rule_id,
        "conditionType": target_condition["conditionType"],
        "updates_made": updates_made,
        "message": f"Condition '{target_condition['id']}' updated successfully. Changes: {', '.join(updates_made)}",
        "updated_condition": target_condition
    }


def update_action(
    rule_id: str,
    action_id: Optional[str] = None,
    action_type: Optional[str] = None,
    parameters: Optional[dict] = None,
    description: Optional[str] = None
) -> dict:
    """
    Update an existing action for an automation rule.
    Only rule_id is required, all other parameters are optional.

    Args:
        rule_id: UUID of the rule this action belongs to (required)
        action_id: UUID of specific action to update. If not provided, updates first action.
        action_type: Optional new type - "frequencyScanRequest", "geolocationRequest", or "userNotification"
        parameters: Optional dict with action-specific parameters to update (partial updates allowed)
        description: Optional human-readable explanation

    Returns:
        Confirmation with updated action details
    """
    print(f"  🔧 Tool Called: update_action(rule_id='{rule_id}', action_id='{action_id}')")

    # Check if rule exists
    rule_exists = any(r["id"] == rule_id for r in MOCK_DATABASE["rules"])
    if not rule_exists:
        return {"error": f"Rule with ID '{rule_id}' not found"}

    # Get actions for the rule
    actions = MOCK_DATABASE["actions"].get(rule_id, [])
    if not actions:
        return {"error": f"No actions found for rule '{rule_id}'"}

    # Find the specific action to update
    target_action = None
    if action_id:
        for act in actions:
            if act["id"] == action_id:
                target_action = act
                break
        if not target_action:
            return {"error": f"Action with ID '{action_id}' not found for rule '{rule_id}'"}
    else:
        # Update the first action if no specific ID provided
        target_action = actions[0]
        print(f"  ℹ️ No action_id provided, updating first action: {target_action['id']}")

    # Track what was updated
    updates_made = []

    # Update action type if provided
    if action_type:
        valid_types = ["frequencyScanRequest", "geolocationRequest", "userNotification"]
        if action_type not in valid_types:
            return {"error": f"Invalid action_type. Must be one of: {valid_types}"}
        target_action["actionType"] = action_type
        updates_made.append(f"actionType -> {action_type}")

    # Update parameters if provided (merge with existing)
    if parameters:
        if "parameters" not in target_action:
            target_action["parameters"] = {}

        # Validate and update based on parameter keys
        if "message" in parameters:
            if not parameters["message"].strip():
                return {"error": "Notification message cannot be empty"}
            target_action["parameters"]["message"] = parameters["message"]
            updates_made.append(f"message updated")

        if "sensorIds" in parameters:
            if not isinstance(parameters["sensorIds"], list) or len(parameters["sensorIds"]) == 0:
                return {"error": "sensorIds must be a non-empty list"}
            target_action["parameters"]["sensorIds"] = parameters["sensorIds"]
            updates_made.append(f"sensorIds -> {parameters['sensorIds']}")

        if "algorithm" in parameters:
            valid_algorithms = ["TDOA", "PDOA"]
            if parameters["algorithm"] not in valid_algorithms:
                return {"error": f"Invalid algorithm. Must be one of: {valid_algorithms}"}
            target_action["parameters"]["algorithm"] = parameters["algorithm"]
            updates_made.append(f"algorithm -> {parameters['algorithm']}")

    # Update description if provided
    if description:
        target_action["description"] = description
        updates_made.append(f"description updated")

    # Update timestamp
    target_action["updatedAt"] = datetime.utcnow().timestamp()

    if not updates_made:
        return {
            "success": True,
            "action_id": target_action["id"],
            "rule_id": rule_id,
            "message": "No changes were made. Provide parameters to update.",
            "current_action": target_action
        }

    print(f"  ✓ Updated action: {', '.join(updates_made)}")
    return {
        "success": True,
        "action_id": target_action["id"],
        "rule_id": rule_id,
        "actionType": target_action["actionType"],
        "updates_made": updates_made,
        "message": f"Action '{target_action['id']}' updated successfully. Changes: {', '.join(updates_made)}",
        "updated_action": target_action
    }

def create_rule_condition(
    # Rule parameters
    name: str,
    description: str,
    is_enabled: bool = False,
    max_executions: Optional[int] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    # Condition parameters
    condition_type: str = None,
    condition_parameters: dict = None,
    condition_description: Optional[str] = None
) -> dict:
    """
    Create a new automation rule AND its condition in a single operation.
    Use this when the user query provides enough information for both rule and condition.
    
    Args:
        # Rule parameters
        name: Clear, descriptive name for the rule (e.g., "5G Signal Monitor")
        description: Detailed explanation of what the rule does
        is_enabled: Whether rule is active immediately (default: False)
        max_executions: Optional limit on how many times rule can trigger
        start_time: ISO format datetime when rule becomes active
        end_time: ISO format datetime when rule becomes inactive
        
        # Condition parameters  
        condition_type: "signalDetection" or "spectralEnergy"
        condition_parameters: Dict with condition-specific parameters:
            - For signalDetection: minFrequencyMHz, maxFrequencyMHz, signalType
            - For spectralEnergy: minFrequencyMHz, maxFrequencyMHz, threshold_dBm
        condition_description: Optional human-readable explanation of the condition
        
    Returns:
        Dict containing created rule and condition with their IDs
        
    Example:
        create_rule_condition(
            name="5G Monitor",
            description="Monitors 5G signals",
            condition_type="signalDetection",
            condition_parameters={"minFrequencyMHz": 3400, "maxFrequencyMHz": 3600, "signalType": "5G"}
        )
    """
    print(f"  🔧 Tool Called: create_rule_condition(name='{name}', condition_type='{condition_type}')")
    
    # Validate rule inputs
    if not name or not name.strip():
        return {"error": "Rule name cannot be empty"}
    
    if start_time and end_time:
        try:
            start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            if start >= end:
                return {"error": "start_time must be before end_time"}
        except ValueError as e:
            return {"error": f"Invalid datetime format: {str(e)}"}
    
    # Validate condition inputs
    if not condition_type:
        return {"error": "condition_type is required (signalDetection or spectralEnergy)"}
    
    valid_condition_types = ["signalDetection", "spectralEnergy"]
    if condition_type not in valid_condition_types:
        return {"error": f"Invalid condition_type. Must be one of: {valid_condition_types}"}
    
    if not condition_parameters:
        return {"error": "condition_parameters is required"}
    
    # Validate condition parameters based on type
    # Apply default frequency values if not provided
    if "minFrequencyMHz" not in condition_parameters:
        condition_parameters["minFrequencyMHz"] = 10
        print(f"  ℹ️ Using default minFrequencyMHz: 10")
    if "maxFrequencyMHz" not in condition_parameters:
        condition_parameters["maxFrequencyMHz"] = 6000
        print(f"  ℹ️ Using default maxFrequencyMHz: 6000")
    
    min_freq = condition_parameters.get("minFrequencyMHz")
    max_freq = condition_parameters.get("maxFrequencyMHz")
    
    # Validate frequency range
    if not (10 <= min_freq <= 6000 and 10 <= max_freq <= 6000):
        return {"error": "Frequencies must be between 10 and 6000 MHz"}
    if min_freq >= max_freq:
        return {"error": "minFrequencyMHz must be less than maxFrequencyMHz"}
    
    if condition_type == "signalDetection":
        # signalType is required for signalDetection
        if "signalType" not in condition_parameters:
            return {"error": "Missing required condition parameter: signalType"}
        
        valid_signals = ["Energy", "5G", "LTE", "QPSK", "CW", "PCMPM", "CPM", "CPMFM", "BPSK", "SOQPSK"]
        if condition_parameters.get("signalType") not in valid_signals:
            return {"error": f"Invalid signalType. Must be one of: {valid_signals}"}
    
    elif condition_type == "spectralEnergy":
        # threshold_dBm is required for spectralEnergy
        if "threshold_dBm" not in condition_parameters:
            return {"error": "Missing required condition parameter: threshold_dBm"}
        
        threshold = condition_parameters.get("threshold_dBm")
        if not (-150 <= threshold <= 150):
            return {"error": "threshold_dBm must be between -150 and 150"}
    
    # Create the rule
    rule_id = str(uuid.uuid4())
    new_rule = {
        "id": rule_id,
        "name": name,
        "description": description,
        "isEnabled": is_enabled,
        "createdAt": datetime.utcnow().isoformat() + "Z",
        "updatedAt": datetime.utcnow().isoformat() + "Z"
    }
    
    if max_executions is not None:
        new_rule["maxExecutions"] = max_executions
        new_rule["executionsRemaining"] = max_executions
    
    if start_time:
        new_rule["startTime"] = start_time
    if end_time:
        new_rule["endTime"] = end_time
    
    # Create the condition
    condition_id = str(uuid.uuid4())
    new_condition = {
        "id": condition_id,
        "rule_id": rule_id,
        "conditionType": condition_type,
        "parameters": condition_parameters,
        "description": condition_description,
        "isSatisfied": False,
        "createdAt": datetime.utcnow().timestamp(),
        "updatedAt": datetime.utcnow().timestamp()
    }
    
    # Add to mock database
    MOCK_DATABASE["rules"].append(new_rule)
    if rule_id not in MOCK_DATABASE["conditions"]:
        MOCK_DATABASE["conditions"][rule_id] = []
    MOCK_DATABASE["conditions"][rule_id].append(new_condition)
    
    print(f"  ✓ Created rule '{name}' with ID: {rule_id}")
    print(f"  ✓ Created {condition_type} condition with ID: {condition_id}")
    
    return {
        "success": True,
        "rule": new_rule,
        "rule_id": rule_id,
        "rule_name": name,
        "condition": new_condition,
        "condition_id": condition_id,
        "condition_type": condition_type,
        "message": f"Successfully created rule '{name}' (ID: {rule_id}) with {condition_type} condition (ID: {condition_id})"
    }


def create_rule_action(
    # Rule parameters
    name: str,
    description: str,
    is_enabled: bool = False,
    max_executions: Optional[int] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    # Action parameters
    action_type: str = None,
    action_parameters: dict = None,
    action_description: Optional[str] = None
) -> dict:
    """
    Create a new automation rule AND its action in a single operation.
    Use this when the user query provides enough information for both rule and action.
    
    Args:
        # Rule parameters
        name: Clear, descriptive name for the rule
        description: Detailed explanation of what the rule does
        is_enabled: Whether rule is active immediately (default: False)
        max_executions: Optional limit on how many times rule can trigger
        start_time: ISO format datetime when rule becomes active
        end_time: ISO format datetime when rule becomes inactive
        
        # Action parameters
        action_type: "frequencyScanRequest", "geolocationRequest", or "userNotification"
        action_parameters: Dict with action-specific parameters:
            - For frequencyScanRequest: sensorIds (list)
            - For geolocationRequest: algorithm ("TDOA" or "PDOA"), sensorIds (list, min 2)
            - For userNotification: message (string)
        action_description: Optional human-readable explanation of the action
        
    Returns:
        Dict containing created rule and action with their IDs
        
    Example:
        create_rule_action(
            name="Alert Rule",
            description="Sends notification on detection",
            action_type="userNotification",
            action_parameters={"message": "Signal detected!"}
        )
    """
    print(f"  🔧 Tool Called: create_rule_action(name='{name}', action_type='{action_type}')")
    
    # Validate rule inputs
    if not name or not name.strip():
        return {"error": "Rule name cannot be empty"}
    
    if start_time and end_time:
        try:
            start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            if start >= end:
                return {"error": "start_time must be before end_time"}
        except ValueError as e:
            return {"error": f"Invalid datetime format: {str(e)}"}
    
    # Validate action inputs
    if not action_type:
        return {"error": "action_type is required (frequencyScanRequest, geolocationRequest, or userNotification)"}
    
    valid_action_types = ["frequencyScanRequest", "geolocationRequest", "userNotification"]
    if action_type not in valid_action_types:
        return {"error": f"Invalid action_type. Must be one of: {valid_action_types}"}
    
    if not action_parameters:
        return {"error": "action_parameters is required"}
    
    # Validate action parameters based on type
    if action_type == "frequencyScanRequest":
        if "sensorIds" not in action_parameters:
            return {"error": "frequencyScanRequest requires 'sensorIds' parameter"}
        if not isinstance(action_parameters["sensorIds"], list) or len(action_parameters["sensorIds"]) == 0:
            return {"error": "sensorIds must be a non-empty list"}
    
    elif action_type == "geolocationRequest":
        required_params = ["algorithm", "sensorIds"]
        for param in required_params:
            if param not in action_parameters:
                return {"error": f"Missing required action parameter: {param}"}
        
        valid_algorithms = ["TDOA", "PDOA"]
        if action_parameters.get("algorithm") not in valid_algorithms:
            return {"error": f"Invalid algorithm. Must be one of: {valid_algorithms}"}
        
        if not isinstance(action_parameters["sensorIds"], list) or len(action_parameters["sensorIds"]) < 2:
            return {"error": "geolocationRequest requires at least 2 sensors"}
    
    elif action_type == "userNotification":
        if "message" not in action_parameters:
            return {"error": "userNotification requires 'message' parameter"}
        if not action_parameters["message"].strip():
            return {"error": "Notification message cannot be empty"}
    
    # Create the rule
    rule_id = str(uuid.uuid4())
    new_rule = {
        "id": rule_id,
        "name": name,
        "description": description,
        "isEnabled": is_enabled,
        "createdAt": datetime.utcnow().isoformat() + "Z",
        "updatedAt": datetime.utcnow().isoformat() + "Z"
    }
    
    if max_executions is not None:
        new_rule["maxExecutions"] = max_executions
        new_rule["executionsRemaining"] = max_executions
    
    if start_time:
        new_rule["startTime"] = start_time
    if end_time:
        new_rule["endTime"] = end_time
    
    # Create the action
    action_id = str(uuid.uuid4())
    new_action = {
        "id": action_id,
        "rule_id": rule_id,
        "actionType": action_type,
        "parameters": action_parameters,
        "description": action_description,
        "createdAt": datetime.utcnow().timestamp(),
        "updatedAt": datetime.utcnow().timestamp()
    }
    
    # Add to mock database
    MOCK_DATABASE["rules"].append(new_rule)
    if rule_id not in MOCK_DATABASE["actions"]:
        MOCK_DATABASE["actions"][rule_id] = []
    MOCK_DATABASE["actions"][rule_id].append(new_action)
    
    print(f"  ✓ Created rule '{name}' with ID: {rule_id}")
    print(f"  ✓ Created {action_type} action with ID: {action_id}")
    
    return {
        "success": True,
        "rule": new_rule,
        "rule_id": rule_id,
        "rule_name": name,
        "action": new_action,
        "action_id": action_id,
        "action_type": action_type,
        "message": f"Successfully created rule '{name}' (ID: {rule_id}) with {action_type} action (ID: {action_id})"
    }

def create_rule_condition_action(
    # Rule parameters
    name: str,
    description: str,
    is_enabled: bool = False,
    max_executions: Optional[int] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    # Condition parameters
    condition_type: str = None,
    condition_parameters: dict = None,
    condition_description: Optional[str] = None,
    # Action parameters
    action_type: str = None,
    action_parameters: dict = None,
    action_description: Optional[str] = None
) -> dict:
    """
    Create a new automation rule WITH BOTH a condition AND an action in a single operation.
    Use this when the user query provides enough information for rule, condition, AND action.

    Args:
        # Rule parameters
        name: Clear, descriptive name for the rule (e.g., "5G Signal Monitor with Alert")
        description: Detailed explanation of what the rule does
        is_enabled: Whether rule is active immediately (default: False)
        max_executions: Optional limit on how many times rule can trigger
        start_time: ISO format datetime when rule becomes active
        end_time: ISO format datetime when rule becomes inactive

        # Condition parameters
        condition_type: "signalDetection" or "spectralEnergy"
        condition_parameters: Dict with condition-specific parameters:
            - For signalDetection: signalType (required), minFrequencyMHz (optional, default 10), maxFrequencyMHz (optional, default 6000)
            - For spectralEnergy: threshold_dBm (required), minFrequencyMHz (optional, default 10), maxFrequencyMHz (optional, default 6000)
        condition_description: Optional human-readable explanation of the condition

        # Action parameters
        action_type: "frequencyScanRequest", "geolocationRequest", or "userNotification"
        action_parameters: Dict with action-specific parameters:
            - For frequencyScanRequest: sensorIds (list)
            - For geolocationRequest: algorithm ("TDOA" or "PDOA"), sensorIds (list, min 2)
            - For userNotification: message (string)
        action_description: Optional human-readable explanation of the action

    Returns:
        Dict containing created rule, condition, and action with their IDs

    Example:
        create_rule_condition_action(
            name="5G Monitor with Alert",
            description="Monitors 5G signals and sends notification",
            condition_type="signalDetection",
            condition_parameters={"minFrequencyMHz": 3400, "maxFrequencyMHz": 3600, "signalType": "5G"},
            action_type="userNotification",
            action_parameters={"message": "5G signal detected!"}
        )
    """
    print(f"  🔧 Tool Called: create_rule_condition_action(name='{name}', condition_type='{condition_type}', action_type='{action_type}')")

    # Validate rule inputs
    if not name or not name.strip():
        return {"error": "Rule name cannot be empty"}

    if start_time and end_time:
        try:
            start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            if start >= end:
                return {"error": "start_time must be before end_time"}
        except ValueError as e:
            return {"error": f"Invalid datetime format: {str(e)}"}

    # ========== VALIDATE CONDITION ==========
    if not condition_type:
        return {"error": "condition_type is required (signalDetection or spectralEnergy)"}

    valid_condition_types = ["signalDetection", "spectralEnergy"]
    if condition_type not in valid_condition_types:
        return {"error": f"Invalid condition_type. Must be one of: {valid_condition_types}"}

    if not condition_parameters:
        condition_parameters = {}

    # Apply default frequency values if not provided
    if "minFrequencyMHz" not in condition_parameters:
        condition_parameters["minFrequencyMHz"] = 10
        print(f"  ℹ️ Using default minFrequencyMHz: 10")
    if "maxFrequencyMHz" not in condition_parameters:
        condition_parameters["maxFrequencyMHz"] = 6000
        print(f"  ℹ️ Using default maxFrequencyMHz: 6000")

    min_freq = condition_parameters.get("minFrequencyMHz")
    max_freq = condition_parameters.get("maxFrequencyMHz")

    # Validate frequency range
    if not (10 <= min_freq <= 6000 and 10 <= max_freq <= 6000):
        return {"error": "Frequencies must be between 10 and 6000 MHz"}
    if min_freq >= max_freq:
        return {"error": "minFrequencyMHz must be less than maxFrequencyMHz"}

    if condition_type == "signalDetection":
        if "signalType" not in condition_parameters:
            return {"error": "Missing required condition parameter: signalType"}

        valid_signals = ["Energy", "5G", "LTE", "QPSK", "CW", "PCMPM", "CPM", "CPMFM", "BPSK", "SOQPSK"]
        if condition_parameters.get("signalType") not in valid_signals:
            return {"error": f"Invalid signalType. Must be one of: {valid_signals}"}

    elif condition_type == "spectralEnergy":
        if "threshold_dBm" not in condition_parameters:
            return {"error": "Missing required condition parameter: threshold_dBm"}

        threshold = condition_parameters.get("threshold_dBm")
        if not (-150 <= threshold <= 150):
            return {"error": "threshold_dBm must be between -150 and 150"}

    # ========== VALIDATE ACTION ==========
    if not action_type:
        return {"error": "action_type is required (frequencyScanRequest, geolocationRequest, or userNotification)"}

    valid_action_types = ["frequencyScanRequest", "geolocationRequest", "userNotification"]
    if action_type not in valid_action_types:
        return {"error": f"Invalid action_type. Must be one of: {valid_action_types}"}

    if not action_parameters:
        return {"error": "action_parameters is required"}

    if action_type == "frequencyScanRequest":
        if "sensorIds" not in action_parameters:
            return {"error": "frequencyScanRequest requires 'sensorIds' parameter"}
        if not isinstance(action_parameters["sensorIds"], list) or len(action_parameters["sensorIds"]) == 0:
            return {"error": "sensorIds must be a non-empty list"}

    elif action_type == "geolocationRequest":
        required_params = ["algorithm", "sensorIds"]
        for param in required_params:
            if param not in action_parameters:
                return {"error": f"Missing required action parameter: {param}"}

        valid_algorithms = ["TDOA", "PDOA"]
        if action_parameters.get("algorithm") not in valid_algorithms:
            return {"error": f"Invalid algorithm. Must be one of: {valid_algorithms}"}

        if not isinstance(action_parameters["sensorIds"], list) or len(action_parameters["sensorIds"]) < 2:
            return {"error": "geolocationRequest requires at least 2 sensors"}

    elif action_type == "userNotification":
        if "message" not in action_parameters:
            return {"error": "userNotification requires 'message' parameter"}
        if not action_parameters["message"].strip():
            return {"error": "Notification message cannot be empty"}

    # ========== CREATE RULE ==========
    rule_id = str(uuid.uuid4())
    new_rule = {
        "id": rule_id,
        "name": name,
        "description": description,
        "isEnabled": is_enabled,
        "createdAt": datetime.utcnow().isoformat() + "Z",
        "updatedAt": datetime.utcnow().isoformat() + "Z"
    }

    if max_executions is not None:
        new_rule["maxExecutions"] = max_executions
        new_rule["executionsRemaining"] = max_executions

    if start_time:
        new_rule["startTime"] = start_time
    if end_time:
        new_rule["endTime"] = end_time

    # ========== CREATE CONDITION ==========
    condition_id = str(uuid.uuid4())
    new_condition = {
        "id": condition_id,
        "rule_id": rule_id,
        "conditionType": condition_type,
        "parameters": condition_parameters,
        "description": condition_description,
        "isSatisfied": False,
        "createdAt": datetime.utcnow().timestamp(),
        "updatedAt": datetime.utcnow().timestamp()
    }

    # ========== CREATE ACTION ==========
    action_id = str(uuid.uuid4())
    new_action = {
        "id": action_id,
        "rule_id": rule_id,
        "actionType": action_type,
        "parameters": action_parameters,
        "description": action_description,
        "createdAt": datetime.utcnow().timestamp(),
        "updatedAt": datetime.utcnow().timestamp()
    }

    # ========== ADD TO DATABASE ==========
    MOCK_DATABASE["rules"].append(new_rule)

    if rule_id not in MOCK_DATABASE["conditions"]:
        MOCK_DATABASE["conditions"][rule_id] = []
    MOCK_DATABASE["conditions"][rule_id].append(new_condition)

    if rule_id not in MOCK_DATABASE["actions"]:
        MOCK_DATABASE["actions"][rule_id] = []
    MOCK_DATABASE["actions"][rule_id].append(new_action)

    print(f"  ✓ Created rule '{name}' with ID: {rule_id}")
    print(f"  ✓ Created {condition_type} condition with ID: {condition_id}")
    print(f"  ✓ Created {action_type} action with ID: {action_id}")

    return {
        "success": True,
        "rule": new_rule,
        "rule_id": rule_id,
        "rule_name": name,
        "condition": new_condition,
        "condition_id": condition_id,
        "condition_type": condition_type,
        "action": new_action,
        "action_id": action_id,
        "action_type": action_type,
        "message": f"Successfully created rule '{name}' (ID: {rule_id}) with {condition_type} condition (ID: {condition_id}) and {action_type} action (ID: {action_id})"
    }

# ============================================================================
# UPDATE HANDLER STATE
# ============================================================================

class UpdateAgentState(TypedDict):
    """State for the Update Intent Handler agent workflow"""
    user_query: str
    original_intent_state: dict  # Original state from main workflow
    messages: Annotated[list, operator.add]
    iteration_count: int
    max_iterations: int
    
    # Tool execution tracking
    tools_called: Annotated[list, operator.add]  # History of tool calls
    updated_entities: dict  # Track what's been updated/created
    
    # Decision making
    next_action: str  # "call_tool" or "respond"
    selected_tool: str  # Tool to call next
    tool_parameters: dict  # Parameters for the tool
    
    # Response generation
    has_completed_update: bool
    final_response: str
    reasoning: str
    validation_errors: list


# ============================================================================
# UPDATE TOOL REGISTRY
# ============================================================================

AVAILABLE_UPDATE_TOOLS = {
    "list_automation_rules": {
        "function": list_automation_rules,
        "description": "Lists all automation rules. Use this to find rule IDs when user provides rule name instead of UUID. ALWAYS call this first if user references a rule by name.",
        "parameters": {},
        "example": "list_automation_rules()"
    },
    "activate_automation_rule": {
        "function": activate_automation_rule,
        "description": "Activate (enable) an automation rule to start monitoring and executing. DO NOT use this to create rules. Use when user wants to enable/activate/turn on a rule.",
        "parameters": {
            "rule_id": "string (required) - The UUID of the automation rule to activate"
        },
        "example": 'activate_automation_rule(rule_id="rule-001")'
    },
    "deactivate_automation_rule": {
        "function": deactivate_automation_rule,
        "description": "Deactivate (disable) an automation rule to stop monitoring. DO NOT use this to delete rules. Use when user wants to disable/deactivate/turn off/pause a rule.",
        "parameters": {
            "rule_id": "string (required) - The UUID of the automation rule to deactivate"
        },
        "example": 'deactivate_automation_rule(rule_id="rule-001")'
    },
    "update_condition": {
        "function": update_condition,
        "description": "Update an existing condition for a rule. Use this to modify condition parameters like frequency range, signal type, or threshold. Only rule_id is required, other parameters are optional.",
        "parameters": {
            "rule_id": "string (required) - UUID of the rule this condition belongs to",
            "condition_id": "string (optional) - UUID of specific condition to update. If not provided, updates the first condition of the rule.",
            "condition_type": "string (optional) - 'signalDetection' or 'spectralEnergy'. Only provide if changing the type.",
            "parameters": "dict (optional) - Condition-specific parameters to update (min-max frequency, signalType, threshold dBm). See the schema for the parameters for different condition types. Also derive the parameters from user's query. Can provide partial updates.",
            "description": "string (optional) - Human-readable explanation"
        },
        "example": 'update_condition(rule_id="rule-001", parameters={"minFrequencyMHz": 3500, "maxFrequencyMHz": 3700})'
    },
    "update_action": {
        "function": update_action,
        "description": "Update an existing action for a rule. Use this to modify action parameters like message, sensor IDs, or algorithm. Only rule_id is required, other parameters are optional.",
        "parameters": {
            "rule_id": "string (required) - UUID of the rule this action belongs to",
            "action_id": "string (optional) - UUID of specific action to update. If not provided, updates the first action of the rule.",
            "action_type": "string (optional) - 'frequencyScanRequest', 'geolocationRequest', or 'userNotification'. Only provide if changing the type.",
            "parameters": "dict (optional) - Action-specific parameters to update (message, sensorsIds, algorithm). the schema for the parameters for different action types. Also derive the parameters from user's query. Can provide partial updates.",
            "description": "string (optional) - Human-readable explanation"
        },
        "example": 'update_action(rule_id="rule-001", parameters={"message": "Updated alert message!"})'
    }
}

UPDATE_SCHEMA_DETAILS = """
CONDITION TYPE SCHEMAS:

1. signalDetection:
   Required parameters:
   - minFrequencyMHz (number, 10-6000): Minimum frequency
   - maxFrequencyMHz (number, 10-6000): Maximum frequency
   - signalType (string): One of ["Energy", "5G", "LTE", "QPSK", "CW", "PCMPM", "CPM", "CPMFM", "BPSK", "SOQPSK"]

2. spectralEnergy:
   Required parameters:
   - minFrequencyMHz (number, 10-6000): Minimum frequency
   - maxFrequencyMHz (number, 10-6000): Maximum frequency
   - threshold_dBm (number, -150 to 150): Power threshold in dBm

ACTION TYPE SCHEMAS:

1. frequencyScanRequest:
   Required parameters:
   - sensorIds (list of strings): Sensor IDs for scanning

2. geolocationRequest:
   Required parameters:
   - algorithm (string): "TDOA" or "PDOA"
   - sensorIds (list of strings, min 2): Sensor IDs for geolocation

3. userNotification:
   Required parameters:
   - message (string): Notification message to send
"""



# ============================================================================
# CREATE HANDLER STATE
# ============================================================================
class CreateAgentState(TypedDict):
    """State for the Create Intent Handler agent workflow"""
    user_query: str
    original_intent_state: dict  # Original state from main workflow
    messages: Annotated[list, operator.add]
    iteration_count: int
    max_iterations: int

    # Tool execution tracking
    tools_called: Annotated[list, operator.add]  # History of tool calls
    created_entities: dict  # Track what's been created

    # Decision making
    next_action: str  # �~P NEW: "call_tool", "respond", or "confirm"
    selected_tool: str  # Tool to call next
    tool_parameters: dict  # Parameters for the tool


    # Response generation
    has_completed_creation: bool
    final_response: str
    reasoning: str
    validation_errors: list



# ============================================================================
# TOOL REGISTRY
# ============================================================================

AVAILABLE_CREATE_TOOLS = {
    "list_automation_rules": {
        "function": list_automation_rules,
        "description": "Lists all automation rules. Use this to find rule IDs when adding conditions/actions to existing rules.",
        "parameters": {},
        "example": "list_automation_rules()"
    },
    "create_automation_rule": {
        "function": create_automation_rule,
        "description": "Creates a new automation rule. This tool only create basic information about the rule.  Always create rules with is_enabled=False initially. Rule  Returns rule ID needed for conditions/actions.",
        "parameters": {
            "name": "string (required) - some human readable and relevant name for the rule. Some text to represents the name of the rule. Don't have to be meaningful text.",
            "description": "string (optional) - text description what is this rule about",
            "is_enabled": "bool (optional, default=False) - Whether rule is active",
            "max_executions": "int (optional) - Limit on rule triggers",
            "start_time": "string (optional) - ISO datetime",
            "end_time": "string (optional) - ISO datetime"
        },
        "example": 'create_automation_rule(name="5G Alert", description="Monitor 5G signals", is_enabled=False)'
    },
    "create_rule_condition": {
        "function": create_rule_condition,
        "description": "Creates a new automation rule WITH a condition in ONE call. Use this when user query has enough information for BOTH rule AND condition (has condition_type and condition_parameters like frequency range, signal type, or threshold).",
        "parameters": {
            "name": "string (required) - Human readable name for the rule",
            "description": "string (optional) - Description of what this rule does",
            "is_enabled": "bool (optional, default=False) - Whether rule is active",
            "max_executions": "int (optional) - Limit on rule triggers",
            "start_time": "string (optional) - ISO datetime",
            "end_time": "string (optional) - ISO datetime",
            "condition_type": "string (required) - 'signalDetection' or 'spectralEnergy'",
            "condition_parameters": "dict (required) - Condition parameters based on type (minFrequencyMHz/maxFrequencyMHz optional, defaults to 10-6000)",
            "condition_description": "string (optional) - Description of the condition"
        },
        "example": 'create_rule_condition(name="5G Monitor", description="Monitor 5G signals", condition_type="signalDetection", condition_parameters={"minFrequencyMHz": 3400, "maxFrequencyMHz": 3600, "signalType": "5G"})'
    },
    "create_rule_action": {
        "function": create_rule_action,
        "description": "Creates a new automation rule WITH an action in ONE call. Use this when user query has enough information for BOTH rule AND action (has action_type and action_parameters like message, sensorIds, or algorithm).",
        "parameters": {
            "name": "string (required) - Human readable name for the rule",
            "description": "string (optional) - Description of what this rule does",
            "is_enabled": "bool (optional, default=False) - Whether rule is active",
            "max_executions": "int (optional) - Limit on rule triggers",
            "start_time": "string (optional) - ISO datetime",
            "end_time": "string (optional) - ISO datetime",
            "action_type": "string (required) - 'frequencyScanRequest', 'geolocationRequest', or 'userNotification'",
            "action_parameters": "dict (required) - Action parameters based on type",
            "action_description": "string (optional) - Description of the action"
        },
        "example": 'create_rule_action(name="Alert Rule", description="Send notifications", action_type="userNotification", action_parameters={"message": "Signal detected!"})'
    },
    "create_rule_condition_action": {
        "function": create_rule_condition_action,
        "description": "Creates a new automation rule WITH BOTH a condition AND an action in ONE call. Use this when user query has enough information for rule, condition, AND action. This is the most complete creation tool.",
        "parameters": {
            "name": "string (required) - Human readable name for the rule",
            "description": "string (optional) - Description of what this rule does",
            "is_enabled": "bool (optional, default=False) - Whether rule is active",
            "max_executions": "int (optional) - Limit on rule triggers",
            "start_time": "string (optional) - ISO datetime",
            "end_time": "string (optional) - ISO datetime",
            "condition_type": "string (required) - 'signalDetection' or 'spectralEnergy'",
            "condition_parameters": "dict (required) - Condition parameters (minFrequencyMHz/maxFrequencyMHz optional, defaults to 10-6000)",
            "condition_description": "string (optional) - Description of the condition",
            "action_type": "string (required) - 'frequencyScanRequest', 'geolocationRequest', or 'userNotification'",
            "action_parameters": "dict (required) - Action parameters based on type",
            "action_description": "string (optional) - Description of the action"
        },
        "example": 'create_rule_condition_action(name="5G Monitor with Alert", description="Monitor 5G and notify", condition_type="signalDetection", condition_parameters={"signalType": "5G"}, action_type="userNotification", action_parameters={"message": "5G detected!"})'
    }
}

CREATE_SCHEMA_DETAILS = """
CONDITION TYPE SCHEMAS:

1. signalDetection:
   Required parameters:
   - signalType (string): One of ["Energy", "5G", "LTE", "QPSK", "CW", "PCMPM", "CPM", "CPMFM", "BPSK", "SOQPSK"]
   Optional parameters (defaults applied if not provided):
   - minFrequencyMHz (number, 10-6000): Minimum frequency (default: 10)
   - maxFrequencyMHz (number, 10-6000): Maximum frequency (default: 6000)

2. spectralEnergy:
   Required parameters:
   - threshold_dBm (number, -150 to 150): Power threshold in dBm
   Optional parameters (defaults applied if not provided):
   - minFrequencyMHz (number, 10-6000): Minimum frequency (default: 10)
   - maxFrequencyMHz (number, 10-6000): Maximum frequency (default: 6000)

ACTION TYPE SCHEMAS:

1. frequencyScanRequest:
   Required parameters:
   - sensorIds (list of strings): Sensor IDs for scanning

2. geolocationRequest:
   Required parameters:
   - algorithm (string): "TDOA" or "PDOA"
   - sensorIds (list of strings, min 2): Sensor IDs for geolocation

3. userNotification:
   Required parameters:
   - message (string): Notification message to send
"""



def extract_json_from_response(response_text: str) -> str:
    """
    ⭐ Extracts JSON from LLM response by removing pre-text and post-text.
    
    Handles cases like:
    - "Here is the response: ```json {...}```"
    - "Let me analyze... {...} Hope this helps!"
    - Plain JSON without any wrapper
    
    Args:
        response_text: Raw LLM response that may contain JSON
        
    Returns:
        Cleaned JSON string ready for parsing
    """
    text = response_text.strip()
    
    # Method 1: Try to extract from markdown code blocks (```json ... ```)
    json_block_pattern = r'```(?:json)?\s*(\{[\s\S]*?\})\s*```'
    match = re.search(json_block_pattern, text)
    if match:
        return match.group(1).strip()
    
    # Method 2: Find the first { and last } to extract JSON object
    first_brace = text.find('{')
    last_brace = text.rfind('}')
    
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        potential_json = text[first_brace:last_brace + 1]
        return potential_json.strip()
    
    # Method 3: Return original if no JSON structure found
    return text


def safe_parse_json(response_text: str, default_value: dict = None) -> tuple[dict, bool]:
    """
    ⭐ Safely parses JSON from LLM response with cleaning.
    
    Args:
        response_text: Raw LLM response
        default_value: Default dict to return if parsing fails
        
    Returns:
        Tuple of (parsed_dict, success_bool)
    """
    if default_value is None:
        default_value = {}
    
    try:
        # First, try direct parsing (in case response is clean JSON)
        return json.loads(response_text.strip()), True
    except json.JSONDecodeError:
        pass
    
    try:
        # Extract and clean JSON from response
        cleaned_json = extract_json_from_response(response_text)
        print(f"  🧹 Cleaned JSON response (removed pre/post text)")
        return json.loads(cleaned_json), True
    except json.JSONDecodeError as e:
        print(f"  ⚠️ JSON parsing failed even after cleaning: {e}")
        print(f"  📝 Raw response preview: {response_text[:200]}...")
        return default_value, False

def execute_create_tool(tool_name: str, parameters: dict) -> Any:
    """Execute a tool with given parameters"""
    if tool_name not in AVAILABLE_CREATE_TOOLS:
        return {"error": f"Tool '{tool_name}' not found"}
    
    tool_info = AVAILABLE_CREATE_TOOLS[tool_name]
    try:
        return tool_info["function"](**parameters)
    except Exception as e:
        return {"error": f"Tool execution error: {str(e)}"}

def execute_update_tool(tool_name: str, parameters: dict) -> Any:
    """Execute a tool with given parameters"""
    if tool_name not in AVAILABLE_UPDATE_TOOLS:
        return {"error": f"Tool '{tool_name}' not found"}
    
    tool_info = AVAILABLE_UPDATE_TOOLS[tool_name]
    try:
        return tool_info["function"](**parameters)
    except Exception as e:
        return {"error": f"Tool execution error: {str(e)}"}


# ============================================================================
# UPDATE AGENT NODES
# ============================================================================

def plan_update_action_node(state: UpdateAgentState) -> UpdateAgentState:
    """
    Analyzes the user query and updated entities to decide next action.
    This is the planner node that decides which tool to call.
    """
    print("\n🤔 Planning Update Action...")

    # Check iteration limit
    if state["iteration_count"] >= state["max_iterations"]:
        print("  ⚠️ Max iterations reached, forcing response generation")
        return {
            **state,
            "next_action": "respond",
            "has_completed_update": True,
            "reasoning": "Maximum iterations reached"
        }

    # Track what's been done
    updated_entities = state.get("updated_entities", {})
    rule_retrieved_done = len(updated_entities.get("retrieved_rules", [])) > 0
    if rule_retrieved_done:
        has_rule_id = "target_rule_id" in updated_entities
    else:
        has_rule_id = False

    activation_done = len(updated_entities.get("activations", [])) > 0
    deactivation_done = len(updated_entities.get("deactivations", [])) > 0
    condition_created = len(updated_entities.get("conditions", [])) > 0
    action_created = len(updated_entities.get("actions", [])) > 0
   
    #available_tools_filtered_ = AVAILABLE_UPDATE_TOOLS

    if rule_retrieved_done:
        if has_rule_id:
            available_tools_filtered = {
            k: v for k, v in AVAILABLE_UPDATE_TOOLS.items()
            if k != "list_automation_rules"
            }
            tool_restriction_note = "\n IMPORTANT: A rule has been found in this workflow. You can ONLY select 'activate_automation_rule'  or 'deactivate_automation_rule' or 'update_condition' or 'update_action' now, or 'respond' if done."
            print("  Rule id found - restricting to update tools only")
        else:
            available_tools_filtered=""
            tool_restriction_note=" Unable to find the rule to update the information, select only 'respond'. "
            return {
            **state,
            "next_action": "respond",
            "has_completed_update": True,
            "reasoning": "Unable to find the rule to update the information.",
            "iteration_count": state["iteration_count"] + 1
            }
    else:
        available_tools_filtered = AVAILABLE_UPDATE_TOOLS
        tool_restriction_note = "If rule Id is not provided in the query call 'list_automation_rules' to extract rule Id."
    #We are going to filter one by one
    if condition_created or action_created or activation_done or deactivation_done:
        print(" Update has been done \n")
        #available_tools_filtered = {
        #    k: v for k, v in available_tools_filtered_.items()
        #    if k != "list_automation_rules"
        #}
        available_tools_filtered=""
        tool_restriction_note = "Updates are complete. ONLY select 'respond' as next_action"
        return {
            **state,
            "next_action": "respond",
            "has_completed_update": True,
            "reasoning": "Updates are complete",
            "iteration_count": state["iteration_count"] + 1
            }

    # Build tool descriptions
    #if has_rule_id:
    if available_tools_filtered!="":
        tool_descriptions = "\n".join([
                f"- {name}:\n  Description: {info['description']}\n  Parameters: {json.dumps(info['parameters'], indent=4)}\n  Example: {info['example']}"
                for name, info in available_tools_filtered.items()
        ])
    else:
        tool_descriptions = ""

    # Build context about what's been done
    tools_history = "\n".join([
         f"- {call['tool']}({json.dumps(call['parameters'])}): {call['result_summary']}"
         for call in state.get("tools_called", [])
    ])


    updated_entities_summary = json.dumps(updated_entities, indent=2)

    llm_update = ChatOllama(model="llama3.1:70b", temperature=0.1, base_url="http://localhost:11434")

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=f"""
You are an update planning agent for an RF spectrum automation system.
Your job is to:
1. Analyze what the user wants to update (activate rule, deactivate rule, add condition, add action)
2. Review what has already been done
3. Decide the NEXT tool to call OR if the update is complete
4. Extract parameters from the user query for the tool call

Available Tools (for current state)::
{tool_descriptions}
Follow
{tool_restriction_note}

Parameter Schemas for Conditions and Actions:
{UPDATE_SCHEMA_DETAILS}

CRITICAL RULES:
- If user references a rule by NAME (not UUID), FIRST call list_automation_rules to find the rule_id
- For activate/deactivate: Use activate_automation_rule or deactivate_automation_rule with the rule_id
- For updating conditions/actions: Use update_condition or update_action with the rule_id
- DO NOT call activate_automation_rule to create rules - it only enables existing rules
- DO NOT call deactivate_automation_rule to delete rules - it only disables existing rules
- Only call "respond" when updates are complete OR if you need more information

Tools Already Called:
{tools_history if tools_history else "None"}

Entities Updated So Far:
{updated_entities_summary if updated_entities_summary != '{{}}' else "None"}

DECISION LOGIC:
- If user references rule by NAME and no rules retrieved yet → call list_automation_rules
- If user wants to activate a rule and have rule_id → call activate_automation_rule
- If user wants to deactivate a rule and have rule_id → call deactivate_automation_rule
- If user wants to add/update condition and have rule_id → call update_condition
- If user wants to add/update action and have rule_id → call update_action
- If updates are done → call respond

Respond ONLY with valid JSON:
{{
    "next_action": "call_tool|respond",
    "reasoning": "Explain your decision and what you're doing",
    "has_completed_update": true/false,
    "selected_tool": "tool_name or null",
    "tool_parameters": {{"param": "value"}} or {{}}
}}
"""),
        HumanMessage(content=f"User Query: {state['user_query']}")
    ])

    response = llm_update.invoke(prompt.format_messages())

    # Parse response
    default_response = {
        "next_action": "respond",
        "reasoning": "Parse error - defaulting to respond",
        "has_completed_update": True,
        "selected_tool": None,
        "tool_parameters": {}
    }

    result, parse_success = safe_parse_json(response.content, default_response)
    if not parse_success:
        print(f"  ⚠️ Failed to parse decision, defaulting to respond")
        return {
            **state,
            "next_action": "respond",
            "has_completed_update": True,
            "reasoning": "Parse error - could not extract valid JSON from response",
            "iteration_count": state["iteration_count"] + 1
        }

    next_action = result.get("next_action", "respond")
    selected_tool = result.get("selected_tool", "") or ""

    print(f"  ✓ Decision: {next_action}")
    print(f"  ✓ Reasoning: {result.get('reasoning', 'N/A')}")

    if next_action == "call_tool":
        print(f"  ✓ Selected Tool: {selected_tool}")
        print(f"  ✓ Parameters: {json.dumps(result.get('tool_parameters', {}), indent=2)}")

    return {
        **state,
        "next_action": next_action,
        "reasoning": result.get("reasoning", ""),
        "has_completed_update": result.get("has_completed_update", False),
        "selected_tool": selected_tool,
        "tool_parameters": result.get("tool_parameters", {}),
        "iteration_count": state["iteration_count"] + 1
    }


def execute_update_tool_node(state: UpdateAgentState) -> UpdateAgentState:
    """
    Executes the selected update tool and tracks updated entities.
    This is the executor node that runs the tool.
    """
    print("\n🔧 Executing Update Tool...")

    tool_name = state.get("selected_tool", "")
    parameters = state.get("tool_parameters", {})

    if not tool_name:
        print("  ⚠️ No tool selected")
        return {
            **state,
            "tools_called": [{
                "tool": "none",
                "parameters": {},
                "result_summary": "No tool selected"
            }]
        }

    # Execute the tool
    result = execute_update_tool(tool_name, parameters)

    # Check for errors
    has_error = isinstance(result, dict) and "error" in result
    result_summary = result.get("error", "Error occurred") if has_error else "Successfully executed"

    if not has_error:
        if tool_name == "list_automation_rules":
            result_summary = f"Retrieved {len(result)} rules"
        elif tool_name == "activate_automation_rule":
            result_summary = f"Activated rule '{result.get('rule_name', 'unknown')}' (ID: {result.get('rule_id')})"
        elif tool_name == "deactivate_automation_rule":
            result_summary = f"Deactivated rule '{result.get('rule_name', 'unknown')}' (ID: {result.get('rule_id')})"
        elif tool_name == "update_condition":
            result_summary = f"Created {result.get('conditionType')} condition with ID {result.get('condition_id')}"
        elif tool_name == "update_action":
            result_summary = f"Created {result.get('actionType')} action with ID {result.get('action_id')}"

    print(f"  ✓ Result: {result_summary}")

    # Track updated entities
    updated_entities = state.get("updated_entities", {}).copy()

    if not has_error:
        if tool_name == "list_automation_rules":
            updated_entities["retrieved_rules"] = result
            # Try to find the target rule by name if we're looking for one
            user_query_lower = state.get("user_query", "").lower()
            for rule in result:
                if rule["name"].lower() in user_query_lower:
                    updated_entities["target_rule_id"] = rule["id"]
                    updated_entities["target_rule_name"] = rule["name"]
                    print(f"  ✓ Found target rule: {rule['name']} (ID: {rule['id']})")
                    break
        elif tool_name == "activate_automation_rule":
            if "activations" not in updated_entities:
                updated_entities["activations"] = []
            updated_entities["activations"].append(result)
        elif tool_name == "deactivate_automation_rule":
            if "deactivations" not in updated_entities:
                updated_entities["deactivations"] = []
            updated_entities["deactivations"].append(result)
        elif tool_name == "update_condition":
            if "conditions" not in updated_entities:
                updated_entities["conditions"] = []
            updated_entities["conditions"].append(result)
        elif tool_name == "update_action":
            if "actions" not in updated_entities:
                updated_entities["actions"] = []
            updated_entities["actions"].append(result)

    # Track validation errors
    validation_errors = state.get("validation_errors", []).copy()
    if has_error:
        validation_errors.append(result.get("error"))

    return {
        **state,
        "updated_entities": updated_entities,
        "validation_errors": validation_errors,
        "tools_called": [{
            "tool": tool_name,
            "parameters": parameters,
            "result": result,
            "result_summary": result_summary,
            "has_error": has_error
        }]
    }


def generate_update_response_node(state: UpdateAgentState) -> UpdateAgentState:
    """
    Generates final response based on updated entities.
    This is the response node that summarizes what was done.
    """
    print("\n✨ Generating Update Response...")

    updated_entities_str = json.dumps(state.get("updated_entities", {}), indent=2)
    tools_called_str = "\n".join([
        f"- {call['tool']}({json.dumps(call['parameters'])}): {call['result_summary']}"
        for call in state.get("tools_called", [])
    ])
    validation_errors_str = "\n".join(state.get("validation_errors", []))

    llm_update = ChatOllama(model="llama3.1:70b", temperature=0.2, base_url="http://localhost:11434")

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=f"""You are a response generator for an RF spectrum automation system.

The user requested update operations, and we've executed the following:
Generate a clear, comprehensive response that:
1. Confirms what was successfully updated (with rule names and IDs)
2. Lists any errors or validation issues encountered
3. Provides next steps if applicable
4. Presents information in a structured, easy-to-read format
5. Is conversational and user-friendly

Tools Called:
{tools_called_str}

Updated Entities:
{updated_entities_str}

Validation Errors (if any):
{validation_errors_str if validation_errors_str else "None"}

For activation/deactivation:
- Clearly state the rule name and whether it's now active or inactive
- Mention that the rule configuration is preserved (for deactivation)

For condition/action creation:
- Confirm the type of condition/action updated
- Include the relevant parameters

Do NOT mention technical implementation details or tool names.
Focus on what the user cares about: what was updated and what they should do next.

IMPORTANT: Respond with plain text, NOT JSON. This is the final user-facing message."""),
        HumanMessage(content=f"User Query: {state['user_query']}")
    ])

    response = llm_update.invoke(prompt.format_messages())
    final_response = response.content.strip()

    print(f"  ✓ Response generated ({len(final_response)} characters)")

    return {
        **state,
        "final_response": final_response,
        "messages": [AIMessage(content=final_response)]
    }
# ============================================================================
# CREATE AGENT NODES
# ============================================================================
def plan_creation_action_node(state: CreateAgentState) -> CreateAgentState:
    """
    Analyzes the user query and created entities to decide next action.
    
    KEY CHANGES:
    - Uses create_rule_condition when query has condition info (frequency, signal type, threshold)
    - Uses create_rule_action when query has action info (message, sensorIds, algorithm)
    - Uses create_automation_rule only when query lacks condition/action details
    - Removed create_condition and create_action as separate tools
    """
    print("\n🔧 Planning Creation Action...")

    # Check iteration limit
    if state["iteration_count"] >= state["max_iterations"]:
        print("  ⚠️ Max iterations reached, forcing response generation")
        return {
            **state,
            "next_action": "respond",
            "has_completed_creation": True,
            "reasoning": "Maximum iterations reached"
        }

    # Check what's been created
    created_entities = state.get("created_entities", {})
    rule_already_created = len(created_entities.get("rules", [])) > 0
    condition_created = len(created_entities.get("conditions", [])) > 0
    action_created = len(created_entities.get("actions", [])) > 0

    # If rule+condition or rule+action already created, we're done
    if rule_already_created and (condition_created or action_created):
        print("  ✓ Rule with condition/action already created - completing")
        return {
            **state,
            "next_action": "respond",
            "has_completed_creation": True,
            "reasoning": "Rule with condition or action has been created successfully"
        }

    # If only rule created (from create_automation_rule), we're also done
    # because the combined tools weren't applicable
    if rule_already_created:
        print("  ✓ Rule created - completing (no condition/action info available)")
        return {
            **state,
            "next_action": "respond",
            "has_completed_creation": True,
            "reasoning": "Rule created. No sufficient information for conditions or actions."
        }

    # Build tool descriptions
    tool_descriptions = "\n".join([
        f"- {name}:\n  Description: {info['description']}\n  Parameters: {json.dumps(info['parameters'], indent=4)}\n  Example: {info['example']}"
        for name, info in AVAILABLE_CREATE_TOOLS.items()
    ])

    # Build context about what's been created
    tools_history = "\n".join([
        f"- {call['tool']}({json.dumps(call['parameters'])}): {call['result_summary']}"
        for call in state.get("tools_called", [])
    ])

    created_entities_summary = json.dumps(created_entities, indent=2)

    llm_create = ChatOllama(model="llama3.1:70b", temperature=0.1, base_url="http://localhost:11434")

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=f"""
You are a creation planning agent for an RF spectrum automation system.

Your job is to:
1. Analyze the user query to determine what to create
2. Extract ALL relevant parameters from the query
3. Select the BEST tool based on available information

Available Tools:
{tool_descriptions}

Parameter Schemas:
{CREATE_SCHEMA_DETAILS}

TOOL SELECTION LOGIC (PRIORITY ORDER - SELECT THE MOST COMPLETE TOOL):

1. **create_rule_condition_action** (HIGHEST PRIORITY): Use when query has BOTH condition AND action info:
   - Has condition info: signal type (5G, LTE, etc.) OR threshold OR frequency range
   - AND has action info: notification message OR sensor IDs OR geolocation algorithm
   - Example: "Create a rule to detect 5G signals and send notification 'Signal found!'"
   - NOTE: Frequency range is OPTIONAL - defaults to 10-6000 MHz if not specified

2. **create_rule_condition**: Use when query has CONDITION info but NO action info:
   - Has signal type (5G, LTE, QPSK, etc.)
   - OR has energy threshold (threshold_dBm)
   - OR has frequency range
   - But NO notification message, sensor IDs, or algorithm
   - NOTE: Frequency range is OPTIONAL - defaults to 10-6000 MHz if not specified

3. **create_rule_action**: Use when query has ACTION info but NO condition info:
   - Has notification message
   - OR has sensor IDs for scanning
   - OR has geolocation algorithm (TDOA, PDOA)
   - But NO signal type, threshold, or frequency range

4. **create_automation_rule** (LOWEST PRIORITY): Use ONLY when query lacks BOTH condition AND action details
   - Just wants a basic rule created
   - No specific monitoring or action requirements

5. **list_automation_rules**: Use when adding to an EXISTING rule by name

CRITICAL RULES:
- ALWAYS create rules with is_enabled=False
- Frequency range (minFrequencyMHz, maxFrequencyMHz) is OPTIONAL - will default to 10-6000 if not provided
- Extract condition_type and condition_parameters from the query
- Extract action_type and action_parameters from the query
- ONE creation per prompt - select the most appropriate combined tool
- PREFER more complete tools (create_rule_condition_action > create_rule_condition/create_rule_action > create_automation_rule)

Tools Already Called:
{tools_history if tools_history else "None"}

Entities Created So Far:
{created_entities_summary if created_entities_summary != '{{}}' else "None"}

Respond ONLY with valid JSON:
{{
    "next_action": "call_tool|respond",
    "reasoning": "Explain your decision",
    "has_completed_creation": true/false,
    "selected_tool": "tool_name or null",
    "tool_parameters": {{
        "name": "rule name",
        "description": "rule description",
        "condition_type": "signalDetection or spectralEnergy (if applicable)",
        "condition_parameters": {{}},
        "action_type": "action type (if applicable)",
        "action_parameters": {{}}
    }}
}}
"""),
        HumanMessage(content=f"User Query: {state['user_query']}")
    ])

    response = llm_create.invoke(prompt.format_messages())

    # Parse response
    default_response = {
        "next_action": "respond",
        "reasoning": "Parse error - defaulting to respond",
        "has_completed_creation": True,
        "selected_tool": None,
        "tool_parameters": {}
    }

    result, parse_success = safe_parse_json(response.content, default_response)
    if not parse_success:
        print(f"  ⚠️ Failed to parse decision, defaulting to respond")
        return {
            **state,
            "next_action": "respond",
            "has_completed_creation": True,
            "reasoning": "Parse error - could not extract valid JSON from response",
            "iteration_count": state["iteration_count"] + 1
        }

    next_action = result.get("next_action", "respond")
    selected_tool = result.get("selected_tool", "") or ""

    print(f"  ✓ Decision: {next_action}")
    print(f"  ✓ Reasoning: {result.get('reasoning', 'N/A')}")

    if next_action == "call_tool":
        print(f"  ✓ Selected Tool: {selected_tool}")
        print(f"  ✓ Parameters: {json.dumps(result.get('tool_parameters', {}), indent=2)}")

    return {
        **state,
        "next_action": next_action,
        "reasoning": result.get("reasoning", ""),
        "has_completed_creation": result.get("has_completed_creation", False),
        "selected_tool": selected_tool,
        "tool_parameters": result.get("tool_parameters", {}),
        "iteration_count": state["iteration_count"] + 1
    }

def execute_creation_tool_node(state: CreateAgentState) -> CreateAgentState:
    """
    Executes the selected creation tool and tracks created entities.
    
    Updated to handle:
    - create_rule_condition: Creates both rule and condition
    - create_rule_action: Creates both rule and action
    - create_rule_condition_action: Creates rule, condition, AND action
    """
    print("\n🔧 Executing Creation Tool...")

    tool_name = state.get("selected_tool", "")
    parameters = state.get("tool_parameters", {})

    if not tool_name:
        print("  ⚠️ No tool selected")
        return {
            **state,
            "tools_called": [{
                "tool": "none",
                "parameters": {},
                "result_summary": "No tool selected"
            }]
        }

    # Execute the tool
    result = execute_create_tool(tool_name, parameters)

    # Check for errors
    has_error = isinstance(result, dict) and "error" in result
    result_summary = result.get("error", "Error occurred") if has_error else "Successfully created"
    
    if not has_error:
        if tool_name == "list_automation_rules":
            result_summary = f"Retrieved {len(result)} rules"
        elif tool_name == "create_automation_rule":
            result_summary = f"Created rule '{result.get('name')}' with ID {result.get('id')}"
        elif tool_name == "create_rule_condition":
            result_summary = f"Created rule '{result.get('rule_name')}' (ID: {result.get('rule_id')}) with {result.get('condition_type')} condition (ID: {result.get('condition_id')})"
        elif tool_name == "create_rule_action":
            result_summary = f"Created rule '{result.get('rule_name')}' (ID: {result.get('rule_id')}) with {result.get('action_type')} action (ID: {result.get('action_id')})"
        elif tool_name == "create_rule_condition_action":
            result_summary = f"Created rule '{result.get('rule_name')}' (ID: {result.get('rule_id')}) with {result.get('condition_type')} condition (ID: {result.get('condition_id')}) and {result.get('action_type')} action (ID: {result.get('action_id')})"

    print(f"  ✓ Result: {result_summary}")

    # Track created entities
    created_entities = state.get("created_entities", {}).copy()

    if not has_error:
        if tool_name == "list_automation_rules":
            created_entities["retrieved_rules"] = result
            
        elif tool_name == "create_automation_rule":
            if "rules" not in created_entities:
                created_entities["rules"] = []
            created_entities["rules"].append(result)
            created_entities["last_rule_id"] = result.get("id")
            
        elif tool_name == "create_rule_condition":
            # Track both rule and condition
            if "rules" not in created_entities:
                created_entities["rules"] = []
            created_entities["rules"].append(result.get("rule"))
            created_entities["last_rule_id"] = result.get("rule_id")
            
            if "conditions" not in created_entities:
                created_entities["conditions"] = []
            created_entities["conditions"].append(result.get("condition"))
            created_entities["last_condition_id"] = result.get("condition_id")
            
        elif tool_name == "create_rule_action":
            # Track both rule and action
            if "rules" not in created_entities:
                created_entities["rules"] = []
            created_entities["rules"].append(result.get("rule"))
            created_entities["last_rule_id"] = result.get("rule_id")
            
            if "actions" not in created_entities:
                created_entities["actions"] = []
            created_entities["actions"].append(result.get("action"))
            created_entities["last_action_id"] = result.get("action_id")
            
        elif tool_name == "create_rule_condition_action":
            # Track rule, condition, AND action
            if "rules" not in created_entities:
                created_entities["rules"] = []
            created_entities["rules"].append(result.get("rule"))
            created_entities["last_rule_id"] = result.get("rule_id")
            
            if "conditions" not in created_entities:
                created_entities["conditions"] = []
            created_entities["conditions"].append(result.get("condition"))
            created_entities["last_condition_id"] = result.get("condition_id")
            
            if "actions" not in created_entities:
                created_entities["actions"] = []
            created_entities["actions"].append(result.get("action"))
            created_entities["last_action_id"] = result.get("action_id")

    # Track validation errors
    validation_errors = state.get("validation_errors", []).copy()
    if has_error:
        validation_errors.append(result.get("error"))

    return {
        **state,
        "created_entities": created_entities,
        "validation_errors": validation_errors,
        "tools_called": [{
            "tool": tool_name,
            "parameters": parameters,
            "result": result,
            "result_summary": result_summary,
            "has_error": has_error
        }]
    }
def generate_creation_response_node(state: CreateAgentState) -> CreateAgentState:
    """
    Generates final response based on created entities
    """
    print("\n Generating Creation Response...")

    created_entities_str = json.dumps(state.get("created_entities", {}), indent=2)
    tools_called_str = "\n".join([
        f"- {call['tool']}({json.dumps(call['parameters'])}): {call['result_summary']}"
        for call in state.get("tools_called", [])
    ])
    validation_errors_str = "\n".join(state.get("validation_errors", []))

    llm_create = ChatOllama(model="llama3.1:70b", temperature=0.2, base_url="http://localhost:11434")

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=f"""You are a response generator for an RF spectrum automation system.

The user requested creation operations, and we've executed the following:

Tools Called:
{tools_called_str}

Created Entities:
{created_entities_str}

Validation Errors (if any):
{validation_errors_str if validation_errors_str else "None"}
Generate a clear, comprehensive response that:
1. Confirms what was successfully created (with IDs)
2. Lists any errors or validation issues encountered
3. Provides next steps if applicable (e.g., "Rule created but disabled - enable it when ready")
4. Presents information in a structured, easy-to-read format
5. Is conversational and user-friendly

Do NOT mention technical implementation details or tool names.
Focus on what the user cares about: what was created and what they should do next.

IMPORTANT: Respond with plain text, NOT JSON. This is the final user-facing message."""),
        HumanMessage(content=f"User Query: {state['user_query']}")
    ])

    response = llm_create.invoke(prompt.format_messages())
    final_response = response.content.strip()

    print(f"Response generated ({len(final_response)} characters)")

    return {
        **state,
        "final_response": final_response,
        "messages": [AIMessage(content=final_response)]
    }

# ============================================================================
# UPDATE ROUTING LOGIC
# ============================================================================

def should_call_update_tool_or_respond(state: UpdateAgentState) -> Literal["execute_tool", "generate_response"]:
    """
    Routes based on next_action from the planner.
    """
    next_action = state.get("next_action", "respond")
    
    if next_action == "call_tool":
        return "execute_tool"
    else:
        return "generate_response"
# ============================================================================
# CREATE ROUTING LOGIC
# ============================================================================
def should_call_tool_or_respond(state: CreateAgentState) -> Literal["execute_tool", "generate_response"]:
    """
    �~P UPDATED: Routes based on next_action including confirmation
    """
    next_action = state.get("next_action", "respond")

    if next_action == "call_tool":
        return "execute_tool"
    else:
        return "generate_response"


# ============================================================================
# BUILD UPDATE AGENT WORKFLOW
# ============================================================================

def create_update_agent_workflow():
    """
    Creates the update agent workflow with planner -> executor -> response pattern.
    
    Workflow:
    1. plan_action: Decides which tool to call next
    2. execute_tool: Executes the selected tool
    3. Loop back to plan_action for next decision
    4. generate_response: When done, summarize results for user
    """
    workflow = StateGraph(UpdateAgentState)
    
    # Add nodes
    workflow.add_node("plan_action", plan_update_action_node)
    workflow.add_node("execute_tool", execute_update_tool_node)
    workflow.add_node("generate_response", generate_update_response_node)
    
    # Set entry point
    workflow.set_entry_point("plan_action")
    
    # Conditional routing from planner
    workflow.add_conditional_edges(
        "plan_action",
        should_call_update_tool_or_respond,
        {
            "execute_tool": "execute_tool",
            "generate_response": "generate_response",
        }
    )
    
    # After executing tool, go back to planner (creates a loop)
    workflow.add_edge("execute_tool", "plan_action")
    
    # Response generation ends the workflow
    workflow.add_edge("generate_response", END)
    
    return workflow.compile()

# ============================================================================
# BUILD CREATE AGENT WORKFLOW
# ============================================================================


def create_creation_agent_workflow():
    """
    �~P UPDATED: Creates the create agent workflow with confirmation support
    """
    workflow = StateGraph(CreateAgentState)

    # Add nodes
    workflow.add_node("plan_action", plan_creation_action_node)
    workflow.add_node("execute_tool", execute_creation_tool_node)
    workflow.add_node("generate_response", generate_creation_response_node)

    # Set entry point
    workflow.set_entry_point("plan_action")

    # �~P UPDATED: Conditional routing from planner (now includes confirmation)
    workflow.add_conditional_edges(
        "plan_action",
        should_call_tool_or_respond,
        {
            "execute_tool": "execute_tool",
            "generate_response": "generate_response",
        }
    )

    # After executing tool, go back to planner (creates a loop)
    workflow.add_edge("execute_tool", "plan_action")

    # Response generation ends the workflow
    workflow.add_edge("generate_response", END)

    return workflow.compile()

# ============================================================================
# DATABASE SCHEMA KNOWLEDGE BASE
# ============================================================================
class InfoAgentState(TypedDict):
    """State for the Info Intent Handler agent workflow"""
    user_query: str
    original_intent_state: dict  # Original state from main workflow
    messages: Annotated[list, operator.add]
    iteration_count: int
    max_iterations: int
    
    # Tool execution tracking
    tools_called: Annotated[list, operator.add]  # History of tool calls
    gathered_data: dict  # Accumulated data from tool calls
    
    # Decision making
    next_action: str  # "call_tool" or "respond"
    selected_tool: str  # Tool to call next
    tool_parameters: dict  # Parameters for the tool
    
    # Response generation
    has_sufficient_data: bool
    final_response: str
    reasoning: str

# ============================================================================
# TOOL REGISTRY
# ============================================================================

AVAILABLE_INFO_TOOLS = {
    "list_automation_rules": {
        "function": list_automation_rules,
        "description": "Lists all automation rules in the system",
        "parameters": {}
    },
    "get_automation_rule": {
        "function": get_automation_rule,
        "description": "Gets details of a specific automation rule by ID",
        "parameters": {
            "rule_id": "string - The ID of the rule to retrieve"
        }
    },
    "list_conditions_for_rule": {
        "function": list_conditions_for_rule,
        "description": "Lists all conditions for a specific rule by rule ID",
        "parameters": {
            "rule_id": "string - The ID of the rule"
        }
    },
    "list_actions_for_rule": {
        "function": list_actions_for_rule,
        "description": "Lists all actions for a specific rule by rule ID",
        "parameters": {
            "rule_id": "string - The ID of the rule"
        }
    }
}

def execute_info_tool(tool_name: str, parameters: dict) -> Any:
    """Execute a tool with given parameters"""
    if tool_name not in AVAILABLE_INFO_TOOLS:
        return {"error": f"Tool '{tool_name}' not found"}
    
    tool_info = AVAILABLE_INFO_TOOLS[tool_name]
    try:
        return tool_info["function"](**parameters)
    except Exception as e:
        return {"error": str(e)}

# ============================================================================
# INFO AGENT NODES
# ============================================================================

def plan_next_action_node(state: InfoAgentState) -> InfoAgentState:
    """
    Analyzes the user query and gathered data to decide next action
    """
    print("\n🤔 Planning Next Action...")
    
    # Check iteration limit
    if state["iteration_count"] >= state["max_iterations"]:
        print("  ⚠️ Max iterations reached, forcing response generation")
        return {
            **state,
            "next_action": "respond",
            "has_sufficient_data": True,
            "reasoning": "Maximum iterations reached"
        }
    
    # Build tool descriptions
    tool_descriptions = "\n".join([
        f"- {name}: {info['description']}\n  Parameters: {info['parameters']}"
        for name, info in AVAILABLE_INFO_TOOLS.items()
    ])
    
    # Build context about what's been done
    tools_history = "\n".join([
        f"- {call['tool']}: {call['result_summary']}"
        for call in state.get("tools_called", [])
    ])
    
    gathered_data_summary = json.dumps(state.get("gathered_data", {}), indent=2)

    # Extract rule IDs from gathered data for reference
    gathered_data = state.get("gathered_data", {})
    all_rule_ids = []
    if "all_rules" in gathered_data:
        all_rule_ids = [rule.get("id") for rule in gathered_data.get("all_rules", [])]
    
    # Check which rule IDs have been processed for conditions/actions
    processed_condition_rule_ids = list(gathered_data.get("conditions", {}).keys())
    processed_action_rule_ids = list(gathered_data.get("actions", {}).keys())
    
    remaining_for_conditions = [rid for rid in all_rule_ids if rid not in processed_condition_rule_ids]
    remaining_for_actions = [rid for rid in all_rule_ids if rid not in processed_action_rule_ids]


    llm_info = ChatOllama(model="llama3.1:70b", temperature=0.1, base_url="http://localhost:11434")
    
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=f"""
        You are a planning agent for information retrieval in an RF spectrum automation system
Your job is to:
1. Analyze what the user is asking for
2. Review what data has already been gathered
3. Decide if you need to call more tools OR if you have enough data to answer
4. If calling a tool, identify which tool and what parameters

Available Tools:
{tool_descriptions}

=============================================================================
TOOL USAGE PATTERNS - FOLLOW THESE SEQUENCES CAREFULLY:
=============================================================================

PATTERN 1: Get specific rule by ID
ser asks: "Show me rule XYZ" or "Get details of rule-001"
Sequence:
  1. Call get_automation_rule(rule_id="rule-001")
  2. Optionally call list_conditions_for_rule(rule_id="rule-001") 
  3. Optionally call list_actions_for_rule(rule_id="rule-001")
  4. Respond with gathered data

PATTERN 2: Get specific rule by NAME
ser asks: "Show me the 5G Monitor rule" or "Get LTE Detector details"
Sequence:
  1. Call list_automation_rules() to find the rule ID by name
  2. Call get_automation_rule(rule_id=<found_id>)
  3. Respond with gathered data

PATTERN 3: List all rules
ser asks: "Show all rules" or "List automation rules"
Sequence:
  1. Call list_automation_rules()
  2. Respond with the list

PATTERN 4: Find rules with specific CONDITION TYPE (signalDetection or spectralEnergy)
ser asks: "Which rules have signalDetection conditions?" or "Find rules with spectralEnergy"
Sequence:
  1. FIRST: Call list_automation_rules() to get ALL rule IDs
  2. THEN: Call list_conditions_for_rule(rule_id=X) for EACH rule ID iteratively
  3. After gathering all conditions, analyze which rules have the requested condition type
  4. Respond with the filtered list

Example iteration for 3 rules (rule-001, rule-002, rule-003):
  - Call list_conditions_for_rule(rule_id="rule-001")
  - Call list_conditions_for_rule(rule_id="rule-002") 
  - Call list_conditions_for_rule(rule_id="rule-003")
  - Then respond

PATTERN 5: Find rules with specific ACTION TYPE (frequencyScanRequest, geolocationRequest, userNotification)
ser asks: "Which rules send notifications?" or "Find rules with geolocation actions"
Sequence:
  1. FIRST: Call list_automation_rules() to get ALL rule IDs
  2. THEN: Call list_actions_for_rule(rule_id=X) for EACH rule ID iteratively
  3. After gathering all actions, analyze which rules have the requested action type
  4. Respond with the filtered list

PATTERN 6: Find rules with specific SIGNAL TYPE (5G, LTE, QPSK, etc.)
ser asks: "Which rules monitor 5G signals?" or "Find LTE detection rules"
Sequence:
  1. FIRST: Call list_automation_rules() to get ALL rule IDs
  2. THEN: Call list_conditions_for_rule(rule_id=X) for EACH rule ID
  3. Check the signalType parameter in each condition
  4. Respond with rules that have the matching signal type

PATTERN 7: Find rules monitoring specific FREQUENCY RANGE
ser asks: "Which rules monitor frequencies above 3000 MHz?"
Sequence:
  1. FIRST: Call list_automation_rules() to get ALL rule IDs
  2. THEN: Call list_conditions_for_rule(rule_id=X) for EACH rule ID
  3. Check minFrequencyMHz/maxFrequencyMHz in each condition
  4. Respond with rules matching the frequency criteria

PATTERN 8: Get complete rule details with conditions AND actions
ser asks: "Show me everything about rule-001" or "Full details of 5G Monitor"
Sequence:
  1. Get rule ID (via list_automation_rules if needed)
  2. Call get_automation_rule(rule_id=X)
  3. Call list_conditions_for_rule(rule_id=X)
  4. Call list_actions_for_rule(rule_id=X)
  5. Respond with complete information

=============================================================================
CURRENT STATE:
=============================================================================

Tools Already Called:
{tools_history if tools_history else "None"}

Data Gathered So Far:
{gathered_data_summary if gathered_data_summary != '{{}}' else "None"}

Rule IDs Retrieved: {all_rule_ids if all_rule_ids else "None yet - need to call list_automation_rules first"}

Rule IDs already processed for CONDITIONS: {processed_condition_rule_ids if processed_condition_rule_ids else "None"}
Rule IDs still needing CONDITIONS: {remaining_for_conditions if remaining_for_conditions else "None or N/A"}

Rule IDs already processed for ACTIONS: {processed_action_rule_ids if processed_action_rule_ids else "None"}
Rule IDs still needing ACTIONS: {remaining_for_actions if remaining_for_actions else "None or N/A"}

=============================================================================
DECISION RULES:
=============================================================================

1. If user asks about condition types/signal types/frequencies AND all_rules NOT yet retrieved:
   Call list_automation_rules() FIRST

2. If user asks about condition types/signal types/frequencies AND all_rules retrieved BUT conditions not gathered for all rules:
   Call list_conditions_for_rule() for the NEXT unprocessed rule ID

3. If user asks about action types AND all_rules NOT yet retrieved:
   Call list_automation_rules() FIRST

4. If user asks about action types AND all_rules retrieved BUT actions not gathered for all rules:
   Call list_actions_for_rule() for the NEXT unprocessed rule ID

5. If all necessary data has been gathered:
   Set next_action to "respond"

6. NEVER call list_automation_rules more than once - it returns ALL rules

7. Process rule IDs ONE AT A TIME for conditions/actions queries

=============================================================================

Respond ONLY with valid JSON:
{{
    "next_action": "call_tool|respond",
    "reasoning": "Explain your decision based on the patterns above",
    "has_sufficient_data": true/false,
    "selected_tool": "tool_name or null",
    "tool_parameters": {{"param": "value"}} or {{}},
    "confidence": 0.0-1.0
}}

"""),
        HumanMessage(content=f"User Query: {state['user_query']}")
    ])
    
    response = llm_info.invoke(prompt.format_messages())
    
    try:
        result = json.loads(response.content.strip())
        next_action = result.get("next_action", "respond")
        
        print(f"  ✓ Decision: {next_action}")
        print(f"  ✓ Reasoning: {result.get('reasoning', 'N/A')}")
        
        if next_action == "call_tool":
            print(f"  ✓ Selected Tool: {result.get('selected_tool', 'None')}")
            print(f"  ✓ Parameters: {result.get('tool_parameters', {})}")
        
        return {
            **state,
            "next_action": next_action,
            "reasoning": result.get("reasoning", ""),
            "has_sufficient_data": result.get("has_sufficient_data", False),
            "selected_tool": result.get("selected_tool", ""),
            "tool_parameters": result.get("tool_parameters", {}),
            "iteration_count": state["iteration_count"] + 1
        }
    except json.JSONDecodeError:
        print("  ⚠️ Failed to parse decision, defaulting to respond")
        return {
            **state,
            "next_action": "respond",
            "has_sufficient_data": True,
            "reasoning": "Parse error",
            "iteration_count": state["iteration_count"] + 1
        }

def execute_info_tool_node(state: InfoAgentState) -> InfoAgentState:
    """
    Executes the selected tool and updates gathered data
    """
    print("\n🔧 Executing Tool...")
    
    tool_name = state.get("selected_tool", "")
    parameters = state.get("tool_parameters", {})
    
    if not tool_name:
        print("  ⚠️ No tool selected")
        return {
            **state,
            "tools_called": [{
                "tool": "none",
                "parameters": {},
                "result_summary": "No tool selected"
            }]
        }
    
    # Execute the tool
    result = execute_info_tool(tool_name, parameters)
    
    # Store the result
    result_summary = f"Retrieved {len(result) if isinstance(result, list) else 1} item(s)"
    if isinstance(result, dict) and "error" in result:
        result_summary = result["error"]
    
    print(f"  ✓ Result: {result_summary}")
    
    # Update gathered data
    updated_data = state.get("gathered_data", {}).copy()
    
    # Store results in a structured way
    if tool_name == "list_automation_rules":
        updated_data["all_rules"] = result
    elif tool_name == "get_automation_rule":
        if "rules" not in updated_data:
            updated_data["rules"] = {}
        rule_id = parameters.get("rule_id", "unknown")
        updated_data["rules"][rule_id] = result
    elif tool_name == "list_conditions_for_rule":
        if "conditions" not in updated_data:
            updated_data["conditions"] = {}
        rule_id = parameters.get("rule_id", "unknown")
        updated_data["conditions"][rule_id] = result
    elif tool_name == "list_actions_for_rule":
        if "actions" not in updated_data:
            updated_data["actions"] = {}
        rule_id = parameters.get("rule_id", "unknown")
        updated_data["actions"][rule_id] = result
    
    return {
        **state,
        "gathered_data": updated_data,
        "tools_called": [{
            "tool": tool_name,
            "parameters": parameters,
            "result": result,
            "result_summary": result_summary
        }]
    }

def generate_info_response_node(state: InfoAgentState) -> InfoAgentState:
    """
    Generates final response based on gathered data
    """
    print("\n✨ Generating Response...")
    
    gathered_data_str = json.dumps(state.get("gathered_data", {}), indent=2)
    tools_called_str = "\n".join([
        f"- {call['tool']}({call['parameters']}): {call['result_summary']}"
        for call in state.get("tools_called", [])
    ])
    
    llm_info = ChatOllama(model="llama3.1:70b", temperature=0.2, base_url="http://localhost:11434")
    
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=f"""You are a response generator for an RF spectrum automation system.

The user asked an information query, and we've gathered the following data:

Tools Called:
{tools_called_str}

Gathered Data:
{gathered_data_str}

Generate a clear, comprehensive response that:
1. Directly answers the user's question
2. Presents the data in an organized, readable format
3. Includes relevant details from the gathered data
4. Uses bullet points or structured formatting where appropriate
5. Is conversational and user-friendly

Do NOT mention tool names or technical implementation details.
Focus on delivering the information the user requested."""),
        HumanMessage(content=f"User Query: {state['user_query']}")
    ])
    
    response = llm_info.invoke(prompt.format_messages())
    final_response = response.content
    
    print(f"  ✓ Response generated ({len(final_response)} characters)")
    
    return {
        **state,
        "final_response": final_response,
        "messages": [AIMessage(content=final_response)]
    }

# ============================================================================
# ROUTING LOGIC
# ============================================================================

def should_call_info_tool_or_respond(state: InfoAgentState) -> Literal["execute_tool", "generate_response"]:
    """
    Routes based on whether we need to call more tools or generate response
    """
    next_action = state.get("next_action", "respond")
    
    if next_action == "call_tool":
        return "execute_tool"
    else:
        return "generate_response"

# ============================================================================
# BUILD INFO AGENT WORKFLOW
# ============================================================================

def create_info_agent_workflow():
    """
    Creates the info agent workflow with iterative tool calling
    """
    workflow = StateGraph(InfoAgentState)
    
    # Add nodes
    workflow.add_node("plan_action", plan_next_action_node)
    workflow.add_node("execute_tool", execute_info_tool_node)
    workflow.add_node("generate_response", generate_info_response_node)
    
    # Set entry point
    workflow.set_entry_point("plan_action")
    
    # Conditional routing from planner
    workflow.add_conditional_edges(
        "plan_action",
        should_call_info_tool_or_respond,
        {
            "execute_tool": "execute_tool",
            "generate_response": "generate_response"
        }
    )
    
    # After executing tool, go back to planner (creates a loop)
    workflow.add_edge("execute_tool", "plan_action")
    
    # Response generation ends the workflow
    workflow.add_edge("generate_response", END)
    
    return workflow.compile()


SCHEMA_KNOWLEDGE = """
DATABASE SCHEMA:

1. AutomationRule Table:
   - id (string, UUID): Auto-generated unique identifier
   - name (string): Rule name (not unique)
   - description (string, optional): Rule description
   - isEnabled (bool): Whether rule is active
   - createdAt (datetime, optional): Creation timestamp
   - updatedAt (datetime, optional): Last update timestamp
   - lastTriggeredAt (float, optional): Last trigger time
   - maxExecutions (int, optional): Maximum execution limit
   - executionsRemaining (int, optional): Remaining executions
   - startTime (datetime, optional): Rule start time
   - endTime (datetime, optional): Rule end time

2. AutomationConditionType Table:
   - id (string, UUID): Auto-generated identifier
   - rule_id (string): Foreign key to AutomationRule
   - conditionType (string): "signalDetection" or "spectralEnergy"
   - description (string, optional): Condition description
   - parameters (dict):
     * For "signalDetection":
       - minFrequencyMHz (10-6000): Minimum frequency
       - maxFrequencyMHz (10-6000): Maximum frequency
       - signalType: ["Energy", "5G", "LTE", "QPSK", "CW", "PCMPM", "CPM", "CPMFM", "BPSK", "SOQPSK"]
     * For "spectralEnergy":
       - minFrequencyMHz (10-6000): Minimum frequency
       - maxFrequencyMHz (10-6000): Maximum frequency
       - threshold_dBm (-150 to 150): Threshold in dBm
   - isSatisfied (bool): Condition satisfaction status
   - satisfiedAt (float): Satisfaction timestamp
   - createdAt (float, optional): Creation timestamp
   - updatedAt (float, optional): Update timestamp

3. AutomationActionType Table:
   - id (string, UUID): Auto-generated identifier
   - rule_id (string): Foreign key to AutomationRule
   - actionType (string): "frequencyScanRequest", "geolocationRequest", or "userNotification"
   - description (string, optional): Action description
   - parameters (dict): Action-specific parameters
     * frequencyScanRequest: Uses sensors to scan frequency ranges
     * geolocationRequest: Uses TDOA/PDOA algorithms with sensors for signal location
     * userNotification: Sends notifications with messages to users
   - createdAt (float, optional): Creation timestamp
   - updatedAt (float, optional): Update timestamp
"""

RF_SPECTRUM_KNOWLEDGE = """
RF SPECTRUM ANALYSIS DOMAIN KNOWLEDGE:

SIGNAL TYPES:
- Energy: General RF energy detection
- 5G: Fifth-generation cellular network signals
- LTE: Long-Term Evolution (4G) cellular signals
- QPSK: Quadrature Phase Shift Keying modulation
- CW: Continuous Wave signals
- PCMPM: Pulse Code Modulation - Phase Modulation
- CPM: Continuous Phase Modulation
- CPMFM: Continuous Phase Frequency Modulation
- BPSK: Binary Phase Shift Keying
- SOQPSK: Shaped Offset Quadrature Phase Shift Keying

FREQUENCY RANGES:
- Supported range: 10 MHz to 6000 MHz (6 GHz)
- Common bands: VHF (30-300 MHz), UHF (300-3000 MHz), SHF (3-30 GHz)

POWER MEASUREMENTS:
- dBm: Decibels relative to 1 milliwatt
- Range: -150 dBm (very weak) to +150 dBm (very strong)
- Typical ambient RF: -90 to -50 dBm

GEOLOCATION METHODS:
- TDOA (Time Difference of Arrival): Uses time differences between sensors
- PDOA (Phase Difference of Arrival): Uses phase differences for positioning

CONDITION TYPES:
- signalDetection: Monitors for specific signal types in frequency ranges
- spectralEnergy: Monitors energy levels in frequency bands

ACTION TYPES:
- frequencyScanRequest: Initiates frequency scanning with sensors
- geolocationRequest: Performs signal source location
- userNotification: Alerts users of detected conditions
"""

# ============================================================================
# STATE DEFINITION
# ============================================================================

class IntentState(TypedDict):
    """State for intent classification workflow"""
    user_query: str
    messages: Annotated[list, operator.add]
    intent: str  # CREATE, UPDATE, INFO, GENERIC
    intent_confidence: float
    intent_reasoning: str
    entity_extraction: dict  # Extracted entities from query
    requires_schema_knowledge: bool
    requires_rf_knowledge: bool
    database_queriers: bool
    final_response: str
    iteration_count: int

# ============================================================================
# AGENT NODES
# ============================================================================

def initial_analyzer_node(state: IntentState) -> IntentState:
    """
    Analyzes the query to determine if it asking about the database schema, generic understanding of RF spectrum management, or about
    operation queries (create, update, modify, delete, extract) to the database tables (AutomationRyle, AutomationConditionType, AutomationActionType).
    """
    print("\n🔍 Initial Query Analyzer...")
    llm = ChatOllama(
        model="llama3.1:70b",
        temperature=0.2,
        base_url="http://localhost:11434"
    )
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="""You are a query analyzer for an RF spectrum automation system.

Analyze if the query requires:
1. Schema knowledge: Query about RF spectrum management database structure that includes tables, fields and what can be stored
2. RF knowledge: Query about generic RF concepts, signal types, frequencies, spectrum analysis
3. Database operation: Query about database operation on the database tables (AutomationRyle, AutomationConditionType, AutomationActionType).
4. None of the above

Respond ONLY with valid JSON:
{
    "requires_schema_knowledge": true/false,
    "requires_rf_knowledge": true/false,
    "requires_database_queries": true/false,
    "detected_entities": {
        "frequency_ranges": [],
        "signal_types": [],
        "action_types": [],
        "condition_types": [],
        "table_references": []
    }
}"""),
        HumanMessage(content=f"Query: {state['user_query']}")
    ])
    
    response = llm.invoke(prompt.format_messages())
    
    try:
        result = json.loads(response.content)
        print(f"Schema knowledge needed: {result.get('requires_schema_knowledge', False)}")
        print(f"RF knowledge needed: {result.get('requires_rf_knowledge', False)}")
        print(f"Database queries needed: {result.get('requires_database_queries', False)}")
        
        return {
            **state,
            "requires_schema_knowledge": result.get("requires_schema_knowledge", False),
            "requires_rf_knowledge": result.get("requires_rf_knowledge", False),
            "database_queries": result.get('requires_database_queries', False),        
            "entity_extraction": result.get("detected_entities", {}),
            "messages": [AIMessage(content="Query analyzed")]
        }
    except json.JSONDecodeError:
        return {
            **state,
            "requires_schema_knowledge": False,
            "requires_rf_knowledge": False,
            "database_queries": False,
            "entity_extraction": {},
            "messages": [AIMessage(content="Analysis incomplete")]
        }


def intent_classifier_node(state: IntentState) -> IntentState:
    """
    Primary Intent Classifier: Classifies into CREATE, UPDATE, INFO, or GENERIC
    """
    print("\n🎯 Intent Classification Agent...")
    
    # Build context based on requirements
    context = ""
    if state.get("requires_schema_knowledge"):
        context += f"\n\nDATABASE SCHEMA:\n{SCHEMA_KNOWLEDGE}"
    if state.get("requires_rf_knowledge"):
        context += f"\n\nRF DOMAIN KNOWLEDGE:\n{RF_SPECTRUM_KNOWLEDGE}"
    if state.get("database_queries") and state.get("requires_schema_knowledge")==False:
        context += f"\n\nDATABASE SCHEMA:\n{SCHEMA_KNOWLEDGE}"

    llm = ChatOllama(
        model="llama3.1:70b",                                                                                                   temperature=0.2,
        base_url="http://localhost:11434"
    )
    
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=f"""You are an assistant that classifies user queries into intents.

{context}

Classify user queries into ONE of these intents:

1. CREATE: Creating new automation rules, conditions, or actions
   Examples: "create a rule", "add a condition", "set up monitoring", "add an action"

2. UPDATE: Modifying or deleting existing rules, conditions, actions, or any field updates
   Examples: "update rule", "change frequency", "disable or enable rule", "modify action type", "modify condition type" 

3. INFO: Retrieving information about existing rules, conditions, or actions
   Examples: "show me rules", "list conditions", "get rule details", "find rules with 5G"

4. GENERIC: General questions about RF spectrum, capabilities, database schema structure, or how the system works
   Examples: "what is TDOA?", "what signal types are supported?", "explain the database schema", "what can I do with this system?"
5. UNKNOWN: Question does not fall into any of the above category


Respond ONLY with valid JSON:
{{
    "intent": "CREATE|UPDATE|INFO|GENERIC|UNKNOWN",
    "confidence": 0.95,
    "reasoning": "Clear explanation of classification",
    "key_indicators": ["keyword1", "keyword2"],
    "extracted_info": {{
        "table_involved": "AutomationRule|AutomationConditionType|AutomationActionType|None",
        "operation": "specific operation if applicable"
    }}
}}"""),
        HumanMessage(content=f"User Query: {state['user_query']}")
    ])
    
    response = llm.invoke(prompt.format_messages())
    
    try:
        result = json.loads(response.content)
        intent = result.get("intent", "GENERIC")
        confidence = result.get("confidence", 0.0)
        reasoning = result.get("reasoning", "")
        
        print(f"✓ Intent: {intent}")
        print(f"✓ Confidence: {confidence:.2f}")
        print(f"✓ Reasoning: {reasoning}")
        
        return {
            **state,
            "intent": intent,
            "intent_confidence": confidence,
            "intent_reasoning": reasoning,
            "messages": [AIMessage(content=f"Intent: {intent}")]
        }
    except json.JSONDecodeError:
        print("⚠ Failed to parse, defaulting to GENERIC")
        return {
            **state,
            "intent": "GENERIC",
            "intent_confidence": 0.3,
            "intent_reasoning": "Parse error, defaulting to GENERIC",
            "messages": [AIMessage(content="Classification uncertain")]
        }

def create_intent_handler(state: dict, user_confirmation: str = None, previous_state: dict = None) -> dict:
    """
    �~P UPDATED: Enhanced CREATE Intent Handler with confirmation support

    This handler supports two modes:
    1. Initial request: Processes new creation requests
    2. Confirmation continuation: Continues after user confirms/denies

    Args:
        state: Current intent state from main workflow
        user_confirmation: User's response to confirmation (if continuing)
        previous_state: Previous create agent state (if continuing after confirmation)

    Returns:
        Updated state with final_response and messages
    """
    print("\n�~_~T� CREATE Intent Handler (Multi-Tool Agent Mode)...")


    # �~P Initial request processing
    create_workflow = create_creation_agent_workflow()
    # Initialize create agent state
    create_state = {
        "user_query": state.get("user_query", ""),
        "original_intent_state": state,
        "messages": [],
        "iteration_count": 0,
        "max_iterations": 8,
        "tools_called": [],
        "created_entities": {},
        "next_action": "call_tool",
        "selected_tool": "",
        "tool_parameters": {},
        "has_completed_creation": False,
        "final_response": "",
        "reasoning": "",
        "validation_errors": []
    }

    # Execute the create agent workflow
    result = create_workflow.invoke(create_state)

    # Extract the final response
    final_response = result.get("final_response", "Unable to complete creation")

    # �~P Check if workflow is waiting for confirmation
    if result.get("awaiting_user_response"):
        print(f"\n Workflow paused - waiting for user confirmation")
        print(f" Confirmation message sent to user")


        return {
            **state,
            "final_response": final_response,
            "messages": result.get("messages", [])
        }

    print(f"\n Create Agent completed after {result['iteration_count']} iterations")
    print(f"Tools called: {len(result['tools_called'])}")
    print(f"Entities created: {len(result.get('created_entities', {}).get('rules', []))} rules, "
          f"{len(result.get('created_entities', {}).get('conditions', []))} conditions, "
          f"{len(result.get('created_entities', {}).get('actions', []))} actions")

    return {
        **state,
        "final_response": final_response,
        "messages": [AIMessage(content=final_response)]
    }

def update_intent_handler(state: IntentState) -> IntentState:
    """
    Handles UPDATE intent queries
    """
    print("\n⚙️ UPDATE Intent Handler...")
    # Create the update agent workflow
    update_workflow = create_update_agent_workflow()
    
    # Initialize update agent state
    update_state = {
        "user_query": state.get("user_query", ""),
        "original_intent_state": state,
        "messages": [],
        "iteration_count": 0,
        "max_iterations": 8,
        "tools_called": [],
        "updated_entities": {},
        "next_action": "call_tool",
        "selected_tool": "",
        "tool_parameters": {},
        "has_completed_update": False,
        "final_response": "",
        "reasoning": "",
        "validation_errors": []
    }
    
    # Execute the update agent workflow
    result = update_workflow.invoke(update_state)
    
    # Extract the final response
    final_response = result.get("final_response", "Unable to complete update")
    
    print(f"\n✓ Update Agent completed after {result['iteration_count']} iterations")
    print(f"✓ Tools called: {len(result['tools_called'])}")
    
    # Summarize what was updated
    updated = result.get('updated_entities', {})
    print(f"✓ Entities updated: "
          f"{len(updated.get('activations', []))} activations, "
          f"{len(updated.get('deactivations', []))} deactivations, "
          f"{len(updated.get('conditions', []))} conditions, "
          f"{len(updated.get('actions', []))} actions")
    
    return {
        **state,
        "final_response": final_response,
        "messages": [AIMessage(content=final_response)]
    }
 

def info_intent_handler(state: dict) -> dict:
    """
    Enhanced INFO Intent Handler with multi-tool agent workflow
    This replaces the original info_intent_handler in the main script
    """
    print("\n📊 INFO Intent Handler (Multi-Tool Agent Mode)...")

    # Create the info agent workflow
    info_workflow = create_info_agent_workflow()

    # Initialize info agent state
    info_state = {
        "user_query": state.get("user_query", ""),
        "original_intent_state": state,
        "messages": [],
        "iteration_count": 0,
        "max_iterations": 5,  # Prevent infinite loops
        "tools_called": [],
        "gathered_data": {},
        "next_action": "call_tool",
        "selected_tool": "",
        "tool_parameters": {},
        "has_sufficient_data": False,
        "final_response": "",
        "reasoning": ""
    }

    # Execute the info agent workflow
    result = info_workflow.invoke(info_state)

    # Extract the final response
    final_response = result.get("final_response", "Unable to retrieve information")

    print(f"\n✓ Info Agent completed after {result['iteration_count']} iterations")
    print(f"✓ Tools called: {len(result['tools_called'])}")

    # Return in the format expected by main workflow
    return {
        **state,
        "final_response": final_response,
        "messages": [AIMessage(content=final_response)]
    }



def generic_intent_handler(state: IntentState) -> IntentState:
    """
    Handles GENERIC intent queries - RF knowledge and system capabilities
    """
    print("\n💡 GENERIC Intent Handler (RF Knowledge Assistant)...")
    
    context = f"{SCHEMA_KNOWLEDGE}\n\n{RF_SPECTRUM_KNOWLEDGE}"
   
    llm = ChatOllama(
        model="llama3.1:70b",
        temperature=0.2,
        base_url="http://localhost:11434"
    )
    
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=f"""You are an RF Spectrum Management expert assistant.

{context}

For GENERIC queries, provide:
1. Educational information about RF concepts
2. Explanations of system capabilities
3. Schema structure information
4. Examples of what users can do
5. Best practices for spectrum monitoring

Be conversational, educational, and helpful. Use analogies when appropriate."""),
        HumanMessage(content=f"User Query: {state['user_query']}")
    ])
    
    response = llm.invoke(prompt.format_messages())
    final_response = response.content
    
    print(f"✓ Generated educational response")
    
    return {
        **state,
        "final_response": final_response,
        "messages": [AIMessage(content=final_response)]
    }


# ============================================================================
# ROUTING LOGIC
# ============================================================================

def route_by_intent(state: IntentState) -> Literal["create_handler", "update_handler", "info_handler", "generic_handler"]:
    """
    Routes to appropriate handler based on classified intent
    """
    intent = state.get("intent", "GENERIC")
    
    routing_map = {
        "CREATE": "create_handler",
        "UPDATE": "update_handler",
        "INFO": "info_handler",
        "GENERIC": "generic_handler",
        "UNKNOWN": "unknown"
    }
    
    return routing_map.get(intent, "generic_handler")


# ============================================================================
# BUILD WORKFLOW GRAPH
# ============================================================================

def error_node(state: IntentState) -> dict:
    return { 
            **state,
            "final_response":"Sorry, I could not understand your request or may be your request not relevant"
    }

def create_intent_workflow():
    """
    Creates the LangGraph workflow for intent classification
    """
    workflow = StateGraph(IntentState)
    
    # Add nodes
    workflow.add_node("initial_analyzer", initial_analyzer_node)
    workflow.add_node("intent_classifier", intent_classifier_node)
    workflow.add_node("create_handler", create_intent_handler)
    workflow.add_node("update_handler", update_intent_handler)
    workflow.add_node("info_handler", info_intent_handler)
    workflow.add_node("generic_handler", generic_intent_handler)
    workflow.add_node("error",error_node)
    # Set entry point
    workflow.set_entry_point("initial_analyzer")
    
    # Linear flow: analyzer -> classifier
    workflow.add_edge("initial_analyzer", "intent_classifier")
    
    # Conditional routing from classifier to handlers
    workflow.add_conditional_edges(
        "intent_classifier",
        route_by_intent,
        {
            "create_handler": "create_handler",
            "update_handler": "update_handler",
            "info_handler": "info_handler",
            "generic_handler": "generic_handler",
            "unknown": "error"
        }
    )
    
    # All handlers end the workflow
    workflow.add_edge("create_handler", END)
    workflow.add_edge("update_handler", END)
    workflow.add_edge("info_handler", END)
    workflow.add_edge("generic_handler", END)
    workflow.add_edge("error",END)

    return workflow.compile()


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def classify_intent(user_query: str):
    """
    Main function to classify intent and generate response
    """
    print("\n" + "="*80)
    print("🤖 RF SPECTRUM AUTOMATION INTENT CLASSIFIER")
    print("="*80)
    print(f"\n📝 User Query: {user_query}\n")
    
    app = create_intent_workflow()
    
    initial_state = {
        "user_query": user_query,
        "messages": [],
        "intent": "",
        "intent_confidence": 0.0,
        "intent_reasoning": "",
        "entity_extraction": {},
        "requires_schema_knowledge": False,
        "requires_rf_knowledge": False,
        "final_response": "",
        "iteration_count": 0
    }
    
    result = app.invoke(initial_state)
    
    print("\n" + "="*80)
    print("📋 CLASSIFICATION RESULTS")
    print("="*80)
    print(f"\n🎯 Intent: {result['intent']}")
    print(f"📊 Confidence: {result['intent_confidence']:.2f}")
    print(f"💭 Reasoning: {result['intent_reasoning']}")
    print(f"\n🔍 Requires Schema Knowledge: {result['requires_schema_knowledge']}")
    print(f"📡 Requires RF Knowledge: {result['requires_rf_knowledge']}")
    
    if result['entity_extraction']:
        print(f"\n🏷️ Extracted Entities: {json.dumps(result['entity_extraction'], indent=2)}")
    
    print(f"\n💬 Final Response:\n{'-'*80}\n{result['final_response']}")
    print("\n" + "="*80 + "\n")
    
    return result


# ============================================================================
# EXAMPLE USAGE & TEST CASES
# ============================================================================

if __name__ == "__main__":
    
    test_queries = [
        # CREATE Intent
        "Create a new automation rule to detect 5G signals between 3400 and 3600 MHz",
        "I want to set up monitoring for LTE signals and send notifications when detected",
        
        # UPDATE Intent
        "Update the frequency range of rule 'LTE Detector' to 1800-2100 MHz",
        "Disable the rule 'Energy Threshold Alert'",
        #"Change the threshold to -80 dBm for the energy detection rule",
        
        # INFO Intent
        "Show me all automation rules that have spectralEnergy conditions",
        "List all active rules",
        #"What actions are configured for rule ID abc-123?",
        #"Find all rules monitoring frequencies above 5000 MHz",
        
        # GENERIC Intent
        "What is TDOA and how does it work for geolocation?",
        "Explain the difference between signalDetection and spectralEnergy conditions",
        #"What signal types can your system detect?",
        #"Tell me about the database schema",
        #"What's the difference between BPSK and QPSK?",
        #"How can I use this system for spectrum monitoring?"
    ]
    
    print("\n" + "="*80)
    print("🧪 RUNNING TEST CASES")
    print("="*80)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"Test Case {i}/{len(test_queries)}")
        classify_intent(query)
        
        if i < len(test_queries):
            input("\nPress Enter to continue to next test case...")
    
    # Interactive mode
    print("\n" + "="*80)
    print("🔹 INTERACTIVE MODE")
    print("="*80)
    print("Enter your queries about RF spectrum automation (type 'quit' to exit):")
    
    while True:
        user_input = input("\n👤 You: ").strip()
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
        if user_input:
            classify_intent(user_input)
