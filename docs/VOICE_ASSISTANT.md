# Voice + side assistant

The Life OS dashboard contains a persistent right-side assistant.

## Proactive questions

`GET /api/assistant/status` computes a deterministic missing-information queue. Current prompts cover:
- no pending tasks;
- no fixed commitments in the next seven days;
- no energy/focus check-in in the last 12 hours;
- no sleep record ending in the last 36 hours;
- pending work without an active weekly plan.

The panel auto-opens at most once per local browser day when at least one prompt exists. Dismissing the panel does not create data or suppress the underlying prompt.

## Voice input

The browser client uses the Web Speech API when available and supports both `SpeechRecognition` and the vendor-prefixed `webkitSpeechRecognition`.

The client:
1. requests English (UK) recognition;
2. attempts on-device recognition when the browser exposes the required local-recognition capability;
3. otherwise warns that the browser may use an online speech service and asks for explicit consent before starting;
4. sends the resulting text to `POST /api/assistant/message`.

Raw assistant messages are not written to the Life OS database. Only structured records produced by an accepted command are persisted.

## Spoken replies

The optional “Speak replies” toggle uses browser speech synthesis. It is disabled by default and remembered in browser local storage.

## Deterministic command handling

The assistant currently handles a deliberately narrow set of structured commands:
- state input: energy/focus ratings;
- task creation with optional duration, priority and simple deadline;
- fixed event creation with explicit ISO date/start/end;
- overnight sleep interval;
- generate current weekly plan;
- return the current next action.

Ambiguous text returns `no_action` and does not mutate the database.

This command layer is intentionally independent from the optional `AIProvider`. A future LLM can expand natural-language understanding, but deterministic validation remains the mutation boundary.
