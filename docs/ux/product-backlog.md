# Product backlog after the evidence-backed dashboard

The dashboard currently reports only facts already stored by PlantAgent: case questions, engineering work logs, `needs_human` items, revisions, decision packs, and approval records. It deliberately does not imitate a live operations or task-management product with invented data.

## Current scope

- The home engineering desk tracks the five featured demo cases.
- Decisions link to their plant workspace.
- Human decisions come from saved work-log `needs_human` entries.
- Approval items come from issued decision packs and sign-off records.
- The plant workspace shows the current draft or applied revision and lists its actual changes on the drawing.

## Not implemented

### Users, ownership, and permissions

- User accounts and organization membership
- Assigning a decision, check, or document to a named owner
- Role-based permissions for process, electrical, safety, operations, and management users
- Personal queues such as "assigned to me"

These require authenticated users, an organization model, and authorization checks on every write endpoint. Until those exist, the UI must not display invented owner names.

### Tasks and deadlines

- Creating, assigning, completing, or reopening tasks
- Due dates, priorities, and overdue states
- Claims such as "due today" or "updated 18 minutes ago"
- Shift handover and action-item tracking

These require a persistent task record with an audit trail, timestamps, ownership, and revision invalidation rules.

### Notifications and collaboration

- In-app notification centre
- Email, Slack, or Teams alerts
- Mentions and subscriptions
- Approval reminders and escalation rules

These should be added only after users, permissions, and task records exist. Delivery status and notification preferences must also be stored rather than inferred.

### Live operations status

- Plant online/offline or "operating normally" status
- Historian freshness such as "last data 12 minutes ago"
- Live alarms, active incidents, and shift status
- A plant-wide "N plants need attention" count

The current product has saved and synthetic historian evidence, not a live historian connection. These features require a real connector, timestamped ingestion health, tag-quality handling, and explicit stale-data rules.

### Portfolio and decision management

- A dashboard covering every case in the repository
- Cross-plant filtering, search, sorting, and saved views
- A full alternatives matrix across capital cost, operability, safety, schedule, and uncertainty
- Portfolio-level risk and approval reporting

The current home desk intentionally follows only the five featured, evidence-complete demo cases. Expanding it should use a case-level inclusion/status field instead of treating every benchmark fixture as an active plant.

### Additional product surfaces

- Mobile-specific workflows
- Offline review and synchronization
- Calendar and maintenance-system integration
- Procurement/vendor workflow beyond the current open vendor-confirmation checks

## Recommended order

1. Add authenticated users, organizations, and authorization.
2. Add audited task records linked to a case, proposal, gate, or document.
3. Add ownership, due dates, and personal queues from those records.
4. Add notifications and approval reminders.
5. Add a real historian connector and data-freshness model before showing live operating status.
6. Expand the engineering desk beyond featured cases and add portfolio filters.

## Product rule

Every dashboard statement must link to a stored engineering record, calculation, source document, or explicit human entry. If PlantAgent does not have the source data, the field stays absent or is shown as an open input; it is never filled with plausible-looking demo data.
