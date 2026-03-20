# Code Interpreter Checklists

## Pre-Interpretation Checklist

Before starting interpretation, verify:

- [ ] User request is captured completely
- [ ] No obvious typos or misunderstandings
- [ ] Context is sufficient (which DocTypes, which Frappe version)
- [ ] If unclear: clarifying questions prepared

---

## Step 1 Checklist: Extract Intent

### Action Identification
- [ ] Primary action verb identified
- [ ] Action mapped to category:
  - [ ] Computation/calculation
  - [ ] Validation/prevention
  - [ ] Notification/communication
  - [ ] Integration/sync
  - [ ] Filtering/permission
  - [ ] Workflow/approval
  - [ ] UI customization
  - [ ] Scheduling/automation
  - [ ] Reporting/analytics
  - [ ] Website/portal
  - [ ] File handling
  - [ ] Deployment/ops
  - [ ] Testing

### Subject Identification
- [ ] Primary DocType(s) identified
- [ ] Related DocType(s) identified (if any)
- [ ] Specific field(s) mentioned (if any)
- [ ] Data transformation described (if any)

### Condition Identification
- [ ] Trigger condition clear (when should this happen?)
- [ ] Filter conditions clear (for which records?)
- [ ] User/role conditions clear (for whom?)

---

## Step 2 Checklist: Identify Trigger

### Trigger Type Confirmed
- [ ] User action on form
  - [ ] Field change
  - [ ] Form load
  - [ ] Button click
  - [ ] Save
  - [ ] Submit
  - [ ] Cancel
- [ ] Time/schedule
  - [ ] Frequency identified
  - [ ] Cron pattern determined
- [ ] External event
  - [ ] Webhook
  - [ ] API call
  - [ ] Other app trigger
- [ ] Permission check
  - [ ] List filtering
  - [ ] Document access

### Timing Confirmed
- [ ] Before action (can block)
- [ ] After action (cannot block, only react)

---

## Step 3 Checklist: Determine Mechanism

### Server Script Eligibility
- [ ] No external library imports needed
- [ ] No complex transaction management needed
- [ ] No file system access needed
- [ ] No shell commands needed
- [ ] --> Server Script is eligible (all checked)
- [ ] --> Controller required (any unchecked)

### v16 Considerations
- [ ] Target version identified (v14, v15, v16, or multi)
- [ ] extend_doctype_class considered if v16-only
- [ ] Type annotations considered if v16
- [ ] Data masking considered for PII fields

### Mechanism Selection
- [ ] Primary mechanism selected:
  - [ ] Client Script
  - [ ] Server Script (Document Event)
  - [ ] Server Script (API)
  - [ ] Server Script (Scheduler)
  - [ ] Server Script (Permission Query)
  - [ ] Controller
  - [ ] hooks.py configuration
  - [ ] Built-in feature (Workflow, Notification, etc.)
  - [ ] Report (Script/Query)
  - [ ] Website template
  - [ ] Integration pattern
- [ ] Selection justified with reasoning
- [ ] Custom app requirement identified (yes/no)

---

## Step 4 Checklist: Generate Specification

### Specification Completeness
- [ ] Summary (1 sentence)
- [ ] Business requirement (clarified)
- [ ] Implementation table:
  - [ ] DocType(s) listed
  - [ ] Trigger specified
  - [ ] Mechanism named
  - [ ] Version compatibility noted
- [ ] Data flow documented (numbered steps)
- [ ] Error handling defined

### Data Flow Quality
- [ ] Input data sources identified
- [ ] Processing steps clear
- [ ] Output/side effects documented
- [ ] No missing steps in flow

### Error Handling Quality
- [ ] Possible errors identified
- [ ] Each error has handling strategy
- [ ] User feedback approach defined
- [ ] Logging requirements noted

---

## Step 5 Checklist: Map to Skills

### Primary Skills (syntax + implementation)
- [ ] Syntax skill for mechanism (`frappe-syntax-*`)
- [ ] Implementation skill for mechanism (`frappe-impl-*`)
- [ ] Error handling skill for mechanism (`frappe-errors-*`)

### Core Skills (if needed)
- [ ] Database operations (`frappe-core-database`)
- [ ] Permission handling (`frappe-core-permissions`)
- [ ] API patterns (`frappe-core-api`)
- [ ] Workflow engine (`frappe-core-workflow`)
- [ ] Notifications (`frappe-core-notifications`)
- [ ] File handling (`frappe-core-files`)
- [ ] Cache operations (`frappe-core-cache`)

### Ops Skills (if needed)
- [ ] Bench commands (`frappe-ops-bench`)
- [ ] Deployment (`frappe-ops-deployment`)
- [ ] Performance (`frappe-ops-performance`)
- [ ] Backup (`frappe-ops-backup`)
- [ ] Upgrades (`frappe-ops-upgrades`)

### Testing Skills (if needed)
- [ ] Unit tests (`frappe-testing-unit`)
- [ ] CI/CD (`frappe-testing-cicd`)

### Agent Skills (if needed)
- [ ] Code validation (`frappe-agent-validator`)
- [ ] Debugging (`frappe-agent-debugger`)
- [ ] Architecture (`frappe-agent-architect`)
- [ ] Migration (`frappe-agent-migrator`)

### Skill Dependencies
- [ ] Dependencies between skills noted
- [ ] Order of skill usage clear

---

## Output Quality Checklist

### Clarity
- [ ] Non-technical user can understand the summary
- [ ] Technical implementer can follow the specification
- [ ] No ambiguous terms or undefined acronyms

### Completeness
- [ ] All aspects of request addressed
- [ ] Edge cases considered
- [ ] Version compatibility explicit (v14/v15/v16)

### Actionability
- [ ] Clear next steps for implementation
- [ ] Required frappe-* skills listed from full catalog
- [ ] Validation criteria defined

---

## Quick Reference: Mechanism --> Skills

| If Mechanism Is... | Then Skills Are... |
|--------------------|-------------------|
| Client Script | `frappe-syntax-clientscripts`, `frappe-impl-clientscripts`, `frappe-errors-clientscripts` |
| Server Script (Doc Event) | `frappe-syntax-serverscripts`, `frappe-impl-serverscripts`, `frappe-errors-serverscripts` |
| Server Script (API) | `frappe-syntax-serverscripts`, `frappe-core-api`, `frappe-errors-api` |
| Server Script (Scheduler) | `frappe-syntax-serverscripts`, `frappe-syntax-scheduler`, `frappe-impl-scheduler` |
| Server Script (Permission) | `frappe-syntax-serverscripts`, `frappe-core-permissions`, `frappe-errors-permissions` |
| Controller | `frappe-syntax-controllers`, `frappe-impl-controllers`, `frappe-errors-controllers` |
| Hooks | `frappe-syntax-hooks`, `frappe-impl-hooks`, `frappe-errors-hooks` |
| Custom App | `frappe-syntax-customapp`, `frappe-impl-customapp`, `frappe-ops-bench` |
| Jinja Template | `frappe-syntax-jinja`, `frappe-impl-jinja` |
| Database heavy | + `frappe-core-database`, `frappe-errors-database` |
| Whitelisted API | + `frappe-syntax-whitelisted`, `frappe-impl-whitelisted` |
| Workflow | `frappe-core-workflow`, `frappe-impl-workflow` |
| Reports | `frappe-syntax-reports`, `frappe-impl-reports` |
| Website | `frappe-impl-website`, `frappe-syntax-jinja` |
| Integration | `frappe-impl-integrations`, `frappe-impl-customapp` |
| Notifications | `frappe-core-notifications` |
| File handling | `frappe-core-files` |
| Cache/performance | `frappe-core-cache`, `frappe-ops-performance` |
| Testing | `frappe-testing-unit`, `frappe-testing-cicd` |
| Deployment | `frappe-ops-deployment`, `frappe-ops-bench` |
