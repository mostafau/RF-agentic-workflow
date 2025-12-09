# EMS System - Complete Tools Reference

## Overview

The EMS (Electromagnetic Spectrum Management) system uses **4 workflows**, each with its own set of tools:

| Workflow | Purpose | Tool Registry |
|----------|---------|---------------|
| **CREATE** | Create new rules, conditions, actions | `AVAILABLE_CREATE_TOOLS` |
| **UPDATE** | Modify existing rules, conditions, actions | `AVAILABLE_UPDATE_TOOLS` |
| **INFO** | Query and retrieve information | `AVAILABLE_INFO_TOOLS` |
| **GENERIC** | Educational/conceptual questions | No tools (direct LLM response) |

---

## 1. INFO WORKFLOW TOOLS (`AVAILABLE_INFO_TOOLS`)

Tools for **reading/querying** data without modification.

### 1.1 `list_automation_rules`

| Property | Value |
|----------|-------|
| **Function** | `list_automation_rules()` |
| **Purpose** | Retrieve all automation rules in the system |
| **Parameters** | None |
| **Returns** | List of all rule objects |

**What it does:**
- Fetches ALL rules from the database
- Returns basic rule info: id, name, description, isEnabled, timestamps
- Does NOT include conditions or actions (need separate calls)

**Use when:**
- User asks "Show all rules" or "List my automation rules"
- Need to find a rule ID when user provides rule NAME
- Starting point for filtering rules by condition/action type

**Example Response:**
```json
[
  {"id": "rule-001", "name": "5G Monitor", "isEnabled": true, ...},
  {"id": "rule-002", "name": "LTE Detector", "isEnabled": false, ...}
]
```

---

### 1.2 `get_automation_rule`

| Property | Value |
|----------|-------|
| **Function** | `get_automation_rule(rule_id)` |
| **Purpose** | Get detailed information about a specific rule |
| **Parameters** | `rule_id: string` - UUID of the rule |
| **Returns** | Single rule object or error |

**What it does:**
- Fetches ONE specific rule by its ID
- Returns complete rule details
- Does NOT include conditions or actions

**Use when:**
- User asks about a specific rule by ID
- Need detailed info after finding ID via `list_automation_rules`

**Example Response:**
```json
{
  "id": "rule-001",
  "name": "5G Monitor",
  "description": "Monitors 5G signals in mid-band",
  "isEnabled": true,
  "createdAt": "2024-01-15T10:00:00Z",
  "updatedAt": "2024-01-15T10:00:00Z",
  "maxExecutions": 100,
  "executionsRemaining": 95
}
```

---

### 1.3 `list_conditions_for_rule`

| Property | Value |
|----------|-------|
| **Function** | `list_conditions_for_rule(rule_id)` |
| **Purpose** | Get all conditions attached to a specific rule |
| **Parameters** | `rule_id: string` - UUID of the rule |
| **Returns** | List of condition objects for that rule |

**What it does:**
- Fetches ALL conditions for a specific rule
- Each condition includes: conditionType, parameters, isSatisfied
- Condition types: `signalDetection`, `spectralEnergy`

**Use when:**
- User asks "What conditions does rule X have?"
- Need to find rules by condition type (call for each rule)
- Need to find rules monitoring specific signal types or frequencies

**Example Response:**
```json
[
  {
    "id": "cond-001",
    "rule_id": "rule-001",
    "conditionType": "signalDetection",
    "parameters": {
      "minFrequencyMHz": 3400,
      "maxFrequencyMHz": 3600,
      "signalType": "5G"
    },
    "isSatisfied": false
  }
]
```

---

### 1.4 `list_actions_for_rule`

| Property | Value |
|----------|-------|
| **Function** | `list_actions_for_rule(rule_id)` |
| **Purpose** | Get all actions attached to a specific rule |
| **Parameters** | `rule_id: string` - UUID of the rule |
| **Returns** | List of action objects for that rule |

**What it does:**
- Fetches ALL actions for a specific rule
- Each action includes: actionType, parameters
- Action types: `userNotification`, `frequencyScanRequest`, `geolocationRequest`

**Use when:**
- User asks "What actions does rule X trigger?"
- Need to find rules by action type (call for each rule)
- Need to find rules using specific sensors or algorithms

**Example Response:**
```json
[
  {
    "id": "act-001",
    "rule_id": "rule-001",
    "actionType": "userNotification",
    "parameters": {
      "message": "5G signal detected in mid-band"
    }
  }
]
```

---

## 2. CREATE WORKFLOW TOOLS (`AVAILABLE_CREATE_TOOLS`)

Tools for **creating new** rules, conditions, and actions.

### 2.1 `list_automation_rules`

*(Same as INFO workflow - used to find existing rules)*

---

### 2.2 `create_automation_rule`

| Property | Value |
|----------|-------|
| **Function** | `create_automation_rule(name, description, is_enabled, max_executions, start_time, end_time)` |
| **Purpose** | Create a basic rule WITHOUT conditions or actions |
| **Required** | `name: string` |
| **Optional** | `description`, `is_enabled` (default: False), `max_executions`, `start_time`, `end_time` |
| **Returns** | Created rule object with generated UUID |

**What it does:**
- Creates a new rule with basic info only
- Auto-generates UUID for the rule
- Sets `isEnabled=False` by default for safety
- Does NOT create conditions or actions

**Use when:**
- User wants to create a rule but doesn't provide condition/action details
- "Create a rule called Test Rule"
- Need to create rule first, then add conditions/actions separately

**Example:**
```python
create_automation_rule(
    name="5G Monitor",
    description="Monitors 5G signals",
    is_enabled=False
)
```

---

### 2.3 `create_rule_condition`

| Property | Value |
|----------|-------|
| **Function** | `create_rule_condition(name, description, is_enabled, max_executions, start_time, end_time, condition_type, condition_parameters, condition_description)` |
| **Purpose** | Create rule AND condition in ONE call |
| **Required** | `name`, `condition_type`, `condition_parameters` |
| **Returns** | Created rule AND condition with UUIDs |

**What it does:**
- Creates BOTH rule and condition atomically
- Validates condition parameters
- Applies default frequency range (10-6000 MHz) if not specified
- Returns both rule_id and condition_id

**Condition Types & Parameters:**

| Type | Required Parameters |
|------|---------------------|
| `signalDetection` | `signalType` (5G, LTE, QPSK, etc.) |
| `spectralEnergy` | `threshold_dBm` (-150 to 150) |

Both types accept optional: `minFrequencyMHz`, `maxFrequencyMHz`

**Use when:**
- User provides condition info but NO action info
- "Create a rule to detect 5G signals"
- "Monitor LTE between 1800-2100 MHz"

**Example:**
```python
create_rule_condition(
    name="5G Monitor",
    condition_type="signalDetection",
    condition_parameters={"signalType": "5G", "minFrequencyMHz": 3400, "maxFrequencyMHz": 3600}
)
```

---

### 2.4 `create_rule_action`

| Property | Value |
|----------|-------|
| **Function** | `create_rule_action(name, description, is_enabled, max_executions, start_time, end_time, action_type, action_parameters, action_description)` |
| **Purpose** | Create rule AND action in ONE call |
| **Required** | `name`, `action_type`, `action_parameters` |
| **Returns** | Created rule AND action with UUIDs |

**What it does:**
- Creates BOTH rule and action atomically
- Validates action parameters
- Returns both rule_id and action_id

**Action Types & Parameters:**

| Type | Required Parameters |
|------|---------------------|
| `userNotification` | `message: string` |
| `frequencyScanRequest` | `sensorIds: list` |
| `geolocationRequest` | `algorithm: "TDOA"/"PDOA"`, `sensorIds: list (min 2)` |

**Use when:**
- User provides action info but NO condition info
- "Create a rule that sends notification 'Alert!'"
- "Create a geolocation rule using TDOA"

**Example:**
```python
create_rule_action(
    name="Alert Rule",
    action_type="userNotification",
    action_parameters={"message": "Signal detected!"}
)
```

---

### 2.5 `create_rule_condition_action`

| Property | Value |
|----------|-------|
| **Function** | `create_rule_condition_action(name, description, is_enabled, max_executions, start_time, end_time, condition_type, condition_parameters, condition_description, action_type, action_parameters, action_description)` |
| **Purpose** | Create rule, condition, AND action in ONE call |
| **Required** | `name`, `condition_type`, `condition_parameters`, `action_type`, `action_parameters` |
| **Returns** | Created rule, condition, AND action with UUIDs |

**What it does:**
- Creates ALL THREE entities atomically (most complete tool)
- Validates both condition and action parameters
- Returns rule_id, condition_id, and action_id

**Use when:**
- User provides BOTH condition AND action info
- "Create a rule to detect 5G signals and send notification 'Signal found!'"
- "Monitor LTE and trigger geolocation using TDOA"

**Example:**
```python
create_rule_condition_action(
    name="5G Monitor with Alert",
    condition_type="signalDetection",
    condition_parameters={"signalType": "5G"},
    action_type="userNotification",
    action_parameters={"message": "5G signal detected!"}
)
```

---

## 3. UPDATE WORKFLOW TOOLS (`AVAILABLE_UPDATE_TOOLS`)

Tools for **modifying existing** rules, conditions, and actions.

### 3.1 `list_automation_rules`

*(Same as INFO workflow - used to find rule ID by name)*

---

### 3.2 `activate_automation_rule`

| Property | Value |
|----------|-------|
| **Function** | `activate_automation_rule(rule_id)` |
| **Purpose** | Enable a rule to start monitoring |
| **Parameters** | `rule_id: string` - UUID of the rule |
| **Returns** | Confirmation with rule details |

**What it does:**
- Sets `isEnabled=True` for the rule
- Resets condition satisfaction states
- Rule begins monitoring for conditions
- Will execute actions when conditions are met

**Use when:**
- User wants to enable/activate/turn on a rule
- "Enable the 5G Monitor rule"
- "Activate rule-001"
- "Turn on the LTE detector"

**Example:**
```python
activate_automation_rule(rule_id="rule-001")
```

---

### 3.3 `deactivate_automation_rule`

| Property | Value |
|----------|-------|
| **Function** | `deactivate_automation_rule(rule_id)` |
| **Purpose** | Disable a rule to stop monitoring |
| **Parameters** | `rule_id: string` - UUID of the rule |
| **Returns** | Confirmation with rule details |

**What it does:**
- Sets `isEnabled=False` for the rule
- Rule stops monitoring for conditions
- No actions will be triggered
- Does NOT delete the rule

**Use when:**
- User wants to disable/deactivate/turn off/pause a rule
- "Disable the 5G Monitor rule"
- "Turn off rule-001"
- "Pause the energy alert"

**Example:**
```python
deactivate_automation_rule(rule_id="rule-001")
```

---

### 3.4 `update_condition`

| Property | Value |
|----------|-------|
| **Function** | `update_condition(rule_id, condition_id, condition_type, parameters, description)` |
| **Purpose** | Modify an existing condition |
| **Required** | `rule_id: string` |
| **Optional** | `condition_id`, `condition_type`, `parameters`, `description` |
| **Returns** | Updated condition details |

**What it does:**
- Updates condition parameters (partial updates allowed)
- If `condition_id` not provided, updates FIRST condition of the rule
- Can change: frequency range, signal type, threshold, condition type
- Merges new parameters with existing ones

**Updatable Parameters:**

| Condition Type | Updatable Parameters |
|----------------|---------------------|
| `signalDetection` | `minFrequencyMHz`, `maxFrequencyMHz`, `signalType` |
| `spectralEnergy` | `minFrequencyMHz`, `maxFrequencyMHz`, `threshold_dBm` |

**Use when:**
- User wants to modify condition parameters
- "Change the frequency range of rule X to 3500-3700 MHz"
- "Update the threshold to -80 dBm"
- "Change signal type from 5G to LTE"

**Example:**
```python
update_condition(
    rule_id="rule-001",
    parameters={"minFrequencyMHz": 3500, "maxFrequencyMHz": 3700}
)
```

---

### 3.5 `update_action`

| Property | Value |
|----------|-------|
| **Function** | `update_action(rule_id, action_id, action_type, parameters, description)` |
| **Purpose** | Modify an existing action |
| **Required** | `rule_id: string` |
| **Optional** | `action_id`, `action_type`, `parameters`, `description` |
| **Returns** | Updated action details |

**What it does:**
- Updates action parameters (partial updates allowed)
- If `action_id` not provided, updates FIRST action of the rule
- Can change: message, sensor IDs, algorithm, action type
- Merges new parameters with existing ones

**Updatable Parameters:**

| Action Type | Updatable Parameters |
|-------------|---------------------|
| `userNotification` | `message` |
| `frequencyScanRequest` | `sensorIds` |
| `geolocationRequest` | `algorithm`, `sensorIds` |

**Use when:**
- User wants to modify action parameters
- "Change the notification message to 'New alert!'"
- "Update sensors to sensor-03 and sensor-04"
- "Switch algorithm from TDOA to PDOA"

**Example:**
```python
update_action(
    rule_id="rule-001",
    parameters={"message": "Updated alert message!"}
)
```

---

## 4. QUICK REFERENCE TABLES

### 4.1 Tools by Workflow

| Tool | INFO | CREATE | UPDATE |
|------|:----:|:------:|:------:|
| `list_automation_rules` | ✅ | ✅ | ✅ |
| `get_automation_rule` | ✅ | ❌ | ❌ |
| `list_conditions_for_rule` | ✅ | ❌ | ❌ |
| `list_actions_for_rule` | ✅ | ❌ | ❌ |
| `create_automation_rule` | ❌ | ✅ | ❌ |
| `create_rule_condition` | ❌ | ✅ | ❌ |
| `create_rule_action` | ❌ | ✅ | ❌ |
| `create_rule_condition_action` | ❌ | ✅ | ❌ |
| `activate_automation_rule` | ❌ | ❌ | ✅ |
| `deactivate_automation_rule` | ❌ | ❌ | ✅ |
| `update_condition` | ❌ | ❌ | ✅ |
| `update_action` | ❌ | ❌ | ✅ |

---

### 4.2 Tool Selection by User Intent

| User Wants To... | Workflow | Tool(s) |
|------------------|----------|---------|
| See all rules | INFO | `list_automation_rules` |
| See specific rule | INFO | `get_automation_rule` |
| See rule conditions | INFO | `list_conditions_for_rule` |
| See rule actions | INFO | `list_actions_for_rule` |
| Find rules by condition type | INFO | `list_automation_rules` → `list_conditions_for_rule` (iterate) |
| Find rules by action type | INFO | `list_automation_rules` → `list_actions_for_rule` (iterate) |
| Create basic rule | CREATE | `create_automation_rule` |
| Create rule with condition | CREATE | `create_rule_condition` |
| Create rule with action | CREATE | `create_rule_action` |
| Create complete rule | CREATE | `create_rule_condition_action` |
| Enable a rule | UPDATE | `activate_automation_rule` |
| Disable a rule | UPDATE | `deactivate_automation_rule` |
| Change frequency range | UPDATE | `update_condition` |
| Change threshold | UPDATE | `update_condition` |
| Change notification message | UPDATE | `update_action` |
| Change sensors | UPDATE | `update_action` |

---

### 4.3 Parameter Schemas

#### Condition Types

| Type | Required | Optional |
|------|----------|----------|
| `signalDetection` | `signalType` | `minFrequencyMHz`, `maxFrequencyMHz` |
| `spectralEnergy` | `threshold_dBm` | `minFrequencyMHz`, `maxFrequencyMHz` |

**Valid Signal Types:** `Energy`, `5G`, `LTE`, `QPSK`, `CW`, `PCMPM`, `CPM`, `CPMFM`, `BPSK`, `SOQPSK`

**Frequency Range:** 10 - 6000 MHz (defaults to full range if not specified)

**Threshold Range:** -150 to 150 dBm

#### Action Types

| Type | Required Parameters |
|------|---------------------|
| `userNotification` | `message: string` (non-empty) |
| `frequencyScanRequest` | `sensorIds: list` (non-empty) |
| `geolocationRequest` | `algorithm: "TDOA"/"PDOA"`, `sensorIds: list` (min 2) |

---

## 5. WORKFLOW PATTERNS

### 5.1 CREATE Workflow Tool Selection Priority

```
1. create_rule_condition_action  (if BOTH condition AND action info present)
   ↓ (no action info)
2. create_rule_condition         (if condition info present, no action)
   ↓ (no condition info)
3. create_rule_action            (if action info present, no condition)
   ↓ (neither present)
4. create_automation_rule        (basic rule only)
```

### 5.2 UPDATE Workflow Typical Sequence

```
1. list_automation_rules         (find rule ID by name)
   ↓
2. One of:
   ├── activate_automation_rule   (to enable)
   ├── deactivate_automation_rule (to disable)
   ├── update_condition           (to modify condition)
   └── update_action              (to modify action)
```

### 5.3 INFO Workflow for Filtered Queries

```
1. list_automation_rules         (get all rule IDs)
   ↓
2. For EACH rule_id:
   ├── list_conditions_for_rule  (if filtering by condition)
   └── list_actions_for_rule     (if filtering by action)
   ↓
3. Filter results and respond
```
