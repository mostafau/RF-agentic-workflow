# RF Spectrum Automation - Complete Agentic Workflow Diagram

## Overview

Your system uses a **hierarchical multi-agent architecture** with:
1. **Main Workflow** - Intent classification and routing
2. **4 Sub-Workflows** - Specialized handlers for each intent type

---

## 1. MAIN WORKFLOW (Intent Classification)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MAIN INTENT WORKFLOW                                 │
│                         State: IntentState                                   │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────┐
                              │  START  │
                              └────┬────┘
                                   │
                                   ▼
                        ┌──────────────────────┐
                        │  initial_analyzer    │
                        │  ─────────────────   │
                        │  Analyzes query      │
                        │  Extracts entities   │
                        │  Determines context  │
                        └──────────┬───────────┘
                                   │
                                   │ (direct edge)
                                   ▼
                        ┌──────────────────────┐
                        │  intent_classifier   │
                        │  ─────────────────   │
                        │  Classifies intent   │
                        │  Sets confidence     │
                        │  Provides reasoning  │
                        └──────────┬───────────┘
                                   │
                                   │ (conditional edge)
                                   │ route_by_intent()
                                   │
           ┌───────────┬───────────┼───────────┬───────────┐
           │           │           │           │           │
           ▼           ▼           ▼           ▼           ▼
    ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────┐
    │  CREATE    │ │  UPDATE    │ │   INFO     │ │  GENERIC   │ │ ERROR  │
    │  handler   │ │  handler   │ │  handler   │ │  handler   │ │  node  │
    │ ────────── │ │ ────────── │ │ ────────── │ │ ────────── │ │        │
    │ Invokes    │ │ Invokes    │ │ Invokes    │ │ Direct LLM │ │        │
    │ CREATE     │ │ UPDATE     │ │ INFO       │ │ response   │ │        │
    │ sub-flow   │ │ sub-flow   │ │ sub-flow   │ │            │ │        │
    └─────┬──────┘ └─────┬──────┘ └─────┬──────┘ └─────┬──────┘ └───┬────┘
          │              │              │              │            │
          └──────────────┴──────────────┴──────────────┴────────────┘
                                        │
                                        ▼
                                   ┌─────────┐
                                   │   END   │
                                   └─────────┘
```

### Routing Logic: `route_by_intent()`
```python
intent → handler mapping:
├── "CREATE"  → create_handler
├── "UPDATE"  → update_handler
├── "INFO"    → info_handler
├── "GENERIC" → generic_handler
└── "UNKNOWN" → error
```

---

## 2. CREATE SUB-WORKFLOW (Planner-Executor Pattern)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CREATE AGENT WORKFLOW                                │
│                         State: CreateAgentState                              │
│                         Entry: plan_action                                   │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────┐
                              │  START  │
                              └────┬────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │      plan_action             │◄──────────────┐
                    │      ────────────            │               │
                    │  plan_creation_action_node   │               │
                    │                              │               │
                    │  • Checks iteration limit    │               │
                    │  • Analyzes what to create   │               │
                    │  • Selects appropriate tool  │               │
                    │  • Extracts parameters       │               │
                    └──────────────┬───────────────┘               │
                                   │                               │
                                   │ (conditional edge)            │
                                   │ should_call_tool_or_respond() │
                                   │                               │
              ┌────────────────────┴────────────────────┐          │
              │                                         │          │
              ▼                                         ▼          │
   ┌─────────────────────┐               ┌─────────────────────┐   │
   │    execute_tool     │               │  generate_response  │   │
   │    ────────────     │               │  ────────────────   │   │
   │ execute_creation_   │               │ generate_creation_  │   │
   │ tool_node           │               │ response_node       │   │
   │                     │               │                     │   │
   │ Available Tools:    │               │ Summarizes results  │   │
   │ • list_automation_  │               │ for user            │   │
   │   rules             │               │                     │   │
   │ • create_automation_│               └──────────┬──────────┘   │
   │   rule              │                          │              │
   │ • create_rule_      │                          ▼              │
   │   condition         │                     ┌─────────┐         │
   │ • create_rule_      │                     │   END   │         │
   │   action            │                     └─────────┘         │
   │ • create_rule_      │                                         │
   │   condition_action  │                                         │
   └──────────┬──────────┘                                         │
              │                                                    │
              │ (direct edge - LOOP)                               │
              └────────────────────────────────────────────────────┘
```

### Routing Logic: `should_call_tool_or_respond()`
```python
next_action:
├── "call_tool" → execute_tool
└── "respond"   → generate_response
```

### Available CREATE Tools:
| Tool | Description |
|------|-------------|
| `list_automation_rules` | Find existing rules |
| `create_automation_rule` | Create rule only |
| `create_rule_condition` | Create rule + condition |
| `create_rule_action` | Create rule + action |
| `create_rule_condition_action` | Create rule + condition + action |

---

## 3. UPDATE SUB-WORKFLOW (Planner-Executor Pattern)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         UPDATE AGENT WORKFLOW                                │
│                         State: UpdateAgentState                              │
│                         Entry: plan_action                                   │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────┐
                              │  START  │
                              └────┬────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │      plan_action             │◄──────────────┐
                    │      ────────────            │               │
                    │  plan_update_action_node     │               │
                    │                              │               │
                    │  • Checks iteration limit    │               │
                    │  • Finds rule if by name     │               │
                    │  • Selects update operation  │               │
                    │  • Extracts parameters       │               │
                    └──────────────┬───────────────┘               │
                                   │                               │
                                   │ (conditional edge)            │
                                   │ should_call_update_tool_      │
                                   │ or_respond()                  │
                                   │                               │
              ┌────────────────────┴────────────────────┐          │
              │                                         │          │
              ▼                                         ▼          │
   ┌─────────────────────┐               ┌─────────────────────┐   │
   │    execute_tool     │               │  generate_response  │   │
   │    ────────────     │               │  ────────────────   │   │
   │ execute_update_     │               │ generate_update_    │   │
   │ tool_node           │               │ response_node       │   │
   │                     │               │                     │   │
   │ Available Tools:    │               │ Summarizes what     │   │
   │ • list_automation_  │               │ was updated         │   │
   │   rules             │               │                     │   │
   │ • activate_         │               └──────────┬──────────┘   │
   │   automation_rule   │                          │              │
   │ • deactivate_       │                          ▼              │
   │   automation_rule   │                     ┌─────────┐         │
   │ • update_condition  │                     │   END   │         │
   │ • update_action     │                     └─────────┘         │
   └──────────┬──────────┘                                         │
              │                                                    │
              │ (direct edge - LOOP)                               │
              └────────────────────────────────────────────────────┘
```

### Routing Logic: `should_call_update_tool_or_respond()`
```python
next_action:
├── "call_tool" → execute_tool
└── "respond"   → generate_response
```

### Available UPDATE Tools:
| Tool | Description |
|------|-------------|
| `list_automation_rules` | Find rule by name to get ID |
| `activate_automation_rule` | Enable a rule |
| `deactivate_automation_rule` | Disable a rule |
| `update_condition` | Modify condition parameters |
| `update_action` | Modify action parameters |

---

## 4. INFO SUB-WORKFLOW (Planner-Executor Pattern)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          INFO AGENT WORKFLOW                                 │
│                          State: InfoAgentState                               │
│                          Entry: plan_action                                  │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────┐
                              │  START  │
                              └────┬────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │      plan_action             │◄──────────────┐
                    │      ────────────            │               │
                    │  plan_next_action_node       │               │
                    │                              │               │
                    │  • Checks iteration limit    │               │
                    │  • Determines data needs     │               │
                    │  • Selects info tool         │               │
                    │  • Extracts parameters       │               │
                    └──────────────┬───────────────┘               │
                                   │                               │
                                   │ (conditional edge)            │
                                   │ should_call_info_tool_        │
                                   │ or_respond()                  │
                                   │                               │
              ┌────────────────────┴────────────────────┐          │
              │                                         │          │
              ▼                                         ▼          │
   ┌─────────────────────┐               ┌─────────────────────┐   │
   │    execute_tool     │               │  generate_response  │   │
   │    ────────────     │               │  ────────────────   │   │
   │ execute_info_       │               │ generate_info_      │   │
   │ tool_node           │               │ response_node       │   │
   │                     │               │                     │   │
   │ Available Tools:    │               │ Formats gathered    │   │
   │ • list_automation_  │               │ data for user       │   │
   │   rules             │               │                     │   │
   │ • get_automation_   │               └──────────┬──────────┘   │
   │   rule              │                          │              │
   │ • list_conditions_  │                          ▼              │
   │   for_rule          │                     ┌─────────┐         │
   │ • list_actions_     │                     │   END   │         │
   │   for_rule          │                     └─────────┘         │
   └──────────┬──────────┘                                         │
              │                                                    │
              │ (direct edge - LOOP)                               │
              └────────────────────────────────────────────────────┘
```

### Routing Logic: `should_call_info_tool_or_respond()`
```python
next_action:
├── "call_tool" → execute_tool
└── "respond"   → generate_response
```

### Available INFO Tools:
| Tool | Description |
|------|-------------|
| `list_automation_rules` | Get all rules |
| `get_automation_rule` | Get specific rule by ID |
| `list_conditions_for_rule` | Get conditions for a rule |
| `list_actions_for_rule` | Get actions for a rule |

---

## 5. GENERIC HANDLER (Direct Response - No Sub-Workflow)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GENERIC HANDLER                                      │
│                         (No separate workflow)                               │
└─────────────────────────────────────────────────────────────────────────────┘

                        ┌──────────────────────┐
                        │  generic_handler     │
                        │  ─────────────────   │
                        │  generic_intent_     │
                        │  handler()           │
                        │                      │
                        │  • Uses SCHEMA_      │
                        │    KNOWLEDGE         │
                        │  • Uses RF_SPECTRUM_ │
                        │    KNOWLEDGE         │
                        │  • Direct LLM call   │
                        │  • Educational       │
                        │    response          │
                        └──────────────────────┘
```

---

## 6. COMPLETE HIERARCHICAL VIEW

```
                                 USER QUERY
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MAIN WORKFLOW                                      │
│  ┌─────────────────┐    ┌───────────────────┐                               │
│  │initial_analyzer │───►│intent_classifier  │                               │
│  └─────────────────┘    └─────────┬─────────┘                               │
│                                   │                                          │
│         ┌─────────────────────────┼─────────────────────────┐               │
│         │           │             │             │           │               │
│         ▼           ▼             ▼             ▼           ▼               │
│    ┌─────────┐ ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐          │
│    │ CREATE  │ │ UPDATE  │  │  INFO   │  │ GENERIC │  │  ERROR  │          │
│    └────┬────┘ └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘          │
└─────────┼───────────┼────────────┼────────────┼────────────┼────────────────┘
          │           │            │            │            │
          ▼           ▼            ▼            │            │
    ┌───────────┐ ┌───────────┐ ┌───────────┐   │            │
    │  CREATE   │ │  UPDATE   │ │   INFO    │   │            │
    │  SUB-     │ │  SUB-     │ │  SUB-     │   │            │
    │  WORKFLOW │ │  WORKFLOW │ │  WORKFLOW │   │            │
    │           │ │           │ │           │   │            │
    │ ┌───────┐ │ │ ┌───────┐ │ │ ┌───────┐ │   │            │
    │ │ Plan  │◄┤ │ │ Plan  │◄┤ │ │ Plan  │◄┤   │            │
    │ └───┬───┘ │ │ └───┬───┘ │ │ └───┬───┘ │   │            │
    │     │     │ │     │     │ │     │     │   │            │
    │   ┌─┴─┐   │ │   ┌─┴─┐   │ │   ┌─┴─┐   │   │            │
    │   ▼   ▼   │ │   ▼   ▼   │ │   ▼   ▼   │   │            │
    │ Exec Resp │ │ Exec Resp │ │ Exec Resp │   │            │
    │  │    │   │ │  │    │   │ │  │    │   │   │            │
    │  └──►─┘   │ │  └──►─┘   │ │  └──►─┘   │   │            │
    └─────┬─────┘ └─────┬─────┘ └─────┬─────┘   │            │
          │             │             │         │            │
          └─────────────┴─────────────┴─────────┴────────────┘
                                      │
                                      ▼
                               FINAL RESPONSE
```

---

## 7. STATE DEFINITIONS

### IntentState (Main Workflow)
```python
class IntentState(TypedDict):
    user_query: str
    messages: Annotated[list, operator.add]
    intent: str  # CREATE, UPDATE, INFO, GENERIC, UNKNOWN
    intent_confidence: float
    intent_reasoning: str
    entity_extraction: dict
    requires_schema_knowledge: bool
    requires_rf_knowledge: bool
    database_queriers: bool
    final_response: str
    iteration_count: int
```

### CreateAgentState (Create Sub-Workflow)
```python
class CreateAgentState(TypedDict):
    user_query: str
    original_intent_state: dict
    messages: Annotated[list, operator.add]
    iteration_count: int
    max_iterations: int
    tools_called: Annotated[list, operator.add]
    created_entities: dict
    next_action: str  # "call_tool" or "respond"
    selected_tool: str
    tool_parameters: dict
    has_completed_creation: bool
    final_response: str
    reasoning: str
    validation_errors: list
```

### UpdateAgentState (Update Sub-Workflow)
```python
class UpdateAgentState(TypedDict):
    user_query: str
    original_intent_state: dict
    messages: Annotated[list, operator.add]
    iteration_count: int
    max_iterations: int
    tools_called: Annotated[list, operator.add]
    updated_entities: dict
    next_action: str  # "call_tool" or "respond"
    selected_tool: str
    tool_parameters: dict
    has_completed_update: bool
    final_response: str
    reasoning: str
    validation_errors: list
```

### InfoAgentState (Info Sub-Workflow)
```python
class InfoAgentState(TypedDict):
    user_query: str
    original_intent_state: dict
    messages: Annotated[list, operator.add]
    iteration_count: int
    max_iterations: int
    tools_called: Annotated[list, operator.add]
    gathered_data: dict
    next_action: str  # "call_tool" or "respond"
    selected_tool: str
    tool_parameters: dict
    has_sufficient_data: bool
    final_response: str
    reasoning: str
```

---

## 8. EDGE SUMMARY

### Main Workflow Edges
| From | To | Type | Condition |
|------|-----|------|-----------|
| START | initial_analyzer | Entry Point | - |
| initial_analyzer | intent_classifier | Direct | Always |
| intent_classifier | create_handler | Conditional | intent == "CREATE" |
| intent_classifier | update_handler | Conditional | intent == "UPDATE" |
| intent_classifier | info_handler | Conditional | intent == "INFO" |
| intent_classifier | generic_handler | Conditional | intent == "GENERIC" |
| intent_classifier | error | Conditional | intent == "UNKNOWN" |
| create_handler | END | Direct | Always |
| update_handler | END | Direct | Always |
| info_handler | END | Direct | Always |
| generic_handler | END | Direct | Always |
| error | END | Direct | Always |

### Create Sub-Workflow Edges
| From | To | Type | Condition |
|------|-----|------|-----------|
| START | plan_action | Entry Point | - |
| plan_action | execute_tool | Conditional | next_action == "call_tool" |
| plan_action | generate_response | Conditional | next_action == "respond" |
| execute_tool | plan_action | Direct | Always (LOOP) |
| generate_response | END | Direct | Always |

### Update Sub-Workflow Edges
| From | To | Type | Condition |
|------|-----|------|-----------|
| START | plan_action | Entry Point | - |
| plan_action | execute_tool | Conditional | next_action == "call_tool" |
| plan_action | generate_response | Conditional | next_action == "respond" |
| execute_tool | plan_action | Direct | Always (LOOP) |
| generate_response | END | Direct | Always |

### Info Sub-Workflow Edges
| From | To | Type | Condition |
|------|-----|------|-----------|
| START | plan_action | Entry Point | - |
| plan_action | execute_tool | Conditional | next_action == "call_tool" |
| plan_action | generate_response | Conditional | next_action == "respond" |
| execute_tool | plan_action | Direct | Always (LOOP) |
| generate_response | END | Direct | Always |

---

## 9. EXECUTION FLOW EXAMPLE

**Query**: "Create a rule to detect 5G signals and send notification 'Signal found!'"

```
1. MAIN WORKFLOW
   └── initial_analyzer: Extracts "5G", "notification", "Signal found!"
       └── intent_classifier: Intent = CREATE (confidence: 0.95)
           └── create_handler: Invokes CREATE sub-workflow

2. CREATE SUB-WORKFLOW
   └── plan_action (iter 1): 
       │   Decision: call_tool
       │   Tool: create_rule_condition_action
       │   Params: {name, condition_type, condition_parameters, action_type, action_parameters}
       │
       └── execute_tool: Creates rule + condition + action
           │   Returns: {rule_id, condition_id, action_id}
           │
           └── plan_action (iter 2):
               │   Decision: respond (creation complete)
               │
               └── generate_response: "Successfully created rule..."

3. BACK TO MAIN WORKFLOW
   └── create_handler returns final_response
       └── END
```
