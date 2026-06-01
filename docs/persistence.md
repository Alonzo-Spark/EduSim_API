# EduSim Persistence Architecture

EduSim now uses PostgreSQL as the primary persistence target for authenticated user data, learning state, and interaction history.

## Core Identity Tables

- `users` stores the login identity and compatibility auth fields.
- `user_profiles` stores avatar, display name, bio, locale, and timezone.
- `roles` defines role names and metadata.
- `user_roles` assigns one or more roles to a user.
- `user_settings` stores user-level settings as structured JSON.
- `user_state` stores last page visited, temporary UI state, and restoration snapshots.

## Session and Authentication Tables

- `user_login_events` stores login attempts and metadata.
- `user_sessions` stores login/session history with device and user-agent metadata.
- `refresh_token_records` stores refresh-token metadata and revocation state.
- `app_session_state` stores generic short-lived app state keyed by namespace and state key.

## Tutor Persistence

- `tutor_conversations` stores conversation metadata.
- `tutor_messages` stores the ordered message history for each tutor session.

Relationship flow:
- one user -> many tutor conversations
- one tutor conversation -> many tutor messages

Soft delete is supported on the conversation row so a chat can be hidden without removing history.

## Curriculum Persistence

- `curriculum_progress` stores the current progress summary per user/topic scope.
- `curriculum_visits` stores history entries for page/topic visits and time spent.

This supports continue-learning and resume-from-last-topic flows.

## Formula Lab Persistence

- `formula_lab_sessions` stores the last opened formula, active tab, and UI state.
- `formula_lab_calculations` stores calculation runs and result payloads.
- `formula_lab_actions` stores visualization and interaction actions.
- `formula_lab_saved_calculations` stores saved calculation snapshots.
- `formula_lab_attempts` stores practice attempts and grading metadata.

## Sandbox and Simulation Persistence

- `sandbox_simulations_state` stores generated simulation state and serialized runtime payloads.
- `sandbox_events` stores user interactions and control updates.

This supports reopening a previous simulation and restoring its state.

## Dashboard and Search Persistence

- `dashboard_state` stores user dashboard widgets, layout, and preferences.
- `search_history` stores recent searches and search analytics.
- `search_selections` stores chosen results from a search session.
- `activity_logs` stores cross-app activity events for analytics and restoration.

## API Flow

Auth and state restore now follow this pattern:

1. The frontend logs in or refreshes the session.
2. The backend records the auth event and session metadata.
3. The frontend calls `GET /api/persistence/snapshot`.
4. The backend returns user-scoped tutor, curriculum, Formula Lab, sandbox, search, dashboard, and generic state.
5. The frontend hydrates the existing local caches used by Formula Lab and prompt history.

## Security Rules

- All persistence endpoints require a valid Bearer access token.
- Every read query is filtered by the authenticated user.
- The schema uses foreign keys and unique constraints to avoid duplication.
- Soft delete fields are used where historical visibility matters.
